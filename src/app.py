import base64
import io
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from bson import ObjectId
from fastapi import Depends, FastAPI, File, HTTPException, Query, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError

from src.auth import create_access_token, get_current_user, hash_password, verify_password
from src.database import get_db, get_client
from src.explain import chat_about_disease, explain_disease
from src.models import ensure_indexes, utcnow
from src.predict import CLASS_NAMES, predict
from src.schemas import (
    ChatMessageOut,
    ChatRequest,
    ChatResponse,
    Explanation,
    PredictionOut,
    PredictionUpdate,
    PredictResponse,
    Prediction,
    SupportResponse,
    SupportStore,
    Token,
    UserCreate,
    UserOut,
)

logger = logging.getLogger("uvicorn.error")

CONFIDENCE_THRESHOLD = 0.70

# Load support info
with open(Path(__file__).parent / "support_info.json", encoding="utf-8") as _f:
    _SUPPORT_INFO = json.load(_f)

_DEFAULT_STORES = [SupportStore(**s) for s in _SUPPORT_INFO["_default_stores"]]
_DEFAULT_DISCLAIMER = _SUPPORT_INFO.get(
    "_disclaimer",
    "Chemical suggestions are general active ingredient groups from university advisories. "
    "Strictly no doses are given. Always consult a local agricultural officer.",
)

app = FastAPI(title="Plant Disease Advisor API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    """Create MongoDB indexes on first boot."""
    client = get_client()
    from src.database import DB_NAME
    db = client[DB_NAME]
    ensure_indexes(db)


# ---------- helpers ----------

def _oid(doc: dict) -> str:
    """Return the _id of a MongoDB document as a plain string."""
    return str(doc["_id"])


def _record_to_out(r: dict) -> PredictionOut:
    explanation = Explanation(**r["explanation"]) if r.get("explanation") else None
    return PredictionOut(
        id=_oid(r),
        disease=r["disease"],
        confidence=r["confidence"],
        status=r["status"],
        explanation=explanation,
        note=r.get("note"),
        image_b64=r.get("image_b64"),
        created_at=r["created_at"],
    )


def _get_owned_record(db, record_id: str, user: dict) -> dict:
    try:
        oid = ObjectId(record_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Prediction not found")

    record = db.predictions.find_one(
        {"_id": oid, "user_id": str(user["_id"])}
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return record


# ---------- system ----------

@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}


@app.get("/classes", tags=["system"])
def classes():
    return {"classes": CLASS_NAMES}


# ---------- auth ----------

@app.post("/auth/register", response_model=UserOut, status_code=201, tags=["auth"])
def register(payload: UserCreate, db=Depends(get_db)):
    username = payload.username.strip().lower()
    if db.users.find_one({"username": username}):
        raise HTTPException(status_code=409, detail="Username already taken")

    result = db.users.insert_one({
        "username": username,
        "password_hash": hash_password(payload.password),
        "created_at": utcnow(),
    })
    return UserOut(id=str(result.inserted_id), username=username)


@app.post("/auth/login", response_model=Token, tags=["auth"])
def login(form: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    user = db.users.find_one({"username": form.username.strip().lower()})
    if user is None or not verify_password(form.password, user["password_hash"]):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(str(user["_id"])))


@app.get("/auth/me", response_model=UserOut, tags=["auth"])
def me(current_user: dict = Depends(get_current_user)):
    return UserOut(id=str(current_user["_id"]), username=current_user["username"])


# ---------- prediction (Create) ----------

@app.post("/predict", response_model=PredictResponse, tags=["predictions"])
async def predict_disease(
    file: UploadFile = File(...),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if file.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(status_code=400, detail="Only JPEG or PNG images are supported")

    contents = await file.read()
    try:
        image = Image.open(io.BytesIO(contents))
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Could not read the image file")

    # Store image as Base64 so it survives Render restarts
    image_b64 = base64.b64encode(contents).decode("utf-8")

    disease, confidence = predict(image)
    request_id = str(uuid.uuid4())
    user_id = str(current_user["_id"])

    if confidence < CONFIDENCE_THRESHOLD:
        result = db.predictions.insert_one({
            "user_id": user_id,
            "disease": disease,
            "confidence": confidence,
            "status": "uncertain",
            "image_b64": image_b64,
            "created_at": utcnow(),
        })
        return PredictResponse(
            status="uncertain",
            prediction=Prediction(disease=disease, confidence=confidence),
            message="The model is not confident about this image. Please upload a clear, close-up photo of a single leaf.",
            request_id=request_id,
            record_id=str(result.inserted_id),
        )

    try:
        explanation = explain_disease(disease)
    except Exception:
        logger.exception("Explanation failed")
        raise HTTPException(status_code=502, detail="Explanation service error")

    result = db.predictions.insert_one({
        "user_id": user_id,
        "disease": disease,
        "confidence": confidence,
        "status": "ok",
        "explanation": explanation,
        "image_b64": image_b64,
        "created_at": utcnow(),
    })

    return PredictResponse(
        status="ok",
        prediction=Prediction(disease=disease, confidence=confidence),
        explanation=Explanation(**explanation),
        request_id=request_id,
        record_id=str(result.inserted_id),
    )


# ---------- predictions (Read, Update, Delete) ----------

@app.get("/predictions", response_model=List[PredictionOut], tags=["predictions"])
def list_predictions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    disease: Optional[str] = None,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query: dict = {"user_id": str(current_user["_id"])}
    if disease:
        query["disease"] = disease

    rows = (
        db.predictions.find(query)
        .sort("_id", -1)
        .skip(skip)
        .limit(limit)
    )
    return [_record_to_out(r) for r in rows]


@app.get("/predictions/{record_id}", response_model=PredictionOut, tags=["predictions"])
def get_prediction(
    record_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return _record_to_out(_get_owned_record(db, record_id, current_user))


@app.put("/predictions/{record_id}", response_model=PredictionOut, tags=["predictions"])
def update_prediction(
    record_id: str,
    payload: PredictionUpdate,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if payload.note is None and payload.disease is None:
        raise HTTPException(status_code=400, detail="Provide a note or a corrected disease")

    record = _get_owned_record(db, record_id, current_user)
    updates: dict = {}

    if payload.disease is not None:
        if payload.disease not in CLASS_NAMES:
            raise HTTPException(status_code=400, detail="Unknown disease class")
        updates["disease"] = payload.disease
        updates["explanation"] = None   # stale explanation cleared on label correction

    if payload.note is not None:
        updates["note"] = payload.note

    db.predictions.update_one({"_id": record["_id"]}, {"$set": updates})
    updated = db.predictions.find_one({"_id": record["_id"]})
    return _record_to_out(updated)


@app.delete("/predictions/{record_id}", status_code=204, tags=["predictions"])
def delete_prediction(
    record_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    record = _get_owned_record(db, record_id, current_user)
    # Cascade: delete chat messages first, then the prediction
    db.chat_messages.delete_many({"record_id": str(record["_id"])})
    db.predictions.delete_one({"_id": record["_id"]})
    return Response(status_code=204)


# ---------- chat ----------

@app.post("/predictions/{record_id}/chat", response_model=ChatResponse, tags=["chat"])
def send_chat_message(
    record_id: str,
    payload: ChatRequest,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    record = _get_owned_record(db, record_id, current_user)

    if record["status"] == "uncertain" or not record.get("explanation"):
        raise HTTPException(
            status_code=400,
            detail="Chat is only available for confident diagnoses with an explanation.",
        )

    explanation = record["explanation"]

    # Build history from existing messages
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in db.chat_messages.find({"record_id": record_id}).sort("_id", 1)
    ]

    reply = chat_about_disease(record["disease"], explanation, history, payload.message)

    db.chat_messages.insert_many([
        {"record_id": record_id, "role": "user",      "content": payload.message, "created_at": utcnow()},
        {"record_id": record_id, "role": "assistant",  "content": reply,          "created_at": utcnow()},
    ])

    return ChatResponse(reply=reply, record_id=record_id)


@app.get("/predictions/{record_id}/chat", response_model=List[ChatMessageOut], tags=["chat"])
def get_chat_history(
    record_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    _get_owned_record(db, record_id, current_user)   # ownership check
    messages = db.chat_messages.find({"record_id": record_id}).sort("_id", 1)
    return [
        ChatMessageOut(
            id=str(m["_id"]),
            role=m["role"],
            content=m["content"],
            created_at=m["created_at"],
        )
        for m in messages
    ]


# ---------- support / where to buy ----------

@app.get("/predictions/{record_id}/support", response_model=SupportResponse, tags=["support"])
def get_support(
    record_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    record = _get_owned_record(db, record_id, current_user)

    disease_info = _SUPPORT_INFO.get(record["disease"], {})
    recommended_products = disease_info.get("recommended_products", ["Consult a local agriculture officer"])
    readable = record["disease"].replace("___", " - ").replace("_", " ")

    return SupportResponse(
        disease=record["disease"],
        disease_readable=readable,
        recommended_products=recommended_products,
        where_to_buy=_DEFAULT_STORES,
        disclaimer=_DEFAULT_DISCLAIMER,
    )


# ---------- Serve frontend static files ----------
_CONSUMER_DIR = Path(__file__).resolve().parent.parent / "consumer"
if _CONSUMER_DIR.is_dir():
    app.mount("/consumer", StaticFiles(directory=str(_CONSUMER_DIR), html=True), name="consumer")


@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/consumer/landing.html")
