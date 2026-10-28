from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Prediction(BaseModel):
    disease: str
    confidence: float


class Explanation(BaseModel):
    summary: str
    symptoms: List[str]
    causes: List[str]
    prevention: List[str]
    source: Optional[str] = None


class PredictResponse(BaseModel):
    status: str                          # "ok" or "uncertain"
    prediction: Prediction
    explanation: Optional[Explanation] = None
    message: Optional[str] = None
    request_id: str
    record_id: Optional[int] = None


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=72)


class UserOut(BaseModel):
    id: int
    username: str

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PredictionOut(BaseModel):
    id: int
    disease: str
    confidence: float
    status: str
    explanation: Optional[Explanation] = None
    note: Optional[str] = None
    created_at: datetime


class PredictionUpdate(BaseModel):
    note: Optional[str] = Field(default=None, max_length=500)
    disease: Optional[str] = None        # corrected label, must be a known class


# --- Chat ---

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    reply: str
    record_id: int


# --- Support / Where to Buy ---

class SupportStore(BaseModel):
    type: str          # "Online", "Government", "Local"
    name: str
    url: Optional[str] = None
    note: str


class SupportResponse(BaseModel):
    disease: str
    disease_readable: str
    recommended_products: List[str]
    where_to_buy: List[SupportStore]
    helpline: str
