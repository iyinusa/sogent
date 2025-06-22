from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
from urllib.parse import urljoin
import mimetypes
import base64

DB_PATH = os.path.join(os.path.dirname(__file__), 'db.json')

router = APIRouter()

class WebsiteRequest(BaseModel):
    url: str

@router.post("/websites/")
async def add_website(data: WebsiteRequest):
    url = data.url.strip()
    try:
        resp = requests.get(url, timeout=5)
        soup = BeautifulSoup(resp.text, 'html.parser')
        name = soup.title.string.strip() if soup.title else url
        # Try to get description
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        description = desc_tag['content'].strip() if desc_tag and 'content' in desc_tag.attrs else ''
        # Try to get icon (support multiple rel types)
        icon_tag = (
            soup.find('link', rel=lambda x: x and 'icon' in x) or
            soup.find('link', rel=lambda x: x and 'shortcut icon' in x) or
            soup.find('link', rel=lambda x: x and 'apple-touch-icon' in x)
        )
        icon_href = icon_tag['href'] if icon_tag and 'href' in icon_tag.attrs else '/favicon.ico'
        # Resolve relative URLs
        icon_url = urljoin(url, icon_href) if not icon_href.startswith('http') else icon_href
        # Try to fetch the icon and convert to base64
        try:
            icon_resp = requests.get(icon_url, timeout=5)
            if icon_resp.status_code == 200:
                content_type = icon_resp.headers.get('Content-Type')
                if not content_type:
                    # Guess from extension
                    ext = icon_url.split('.')[-1]
                    content_type = mimetypes.types_map.get('.' + ext, 'image/x-icon')
                b64_icon = base64.b64encode(icon_resp.content).decode('utf-8')
                icon = f"data:{content_type};base64,{b64_icon}"
            else:
                icon = ''
        except Exception:
            icon = ''
        # Fallback to icon URL if base64 failed
        if not icon:
            icon = icon_url
        # Load DB
        with open(DB_PATH, 'r') as f:
            db = json.load(f)
        websites = db.get('websites', [])
        new_id = max([w['id'] for w in websites], default=0) + 1
        website = {
            'id': new_id,
            'name': name,
            'url': url,
            'icon': icon,
            'description': description,
            'created_at': datetime.utcnow().isoformat() + 'Z'
        }
        websites.append(website)
        db['websites'] = websites
        with open(DB_PATH, 'w') as f:
            json.dump(db, f, indent=4)
        return website
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch website details: {e}")

@router.get("/websites/")
async def get_websites():
    try:
        with open(DB_PATH, 'r') as f:
            db = json.load(f)
        return db.get('websites', [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load websites: {e}")
