from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import asyncio

# Add the current directory to the Python path if needed
current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Import the agents router
from agents import router as agents_router
from agents.agents import ensure_session
from websites import router as websites_router

app = FastAPI()

# Initialize session at startup
@app.on_event("startup")
async def startup_event():
    print("Initializing session at startup...")
    try:
        await ensure_session()
        print("Session initialized successfully")
    except Exception as e:
        print(f"Error initializing session: {e}")

# Path to the frontend directory
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '../frontend')

# Mount static files (css, js, images)
app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")
app.mount("/images", StaticFiles(directory=os.path.join(FRONTEND_DIR, "images")), name="images")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the agents and websites routers
app.include_router(agents_router, prefix="/api")
app.include_router(websites_router, prefix="/api")

@app.get("/")
def read_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    return FileResponse(index_path)

@app.get("/support")
def read_support():
    support_path = os.path.join(FRONTEND_DIR, "support.html")
    return FileResponse(support_path)
