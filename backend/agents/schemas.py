from pydantic import BaseModel
from typing import Optional

class WebsiteInfo(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    url: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[str] = None

class ProductInfo(BaseModel):
    name: str
    content: str
    image: Optional[str] = None
    price: Optional[str] = None
    link: Optional[str] = None

class ConversationMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    image: Optional[str] = None
    price: Optional[str] = None
    link: Optional[str] = None

class Conversation(BaseModel):
    id: int
    website_id: int
    messages: list[ConversationMessage]
    created_at: str

class ProductComparisonItem(BaseModel):
    label: str
    product1_value: str
    product2_value: str

class ProductComparisonProduct(BaseModel):
    name: str
    image: Optional[str] = None
    price: Optional[str] = None
    link: Optional[str] = None
    summary: Optional[str] = None

class ProductComparisonResult(BaseModel):
    product1: ProductComparisonProduct
    product2: ProductComparisonProduct
    comparison: list[ProductComparisonItem]
    winner: Optional[str] = None
    summary: Optional[str] = None
