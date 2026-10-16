# src/explain.py
import json
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")   # confirm the current name in AI Studio

def explain_disease(disease_name: str) -> dict:
    prompt = f"""A plant disease detection model identified: {disease_name}.
Return JSON with exactly these keys:
"summary" (string), "symptoms" (list of strings),
"causes" (list of strings), "prevention" (list of strings).
Keep it accurate, farmer-friendly, and concise."""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )
    return json.loads(response.text)