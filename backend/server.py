from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import secrets
import zipfile
import io
import base64
from fastapi.responses import StreamingResponse

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Pydantic Models
class WebsiteRequest(BaseModel):
    description: str
    site_type: str  # 'vitrine', 'ecommerce', 'blog'
    business_name: str
    primary_color: Optional[str] = "#3B82F6"
    referral_code: Optional[str] = None

class WebsiteResponse(BaseModel):
    id: str
    html_content: str
    css_content: str
    js_content: str
    preview_url: str
    price: float
    created_at: datetime

class ReferralLink(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    used: bool = False

class PaymentSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    website_id: str
    amount: float
    referral_code: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"  # pending, completed, failed

# LLM Integration for website generation
async def generate_website_content(description: str, site_type: str, business_name: str, primary_color: str):
    """Generate website content using Gemini AI"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        # Get Gemini API key from environment
        gemini_key = os.environ.get('GEMINI_API_KEY')
        if not gemini_key:
            raise HTTPException(status_code=500, detail="Gemini API key not configured")
        
        # Create chat instance
        chat = LlmChat(
            api_key=gemini_key,
            session_id=str(uuid.uuid4()),
            system_message=f"""You are an expert web developer who creates beautiful, modern, responsive websites.
            Create a complete website with HTML, CSS, and JavaScript based on the user's requirements.
            
            Requirements:
            - Use modern, clean design principles
            - Make it fully responsive (mobile-first)
            - Include interactive elements where appropriate
            - Use the primary color: {primary_color}
            - Business name: {business_name}
            - Site type: {site_type}
            
            Return your response in this exact format:
            
            HTML:
            [Complete HTML code here]
            
            CSS:
            [Complete CSS code here]
            
            JS:
            [Complete JavaScript code here]
            
            Make sure the website is professional, modern, and fully functional."""
        ).with_model("gemini", "gemini-2.0-flash")
        
        # Generate the website
        prompt = f"""Create a {site_type} website for {business_name}.
        
        Description: {description}
        
        Requirements:
        - Modern, professional design
        - Responsive layout
        - Primary color: {primary_color}
        - Include relevant sections for a {site_type} site
        - Add placeholder content if needed
        - Make it visually appealing and functional"""
        
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        # Parse the response to extract HTML, CSS, and JS
        content = response.strip()
        
        # Extract HTML
        html_start = content.find("HTML:") + 5
        html_end = content.find("CSS:")
        html_content = content[html_start:html_end].strip()
        
        # Extract CSS
        css_start = content.find("CSS:") + 4
        css_end = content.find("JS:")
        css_content = content[css_start:css_end].strip()
        
        # Extract JS
        js_start = content.find("JS:") + 3
        js_content = content[js_start:].strip()
        
        return {
            "html": html_content,
            "css": css_content,
            "js": js_content
        }
        
    except Exception as e:
        logging.error(f"Error generating website: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate website: {str(e)}")

# API Routes
@api_router.post("/generate-website", response_model=WebsiteResponse)
async def generate_website(request: WebsiteRequest):
    """Generate a website based on user requirements"""
    try:
        # Check if referral code is valid and not expired
        price = 15.0
        if request.referral_code:
            referral = await db.referrals.find_one({
                "code": request.referral_code,
                "expires_at": {"$gt": datetime.utcnow()},
                "used": False
            })
            if referral:
                price = 10.0
        
        # Generate website content using AI
        website_content = await generate_website_content(
            request.description,
            request.site_type,
            request.business_name,
            request.primary_color or "#3B82F6"
        )
        
        # Create website record
        website_id = str(uuid.uuid4())
        website_data = {
            "id": website_id,
            "description": request.description,
            "site_type": request.site_type,
            "business_name": request.business_name,
            "primary_color": request.primary_color,
            "html_content": website_content["html"],
            "css_content": website_content["css"],
            "js_content": website_content["js"],
            "price": price,
            "referral_code": request.referral_code,
            "created_at": datetime.utcnow(),
            "paid": False
        }
        
        await db.websites.insert_one(website_data)
        
        return WebsiteResponse(
            id=website_id,
            html_content=website_content["html"],
            css_content=website_content["css"],
            js_content=website_content["js"],
            preview_url=f"/preview/{website_id}",
            price=price,
            created_at=website_data["created_at"]
        )
        
    except Exception as e:
        logging.error(f"Error in generate_website: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/preview/{website_id}")
async def preview_website(website_id: str):
    """Get website preview"""
    website = await db.websites.find_one({"id": website_id})
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    
    # Combine HTML, CSS, and JS into a single HTML page
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{website['business_name']}</title>
    <style>
        {website['css_content']}
    </style>
</head>
<body>
    {website['html_content']}
    <script>
        {website['js_content']}
    </script>
</body>
</html>"""
    
    return {"html": full_html}

@api_router.post("/create-referral")
async def create_referral_link(user_id: str = None):
    """Create a referral link for sharing"""
    if not user_id:
        user_id = str(uuid.uuid4())
    
    referral_code = secrets.token_urlsafe(8)
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    referral_data = {
        "id": str(uuid.uuid4()),
        "code": referral_code,
        "user_id": user_id,
        "created_at": datetime.utcnow(),
        "expires_at": expires_at,
        "used": False
    }
    
    await db.referrals.insert_one(referral_data)
    
    return {
        "referral_code": referral_code,
        "referral_link": f"https://your-domain.com/?ref={referral_code}",
        "expires_at": expires_at
    }

@api_router.post("/create-payment-session")
async def create_payment_session(website_id: str, referral_code: str = None):
    """Create a payment session for PayPal"""
    website = await db.websites.find_one({"id": website_id})
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    
    # Check referral code if provided
    final_price = website["price"]
    if referral_code:
        referral = await db.referrals.find_one({
            "code": referral_code,
            "expires_at": {"$gt": datetime.utcnow()},
            "used": False
        })
        if referral:
            final_price = 10.0
    
    payment_session = {
        "id": str(uuid.uuid4()),
        "website_id": website_id,
        "amount": final_price,
        "referral_code": referral_code,
        "created_at": datetime.utcnow(),
        "status": "pending"
    }
    
    await db.payment_sessions.insert_one(payment_session)
    
    return {
        "payment_session_id": payment_session["id"],
        "amount": final_price,
        "paypal_url": f"https://www.paypal.com/paypalme/YourPayPalUsername/{final_price}EUR"
    }

@api_router.post("/confirm-payment")
async def confirm_payment(payment_session_id: str):
    """Confirm payment and mark website as paid"""
    payment_session = await db.payment_sessions.find_one({"id": payment_session_id})
    if not payment_session:
        raise HTTPException(status_code=404, detail="Payment session not found")
    
    # Update payment status
    await db.payment_sessions.update_one(
        {"id": payment_session_id},
        {"$set": {"status": "completed"}}
    )
    
    # Mark website as paid
    await db.websites.update_one(
        {"id": payment_session["website_id"]},
        {"$set": {"paid": True}}
    )
    
    # Mark referral code as used if applicable
    if payment_session.get("referral_code"):
        await db.referrals.update_one(
            {"code": payment_session["referral_code"]},
            {"$set": {"used": True}}
        )
    
    return {"message": "Payment confirmed successfully"}

@api_router.get("/download/{website_id}")
async def download_website(website_id: str):
    """Download website as ZIP file"""
    website = await db.websites.find_one({"id": website_id})
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    
    if not website.get("paid", False):
        raise HTTPException(status_code=403, detail="Payment required to download website")
    
    # Create ZIP file in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add HTML file
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{website['business_name']}</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    {website['html_content']}
    <script src="script.js"></script>
</body>
</html>"""
        zip_file.writestr("index.html", html_content)
        
        # Add CSS file
        zip_file.writestr("styles.css", website['css_content'])
        
        # Add JS file
        zip_file.writestr("script.js", website['js_content'])
        
        # Add README
        readme_content = f"""# {website['business_name']} Website

Generated on: {website['created_at']}
Site Type: {website['site_type']}

## Files included:
- index.html - Main HTML file
- styles.css - CSS styles
- script.js - JavaScript functionality

## Usage:
1. Extract all files to a folder
2. Open index.html in a web browser
3. Upload to your web hosting service

Enjoy your new website!
"""
        zip_file.writestr("README.md", readme_content)
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(zip_buffer.read()),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={website['business_name']}_website.zip"}
    )

@api_router.get("/")
async def root():
    return {"message": "Website Generator API is running!"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()