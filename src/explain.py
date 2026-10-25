import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

USE_LLM = os.getenv("USE_LLM", "true").lower() == "true"
PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()          # "groq" or "gemini"
TIMEOUT = float(os.getenv("LLM_TIMEOUT", "12"))                # seconds to wait before falling back
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

KEYS = ("summary", "symptoms", "causes", "prevention")

with open(Path(__file__).parent / "disease_info.json", encoding="utf-8") as f:
    DISEASE_INFO = json.load(f)

GENERIC = {
    "summary": "A possible disease was detected, but detailed information is not available for this class yet.",
    "symptoms": [],
    "causes": [],
    "prevention": ["Consult a local agriculture officer for advice"],
}

SYSTEM = (
    "You are a plant health assistant for farmers. Reply with JSON only. "
    "Give general guidance only: no specific pesticide names or doses, "
    "and suggest a local agriculture officer for treatment advice."
)


def _prompt(disease_name: str) -> str:
    readable = disease_name.replace("___", " - ").replace("_", " ")
    return f"""A plant disease detection model identified: {readable}.
Return JSON with exactly these keys:
"summary" (string, 2-3 sentences), "symptoms" (list of strings),
"causes" (list of strings), "prevention" (list of strings).
If the label says healthy, say the plant looks healthy and give general care tips.
Keep it accurate, farmer-friendly, and concise."""


def _clean(parsed: dict) -> dict:
    """Keep only the four expected fields and check their types; anything else raises."""
    out = {k: parsed[k] for k in KEYS}
    if not isinstance(out["summary"], str) or not out["summary"].strip():
        raise ValueError("summary missing")
    for k in ("symptoms", "causes", "prevention"):
        if not isinstance(out[k], list) or not all(isinstance(i, str) for i in out[k]):
            raise ValueError(f"{k} is not a list of strings")
    return out


def _groq_explain(disease_name: str) -> dict:
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": "Bearer " + os.environ["GROQ_API_KEY"]},
        json={
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": _prompt(disease_name)},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.3,
        },
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return _clean(json.loads(r.json()["choices"][0]["message"]["content"]))


def _gemini_explain(disease_name: str) -> dict:
    from google import genai

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=SYSTEM + "\n\n" + _prompt(disease_name),
        config={"response_mime_type": "application/json"},
    )
    return _clean(json.loads(response.text))


def explain_disease(disease_name: str) -> dict:
    if USE_LLM:
        try:
            result = _gemini_explain(disease_name) if PROVIDER == "gemini" else _groq_explain(disease_name)
            result["source"] = "llm"
            return result
        except Exception as e:
            detail = ""
            if isinstance(e, requests.HTTPError) and e.response is not None:
                detail = f" status={e.response.status_code} body={e.response.text[:300]}"
            print(f"[explain] LLM ({PROVIDER}) unavailable: {type(e).__name__}{detail}, using knowledge base")

    info = DISEASE_INFO.get(disease_name, GENERIC)
    return {**info, "source": "knowledge_base"}