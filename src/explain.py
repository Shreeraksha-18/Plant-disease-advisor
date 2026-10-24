import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
USE_LLM = os.getenv("USE_LLM", "true").lower() == "true"
KEYS = ("summary", "symptoms", "causes", "prevention")

with open(Path(__file__).parent / "disease_info.json", encoding="utf-8") as f:
    DISEASE_INFO = json.load(f)

GENERIC = {
    "summary": "A possible disease was detected, but detailed information is not available for this class yet.",
    "symptoms": [],
    "causes": [],
    "prevention": ["Consult a local agriculture officer for advice"],
}


def _gemini_explain(disease_name: str) -> dict:
    from google import genai

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    readable = disease_name.replace("___", " - ").replace("_", " ")
    prompt = f"""A plant disease detection model identified: {readable}.
Return JSON with exactly these keys:
"summary" (string, 2-3 sentences), "symptoms" (list of strings),
"causes" (list of strings), "prevention" (list of strings).
If the label says healthy, say the plant looks healthy and give general care tips.
Give general guidance only: no specific pesticide names or doses, and suggest
a local agriculture officer for treatment advice.
Keep it accurate, farmer-friendly, and concise."""
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )
    parsed = json.loads(response.text)
    return {k: parsed[k] for k in KEYS}      # KeyError here triggers the fallback


def explain_disease(disease_name: str) -> dict:
    if USE_LLM:
        try:
            result = _gemini_explain(disease_name)
            result["source"] = "llm"
            return result
        except Exception as e:
            print(f"[explain] LLM unavailable ({type(e).__name__}), using knowledge base")

    info = DISEASE_INFO.get(disease_name, GENERIC)
    return {**info, "source": "knowledge_base"}