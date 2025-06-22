# agents.py using Google ADK
import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google import genai
from google.genai import types
import json
from datetime import datetime
from typing import Optional, Dict
from .schemas import ProductInfo, Conversation, ConversationMessage, WebsiteInfo, ProductComparisonResult

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Set up the google-genai client
if GOOGLE_API_KEY:
    client = genai.Client(api_key=GOOGLE_API_KEY)
else:
    print("WARNING: GOOGLE_API_KEY not found in environment variables")
    client = None

MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash-001"
MODEL_GEMINI_2_5_FLASH = "gemini-2.5-flash"
DB_PATH = os.path.join(os.path.dirname(__file__), '../db.json')

def save_conversation(website_id: int, user_message: ConversationMessage, ai_message: ConversationMessage):
    # Load DB
    with open(DB_PATH, 'r') as f:
        db = json.load(f)
    conversations = db.get('conversations', [])
    new_id = max([c.get('id', 0) for c in conversations], default=0) + 1
    conversation = {
        'id': new_id,
        'website_id': website_id if website_id is not None else 0,
        'messages': [user_message.dict(), ai_message.dict()],
        'created_at': datetime.utcnow().isoformat() + 'Z'
    }
    conversations.append(conversation)
    db['conversations'] = conversations
    with open(DB_PATH, 'w') as f:
        json.dump(db, f, indent=4)
    return conversation

# --- Define Product Info Tool ---
def product_info(query: str, website_url: str) -> dict:
    """Provides product information, pricing, and handles product-related queries using Gemini API (google-genai)."""
    if not client:
        return {"error": "Gemini client not configured."}
    prompt = f"User Query: {query}\nWebsite: {website_url}"
    try:
        response = client.models.generate_content(
            model=MODEL_GEMINI_2_0_FLASH,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=ProductInfo,
                candidate_count=1,
                temperature=0.1,
            )
        )
        print(f"Response from Gemini: {response.text}")
        # The SDK will return .text as JSON string, parse it
        import json as pyjson
        data = pyjson.loads(response.text)
        product = ProductInfo(**data)
        return product.dict()
    except Exception as e:
        return {"error": f"Failed to get product info: {e}"}

# --- Define Support Agent ---
def support_agent_info(query: str, website_url: str) -> dict:
    """Support Agent: Answers queries from the selected website."""
    if not website_url:
        return {"error": "No website URL provided."}
    prompt = f"You are a support agent. Use the following website content to answer the user's question.\nWebsite Content: User Query: {query}\nRespond concisely and helpfully."
    try:
        response = client.models.generate_content(
            model=MODEL_GEMINI_2_5_FLASH,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type='text/plain')
        )
        return {"content": response.text}
    except Exception as e:
        return {"error": f"Support agent failed: {e}"}

# --- Define Compare Product Tool ---
def compare_product_info(product1: str, product2: str, website_url: str) -> dict:
    """Compares two products using Gemini and returns a structured comparison for UI card/table display."""
    if not client:
        return {"error": "Gemini client not configured."}
    prompt = (
        f"Compare the following two products from the website: {website_url}.\n"
        f"Product 1: {product1}\n"
        f"Product 2: {product2}\n"
        "Return a JSON object with these fields: 'product1' (object: name, image, price, link, summary), 'product2' (object: name, image, price, link, summary), "
        "'comparison' (array of {label, product1_value, product2_value}), 'winner' (string), and 'summary' (string).\n"
        "If you cannot compare, still return the JSON object with the above fields, and provide an explanation in the 'summary' field."
    )
    try:
        response = client.models.generate_content(
            model=MODEL_GEMINI_2_5_FLASH,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=ProductComparisonResult,
                candidate_count=1,
                temperature=0.2,
            )
        )
        import json as pyjson
        data = pyjson.loads(response.text)
        result = ProductComparisonResult(**data)
        return result.dict()
    except Exception as e:
        return {
            "product1": {"name": product1, "image": None, "price": None, "link": None, "summary": None},
            "product2": {"name": product2, "image": None, "price": None, "link": None, "summary": None},
            "comparison": [],
            "winner": None,
            "summary": f"Failed to compare products: {e}"
        }

# --- Define Greeting Agent ---
greeting_agent = Agent(
    name="greeting_agent",
    model=MODEL_GEMINI_2_0_FLASH,
    instruction="You are the Greeting Agent. Your ONLY task is to provide a friendly greeting or chitchat. Respond warmly to greetings and small talk. Do not answer product or other questions.",
    description="Handles greetings and chitchat.",
    # No tools needed for simple greeting
)

# --- Define Product Agent ---
product_agent = Agent(
    name="product_agent",
    model=MODEL_GEMINI_2_0_FLASH,
    instruction="You are the Product Agent. Your ONLY task is to answer product-related questions, pricing, and catalog inquiries. Use the 'product_info' tool for all product queries.",
    description="Handles product requests and enquiries.",
    tools=[product_info],
)

# --- Define Support Agent ---
support_agent = Agent(
    name="support_agent",
    model=MODEL_GEMINI_2_0_FLASH,
    instruction="You are the Support Agent. Your ONLY task is to answer user queries by fetching and using content from the selected website.",
    description="Handles support queries by fetching website content.",
    tools=[support_agent_info],
)

# --- Define Compare Product Agent ---
compare_product_agent = Agent(
    name="compare_product_agent",
    model=MODEL_GEMINI_2_0_FLASH,
    instruction="You are the Compare Product Agent. Your ONLY task is to compare two products for the user using the 'compare_product_info' tool. Return a structured, professional comparison.",
    description="Handles product comparison requests.",
    tools=[compare_product_info],
)

# --- Define Root Agent (SoGent) ---
sogent_agent = Agent(
    name="sogent_root_agent",
    model=MODEL_GEMINI_2_0_FLASH,
    instruction="You are SoGent, the main customer service agent. Delegate greetings to 'greeting_agent', product queries to 'product_agent', support queries to 'support_agent', and product comparison to 'compare_product_agent'. Handle only customer service, greeting, product support, website support, and product comparison.",
    description="Main agent for SoGent, delegates to greeting, product, support, and compare agents.",
    sub_agents=[greeting_agent, product_agent, support_agent, compare_product_agent],
)

# Define root_agent as required by Google ADK
root_agent = sogent_agent  # This is required by Google ADK to have a root_agent variable

# --- Session and Runner Setup ---
session_service = InMemorySessionService()
APP_NAME = "sogent_app"
USER_ID = "user_2"
SESSION_ID = "session_003"

# Create session at startup (for demo; in production, use per-user/session)
async def ensure_session():
    """Ensure a session exists for the user"""
    try:
        await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    except Exception as e:
        print(f"Error creating session: {e}")
        # If session already exists, this is fine
        pass

# Initialize session flag to ensure we only create it once
session_initialized = False

runner = Runner(agent=sogent_agent, app_name=APP_NAME, session_service=session_service)

# --- Message handler ---
async def handle_message(message: str) -> str:
    """Handle incoming messages from the user"""
    global session_initialized
    
    try:
        # Initialize session if not done yet - using a safer approach
        if not session_initialized:
            # Use create_task to avoid blocking or event loop issues
            try:
                session_initialized = True
                await ensure_session()
            except RuntimeError as e:
                if "already running" in str(e):
                    print("Session creation skipped - loop already running")
                else:
                    raise
        
        content = types.Content(role='user', parts=[types.Part(text=message)])
        final_response = "Agent did not produce a final response."
        
        async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content):
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response = event.content.parts[0].text
                break
    except Exception as e:
        final_response = f"Error processing request: {str(e)}"
        print(f"Error in handle_message: {e}")
    
    return final_response
