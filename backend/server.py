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
import json
import requests
from fastapi.responses import StreamingResponse

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# PayPal Configuration
PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET')
PAYPAL_BASE_URL = "https://api.sandbox.paypal.com"  # Use sandbox for testing

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# PayPal Access Token Cache
paypal_access_token = None
paypal_token_expires_at = None

async def get_paypal_access_token():
    """Get PayPal access token"""
    global paypal_access_token, paypal_token_expires_at
    
    # Check if we have a valid token
    if paypal_access_token and paypal_token_expires_at and datetime.utcnow() < paypal_token_expires_at:
        return paypal_access_token
    
    # Get new token
    auth_url = f"{PAYPAL_BASE_URL}/v1/oauth2/token"
    
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US"
    }
    
    data = "grant_type=client_credentials"
    
    try:
        response = requests.post(
            auth_url,
            headers=headers,
            data=data,
            auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET)
        )
        
        if response.status_code == 200:
            token_data = response.json()
            paypal_access_token = token_data['access_token']
            expires_in = token_data.get('expires_in', 3600)
            paypal_token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 300)  # 5 min buffer
            return paypal_access_token
        else:
            raise HTTPException(status_code=500, detail="Failed to get PayPal access token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PayPal authentication error: {str(e)}")

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

class PayPalOrderRequest(BaseModel):
    website_id: str
    referral_code: Optional[str] = None

class PayPalOrderResponse(BaseModel):
    order_id: str
    approval_url: str
    amount: float

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
        "referral_link": f"https://707b7a03-8bf6-42b4-a6bc-cbbf63f8a0b5.preview.emergentagent.com/?ref={referral_code}",
        "expires_at": expires_at
    }

@api_router.post("/paypal/create-order", response_model=PayPalOrderResponse)
async def create_paypal_order(request: PayPalOrderRequest):
    """Create a PayPal order for website purchase"""
    try:
        # Get website details
        website = await db.websites.find_one({"id": request.website_id})
        if not website:
            raise HTTPException(status_code=404, detail="Website not found")
        
        # Check referral code if provided
        final_price = website["price"]
        if request.referral_code:
            referral = await db.referrals.find_one({
                "code": request.referral_code,
                "expires_at": {"$gt": datetime.utcnow()},
                "used": False
            })
            if referral:
                final_price = 10.0
        
        # Get PayPal access token
        access_token = await get_paypal_access_token()
        
        # Create PayPal order
        order_url = f"{PAYPAL_BASE_URL}/v2/checkout/orders"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "PayPal-Request-Id": str(uuid.uuid4())
        }
        
        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "reference_id": request.website_id,
                "amount": {
                    "currency_code": "EUR",
                    "value": str(final_price)
                },
                "description": f"Site web AI pour {website['business_name']}"
            }],
            "application_context": {
                "return_url": f"https://707b7a03-8bf6-42b4-a6bc-cbbf63f8a0b5.preview.emergentagent.com/payment-success",
                "cancel_url": f"https://707b7a03-8bf6-42b4-a6bc-cbbf63f8a0b5.preview.emergentagent.com/payment-cancel"
            }
        }
        
        response = requests.post(order_url, headers=headers, json=order_data)
        
        if response.status_code == 201:
            order_response = response.json()
            order_id = order_response["id"]
            
            # Find approval URL
            approval_url = None
            for link in order_response.get("links", []):
                if link.get("rel") == "approve":
                    approval_url = link.get("href")
                    break
            
            if not approval_url:
                raise HTTPException(status_code=500, detail="PayPal approval URL not found")
            
            # Store order in database
            order_data = {
                "id": str(uuid.uuid4()),
                "paypal_order_id": order_id,
                "website_id": request.website_id,
                "amount": final_price,
                "referral_code": request.referral_code,
                "status": "created",
                "created_at": datetime.utcnow()
            }
            
            await db.paypal_orders.insert_one(order_data)
            
            return PayPalOrderResponse(
                order_id=order_id,
                approval_url=approval_url,
                amount=final_price
            )
        else:
            raise HTTPException(status_code=500, detail=f"PayPal order creation failed: {response.text}")
            
    except Exception as e:
        logging.error(f"Error creating PayPal order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/paypal/capture-order/{order_id}")
async def capture_paypal_order(order_id: str):
    """Capture a PayPal order after user approval"""
    try:
        # Get PayPal access token
        access_token = await get_paypal_access_token()
        
        # Capture the order
        capture_url = f"{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "PayPal-Request-Id": str(uuid.uuid4())
        }
        
        response = requests.post(capture_url, headers=headers)
        
        if response.status_code == 201:
            capture_response = response.json()
            
            # Update order status in database
            await db.paypal_orders.update_one(
                {"paypal_order_id": order_id},
                {"$set": {"status": "completed", "captured_at": datetime.utcnow()}}
            )
            
            # Get order details
            order = await db.paypal_orders.find_one({"paypal_order_id": order_id})
            if order:
                # Mark website as paid
                await db.websites.update_one(
                    {"id": order["website_id"]},
                    {"$set": {"paid": True}}
                )
                
                # Mark referral code as used if applicable
                if order.get("referral_code"):
                    await db.referrals.update_one(
                        {"code": order["referral_code"]},
                        {"$set": {"used": True}}
                    )
            
            return {"message": "Payment captured successfully", "capture_id": capture_response["id"]}
        else:
            raise HTTPException(status_code=500, detail=f"PayPal capture failed: {response.text}")
            
    except Exception as e:
        logging.error(f"Error capturing PayPal order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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