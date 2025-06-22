import os
from fastapi import APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv
from .agents import handle_message
from .schemas import ConversationMessage, WebsiteInfo
from websites import DB_PATH as WEBSITES_DB_PATH 
import json

load_dotenv()

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    website_id: int = None  # Optional, for product queries

@router.post("/chat")
async def chat(request: ChatRequest):
    user_message = request.message
    website_id = request.website_id
    website = None
    website_url = None
    if website_id:
        # Load website info
        with open(WEBSITES_DB_PATH, 'r') as f:
            db = json.load(f)
        for w in db.get('websites', []):
            if w.get('id') == website_id:
                website = WebsiteInfo(**w)
                website_url = website.url
                break
    # If product query, use product_info tool
    if website_url:
        from .agents import product_info, save_conversation
        product = product_info(user_message, website_url)
        ai_content = product.get('content', str(product))
        ai_message = ConversationMessage(role="assistant", content=ai_content, image=product.get('image'), price=product.get('price'), link=product.get('link'))
        user_msg = ConversationMessage(role="user", content=user_message)
        save_conversation(website_id, user_msg, ai_message)
        return {"response": ai_content, "product": product}
    else:
        from .agents import handle_message, save_conversation
        ai_content = await handle_message(user_message)
        ai_message = ConversationMessage(role="assistant", content=ai_content)
        user_msg = ConversationMessage(role="user", content=user_message)
        save_conversation(website_id or 0, user_msg, ai_message)
        return {"response": ai_content}
