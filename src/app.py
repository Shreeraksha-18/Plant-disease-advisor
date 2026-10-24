import io
import json
import logging
import uuid
from typing import List, Optional

from fastapi import Depends, FastAPI, File, HTTPException, Query, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from src.auth import create_access_token, get_current_user, hash_password, verify_password
from src.database import Base, engine, get_db
from src.explain import explain_disease
from src.models import PredictionRecord, User
from src.predict import CLASS_NAMES, predict
from src.schemas import (
    Explanation,
    PredictionOut,
    PredictionUpdate,
    PredictResponse,
    Prediction,
    Token,
    UserCreate,
    UserOut,
)

logger = logging.getLogger("uvicorn.error")

CONFIDENCE_THRESHOLD = 0.70

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Plant Disease Advisor API", version="1.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # fine for a student demo; restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)


def record_to_out(record: PredictionRecord) -> PredictionOut:
    explanation = Explanation(**json.loads(record.explanation_json)) if record.explanation_json else None
    return PredictionOut(
        id=record.id,
        disease=record.disease,
        confidence=record.confidence,
        status=record.status,
        explanation=explanation,
        note=record.note,
        created_at=record.created_at,
    )


def get_owned_record(db: Session, record_id: int, user: User) -> PredictionRecord:
    record = (
        db.query(PredictionRecord)
        .filter(PredictionRecord.id == record_id, PredictionRecord.user_id == user.id)
        .first()
    )
    if record is None:
        # 404 (not 403) so users can't discover other users' record ids
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
def register(payload: UserCreate, db: Session = Depends(get_db)):
    username = payload.username.strip().lower()
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=409, detail="Username already taken")
    user = User(username=username, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=Token, tags=["auth"])
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form.username.strip().lower()).first()
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user.id))


@app.get("/auth/me", response_model=UserOut, tags=["auth"])
def me(current_user: User = Depends(get_current_user)):
    return current_user


# ---------- prediction (Create) ----------

@app.post("/predict", response_model=PredictResponse, tags=["predictions"])
async def predict_disease(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(status_code=400, detail="Only JPEG or PNG images are supported")

    contents = await file.read()
    try:
        image = Image.open(io.BytesIO(contents))
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Could not read the image file")

    disease, confidence = predict(image)
    request_id = str(uuid.uuid4())

    if confidence < CONFIDENCE_THRESHOLD:
        record = PredictionRecord(
            user_id=current_user.id, disease=disease, confidence=confidence, status="uncertain"
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return PredictResponse(
            status="uncertain",
            prediction=Prediction(disease=disease, confidence=confidence),
            message="The model is not confident about this image. Please upload a clear, close-up photo of a single leaf.",
            request_id=request_id,
            record_id=record.id,
        )

    try:
        explanation = explain_disease(disease)
    except Exception as e:
        logger.exception("Explanation failed")
        raise HTTPException(status_code=502, detail=f"Explanation service error: {type(e).__name__}")

    record = PredictionRecord(
        user_id=current_user.id,
        disease=disease,
        confidence=confidence,
        status="ok",
        explanation_json=json.dumps(explanation),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return PredictResponse(
        status="ok",
        prediction=Prediction(disease=disease, confidence=confidence),
        explanation=Explanation(**explanation),
        request_id=request_id,
        record_id=record.id,
    )


# ---------- predictions (Read, Update, Delete) ----------

@app.get("/predictions", response_model=List[PredictionOut], tags=["predictions"])
def list_predictions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    disease: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(PredictionRecord).filter(PredictionRecord.user_id == current_user.id)
    if disease:
        query = query.filter(PredictionRecord.disease == disease)
    rows = query.order_by(PredictionRecord.id.desc()).offset(skip).limit(limit).all()
    return [record_to_out(r) for r in rows]


@app.get("/predictions/{record_id}", response_model=PredictionOut, tags=["predictions"])
def get_prediction(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return record_to_out(get_owned_record(db, record_id, current_user))


@app.put("/predictions/{record_id}", response_model=PredictionOut, tags=["predictions"])
def update_prediction(
    record_id: int,
    payload: PredictionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.note is None and payload.disease is None:
        raise HTTPException(status_code=400, detail="Provide a note or a corrected disease")

    record = get_owned_record(db, record_id, current_user)

    if payload.disease is not None:
        if payload.disease not in CLASS_NAMES:
            raise HTTPException(status_code=400, detail="Unknown disease class")
        record.disease = payload.disease
        record.explanation_json = None      # old explanation no longer matches the corrected label
    if payload.note is not None:
        record.note = payload.note

    db.commit()
    db.refresh(record)
    return record_to_out(record)


@app.delete("/predictions/{record_id}", status_code=204, tags=["predictions"])
def delete_prediction(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = get_owned_record(db, record_id, current_user)
    db.delete(record)
    db.commit()
    return Response(status_code=204)