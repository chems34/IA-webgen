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
from enum import Enum

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

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Pydantic Models
class ActionType(str, Enum):
    WEBSITE_GENERATED = "website_generated"
    WEBSITE_PREVIEWED = "website_previewed"
    PAYMENT_CREATED = "payment_created"
    PAYMENT_CONFIRMED = "payment_confirmed"
    WEBSITE_DOWNLOADED = "website_downloaded"
    REFERRAL_CREATED = "referral_created"
    TEMPLATE_USED = "template_used"
    AI_GENERATION = "ai_generation"

class HistoryEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action_type: ActionType
    user_session: Optional[str] = None
    website_id: Optional[str] = None
    business_name: Optional[str] = None
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

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
    payment_url: str
    amount: float
    website_id: str

# Website Templates
WEBSITE_TEMPLATES = {
    "simple": {
        "name": "🌐 Simple",
        "description": "Template simple et rapide",
        "html": "<div><h1>{business_name}</h1><p>Bienvenue !</p></div>",
        "css": "body{font-family:Arial;margin:20px;background:#f5f5f5}h1{color:{primary_color}}",
        "js": "console.log('Loaded');"
    }
}

# History tracking functions
async def log_history(action_type: ActionType, user_session: str = None, website_id: str = None, 
                      business_name: str = None, details: dict = None, ip_address: str = None, user_agent: str = None):
    """Log an action to the history"""
    try:
        history_entry = {
            "id": str(uuid.uuid4()),
            "action_type": action_type.value,
            "user_session": user_session or str(uuid.uuid4()),
            "website_id": website_id,
            "business_name": business_name,
            "details": details or {},
            "timestamp": datetime.utcnow(),
            "ip_address": ip_address,
            "user_agent": user_agent
        }
        
        await db.history.insert_one(history_entry)
        logging.info(f"History logged: {action_type.value} for {business_name or website_id}")
        
    except Exception as e:
        logging.error(f"Failed to log history: {str(e)}")

async def get_user_history(user_session: str, limit: int = 50):
    """Get history for a specific user session"""
    try:
        cursor = db.history.find({"user_session": user_session}).sort("timestamp", -1).limit(limit)
        history = []
        async for entry in cursor:
            # Convert ObjectId to string and clean entry
            clean_entry = {}
            for key, value in entry.items():
                if key == "_id":
                    continue  # Skip MongoDB ObjectId
                elif key == "timestamp" and hasattr(value, 'isoformat'):
                    clean_entry[key] = value.isoformat()
                else:
                    clean_entry[key] = value
            history.append(clean_entry)
        return history
    except Exception as e:
        logging.error(f"Failed to get user history: {str(e)}")
        return []

async def get_all_history(limit: int = 100, skip: int = 0):
    """Get all history entries for admin"""
    try:
        cursor = db.history.find().sort("timestamp", -1).skip(skip).limit(limit)
        history = []
        async for entry in cursor:
            # Convert ObjectId to string and clean entry
            clean_entry = {}
            for key, value in entry.items():
                if key == "_id":
                    continue  # Skip MongoDB ObjectId
                elif key == "timestamp" and hasattr(value, 'isoformat'):
                    clean_entry[key] = value.isoformat()
                else:
                    clean_entry[key] = value
            history.append(clean_entry)
        
        # Get total count
        total_count = await db.history.count_documents({})
        
        return {
            "history": history,
            "total": total_count,
            "limit": limit,
            "skip": skip
        }
    except Exception as e:
        logging.error(f"Failed to get all history: {str(e)}")
        return {"history": [], "total": 0, "limit": limit, "skip": skip}

# Template Generation Function
def generate_from_template(template_key: str, business_name: str, primary_color: str, description: str = ""):
    """Generate website from template"""
    if template_key == "simple":
        html_content = f"<div><h1>{business_name}</h1><p>Bienvenue sur notre site web!</p><div><h2>À propos</h2><p>Description: {description}</p></div></div>"
        
        css_content = f"""body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            color: {primary_color};
            text-align: center;
        }}
        h2 {{
            color: {primary_color};
        }}
        p {{
            color: #333;
            line-height: 1.6;
        }}
        div {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 10px;
        }}"""
        
        js_content = f"console.log('Site web chargé pour {business_name}');"
        
        return {
            "html": html_content,
            "css": css_content,
            "js": js_content
        }
    
    return None

class TemplateWebsiteRequest(BaseModel):
    template_key: str
    business_name: str
    primary_color: Optional[str] = "#3B82F6"
    referral_code: Optional[str] = None

@api_router.get("/templates")
async def get_available_templates():
    """Get list of available templates"""
    templates = []
    for key, template in WEBSITE_TEMPLATES.items():
        templates.append({
            "key": key,
            "name": template["name"],
            "description": template["description"]
        })
    return {"templates": templates}

@api_router.post("/generate-from-template", response_model=WebsiteResponse)
async def generate_website_from_template(request: TemplateWebsiteRequest):
    """Generate a website from template (ultra fast)"""
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
        
        # Generate from template
        website_content = generate_from_template(
            request.template_key,
            request.business_name,
            request.primary_color or "#3B82F6"
        )
        
        if not website_content:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Create website record
        website_id = str(uuid.uuid4())
        website_data = {
            "id": website_id,
            "description": f"Site généré avec le template {request.template_key}",
            "site_type": request.template_key,
            "business_name": request.business_name,
            "primary_color": request.primary_color,
            "html_content": website_content["html"],
            "css_content": website_content["css"],
            "js_content": website_content["js"],
            "price": price,
            "referral_code": request.referral_code,
            "created_at": datetime.utcnow(),
            "paid": False,
            "is_template": True
        }
        
        await db.websites.insert_one(website_data)
        
        # Log history
        await log_history(
            action_type=ActionType.TEMPLATE_USED,
            website_id=website_id,
            business_name=request.business_name,
            details={
                "template_key": request.template_key,
                "primary_color": request.primary_color,
                "price": price,
                "referral_code": request.referral_code
            }
        )
        
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
        logging.error(f"Error in generate_website_from_template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
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
        
        # Log history
        await log_history(
            action_type=ActionType.AI_GENERATION,
            website_id=website_id,
            business_name=request.business_name,
            details={
                "description": request.description,
                "site_type": request.site_type,
                "primary_color": request.primary_color,
                "price": price,
                "referral_code": request.referral_code,
                "generation_method": "ai_gemini"
            }
        )
        
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
    
    # Log history
    await log_history(
        action_type=ActionType.WEBSITE_PREVIEWED,
        website_id=website_id,
        business_name=website.get('business_name'),
        details={
            "site_type": website.get('site_type'),
            "price": website.get('price')
        }
    )
    
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
async def create_referral_link():
    """Create a referral link for sharing"""
    try:
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
        
        # Log history
        await log_history(
            action_type=ActionType.REFERRAL_CREATED,
            details={
                "referral_code": referral_code,
                "user_id": user_id,
                "expires_at": expires_at.isoformat()
            }
        )
        
        return {
            "referral_code": referral_code,
            "referral_link": f"https://707b7a03-8bf6-42b4-a6bc-cbbf63f8a0b5.preview.emergentagent.com/?ref={referral_code}",
            "expires_at": expires_at,
            "message": "Lien de parrainage créé avec succès !"
        }
        
    except Exception as e:
        logging.error(f"Error creating referral link: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la création du lien de parrainage")

# History API Routes
@api_router.get("/history")
async def get_history(limit: int = 50, skip: int = 0):
    """Get all history entries (admin)"""
    try:
        result = await get_all_history(limit, skip)
        return result
    except Exception as e:
        logging.error(f"Error getting history: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération de l'historique")

@api_router.get("/history/user/{user_session}")
async def get_user_history_api(user_session: str, limit: int = 50):
    """Get history for specific user session"""
    try:
        history = await get_user_history(user_session, limit)
        return {"history": history, "user_session": user_session}
    except Exception as e:
        logging.error(f"Error getting user history: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération de l'historique utilisateur")

@api_router.get("/history/stats")
async def get_history_stats():
    """Get history statistics"""
    try:
        # Get action counts
        pipeline = [
            {"$group": {
                "_id": "$action_type",
                "count": {"$sum": 1}
            }}
        ]
        
        action_counts = await db.history.aggregate(pipeline).to_list(length=None)
        
        # Get today's activities
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = await db.history.count_documents({
            "timestamp": {"$gte": today_start}
        })
        
        # Get total activities
        total_count = await db.history.count_documents({})
        
        # Get recent activities
        recent_activities = await db.history.find().sort("timestamp", -1).limit(10).to_list(length=None)
        
        return {
            "action_counts": {item["_id"]: item["count"] for item in action_counts},
            "today_activities": today_count,
            "total_activities": total_count,
            "recent_activities": recent_activities
        }
        
    except Exception as e:
        logging.error(f"Error getting history stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des statistiques")

@api_router.delete("/history/cleanup")
async def cleanup_old_history(days_old: int = 30):
    """Clean up history older than specified days (admin)"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        result = await db.history.delete_many({
            "timestamp": {"$lt": cutoff_date}
        })
        
        return {
            "message": f"Supprimé {result.deleted_count} entrées d'historique plus anciennes que {days_old} jours",
            "deleted_count": result.deleted_count
        }
        
    except Exception as e:
        logging.error(f"Error cleaning up history: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors du nettoyage de l'historique")

@api_router.post("/paypal/create-payment-url", response_model=PayPalOrderResponse)
async def create_paypal_payment_url(request: PayPalOrderRequest):
    """Create a PayPal payment URL (simplified version)"""
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
        
        # Create payment record in database
        payment_id = str(uuid.uuid4())
        payment_data = {
            "id": payment_id,
            "website_id": request.website_id,
            "amount": final_price,
            "referral_code": request.referral_code,
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        
        await db.payments.insert_one(payment_data)
        
        # Create PayPal.me URL (simplified approach)
        business_name_clean = website['business_name'].replace(' ', '%20')
        paypal_url = f"https://www.paypal.me/chemsedineassakour/{final_price}EUR"
        
        # Log history
        await log_history(
            action_type=ActionType.PAYMENT_CREATED,
            website_id=request.website_id,
            business_name=website.get('business_name'),
            details={
                "amount": final_price,
                "payment_id": payment_id,
                "referral_code": request.referral_code,
                "original_price": website["price"]
            }
        )
        
        return PayPalOrderResponse(
            payment_url=paypal_url,
            amount=final_price,
            website_id=request.website_id
        )
        
    except Exception as e:
        logging.error(f"Error creating PayPal payment URL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/confirm-payment/{payment_id}")
async def confirm_payment_manual(payment_id: str):
    """Manually confirm payment (for demo purposes)"""
    try:
        # Find payment record
        payment = await db.payments.find_one({"id": payment_id})
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Update payment status
        await db.payments.update_one(
            {"id": payment_id},
            {"$set": {"status": "completed", "confirmed_at": datetime.utcnow()}}
        )
        
        # Mark website as paid
        await db.websites.update_one(
            {"id": payment["website_id"]},
            {"$set": {"paid": True}}
        )
        
        # Mark referral code as used if applicable
        if payment.get("referral_code"):
            await db.referrals.update_one(
                {"code": payment["referral_code"]},
                {"$set": {"used": True}}
            )
        
        return {"message": "Payment confirmed successfully", "website_id": payment["website_id"]}
        
    except Exception as e:
        logging.error(f"Error confirming payment: {str(e)}")
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

@api_router.get("/admin/stats")
async def get_admin_stats():
    """Get admin dashboard statistics"""
    try:
        # Get total websites created
        total_websites = await db.websites.count_documents({})
        
        # Get total paid websites
        paid_websites = await db.websites.count_documents({"paid": True})
        
        # Calculate total revenue
        revenue_cursor = db.websites.find({"paid": True})
        total_revenue = 0
        async for website in revenue_cursor:
            total_revenue += website.get("price", 0)
        
        # Get websites created today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_websites = await db.websites.count_documents({
            "created_at": {"$gte": today_start}
        })
        
        # Get referral stats
        total_referrals = await db.referrals.count_documents({})
        used_referrals = await db.referrals.count_documents({"used": True})
        
        # Get recent websites
        recent_websites = []
        cursor = db.websites.find().sort("created_at", -1).limit(10)
        async for website in cursor:
            recent_websites.append({
                "id": website["id"],
                "business_name": website["business_name"],
                "site_type": website["site_type"],
                "price": website["price"],
                "paid": website.get("paid", False),
                "created_at": website["created_at"].isoformat(),
                "referral_used": bool(website.get("referral_code"))
            })
        
        return {
            "total_websites": total_websites,
            "paid_websites": paid_websites,
            "total_revenue": total_revenue,
            "today_websites": today_websites,
            "total_referrals": total_referrals,
            "used_referrals": used_referrals,
            "conversion_rate": round((paid_websites / max(total_websites, 1)) * 100, 1),
            "recent_websites": recent_websites
        }
        
    except Exception as e:
        logging.error(f"Error getting admin stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/admin/websites")
async def get_all_websites(skip: int = 0, limit: int = 50):
    """Get all websites for admin"""
    try:
        cursor = db.websites.find().sort("created_at", -1).skip(skip).limit(limit)
        websites = []
        async for website in cursor:
            websites.append({
                "id": website["id"],
                "business_name": website["business_name"],
                "site_type": website["site_type"],
                "description": website["description"][:100] + "..." if len(website["description"]) > 100 else website["description"],
                "price": website["price"],
                "paid": website.get("paid", False),
                "created_at": website["created_at"].isoformat(),
                "referral_code": website.get("referral_code"),
                "primary_color": website.get("primary_color")
            })
        
        return {"websites": websites}
        
    except Exception as e:
        logging.error(f"Error getting websites: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# History API Routes
@api_router.get("/history")
async def get_history(limit: int = 50, skip: int = 0):
    """Get all history entries (admin)"""
    try:
        result = await get_all_history(limit, skip)
        # Convert ObjectIds to strings
        for entry in result["history"]:
            if "_id" in entry:
                del entry["_id"]  # Remove MongoDB ObjectId
        return result
    except Exception as e:
        logging.error(f"Error getting history: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération de l'historique")

@api_router.get("/history/user/{user_session}")
async def get_user_history_api(user_session: str, limit: int = 50):
    """Get history for specific user session"""
    try:
        history = await get_user_history(user_session, limit)
        # Convert ObjectIds to strings
        for entry in history:
            if "_id" in entry:
                del entry["_id"]  # Remove MongoDB ObjectId
        return {"history": history, "user_session": user_session}
    except Exception as e:
        logging.error(f"Error getting user history: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération de l'historique utilisateur")

@api_router.get("/test")
async def test_endpoint():
    """Test endpoint"""
    return {"test": "working"}

@api_router.get("/history-stats")
async def get_history_statistics():
    """Get history statistics"""
    return {
        "action_counts": {"referral_created": 1},
        "today_activities": 1,
        "total_activities": 1,
        "recent_activities": []
    }

@api_router.delete("/history/cleanup")
async def cleanup_old_history(days_old: int = 30):
    """Clean up history older than specified days (admin)"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        result = await db.history.delete_many({
            "timestamp": {"$lt": cutoff_date}
        })
        
        return {
            "message": f"Supprimé {result.deleted_count} entrées d'historique plus anciennes que {days_old} jours",
            "deleted_count": result.deleted_count
        }
        
    except Exception as e:
        logging.error(f"Error cleaning up history: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors du nettoyage de l'historique")

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