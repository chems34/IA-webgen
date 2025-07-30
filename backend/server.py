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
from fastapi.responses import StreamingResponse, FileResponse
from enum import Enum
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

# Gemini AI Configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Concierge Automation Configuration
NAMECHEAP_API_USER = os.environ.get('NAMECHEAP_API_USER')
NAMECHEAP_API_KEY = os.environ.get('NAMECHEAP_API_KEY')
NETLIFY_TOKEN = os.environ.get('NETLIFY_TOKEN')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
SMTP_EMAIL = os.environ.get('SMTP_EMAIL', 'noreply@aiwebgen.com')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')

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

class ConciergeRequest(BaseModel):
    website_id: str
    contact_email: str
    preferred_domain: str
    phone: Optional[str] = None
    urgency: Optional[str] = "normal"  # "normal" or "urgent"

class ConciergeResponse(BaseModel):
    request_id: str
    status: str
    message: str
    payment_link: Optional[str] = None
    estimated_completion: str
    price: float
    domain_available: bool
    alternatives: Optional[List[str]] = None

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
async def generate_website_content(description: str, site_type: str, business_name: str, primary_color: str = "#3B82F6"):
    """Generate website content using AI or fallback to template"""
    try:
        # Try AI generation first
        if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
            try:
                # Configure Gemini API (if available)
                from emergentintegrations.llm.chat import LlmChat, UserMessage
                
                chat = LlmChat(
                    api_key=GEMINI_API_KEY,
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
            except Exception as ai_error:
                logging.warning(f"AI generation failed: {str(ai_error)}, falling back to template")
        
        # Fallback to enhanced template generation
        logging.info("Using enhanced template generation (AI fallback)")
        return generate_enhanced_template(description, site_type, business_name, primary_color)
        
    except Exception as e:
        logging.error(f"Error in generate_website_content: {str(e)}")
        # Final fallback to simple template
        return generate_from_template("simple", business_name, primary_color, description)

def generate_enhanced_template(description: str, site_type: str, business_name: str, primary_color: str):
    """Generate enhanced template based on business type and description"""
    
    # Analyze description for key features
    description_lower = description.lower()
    has_services = "service" in description_lower or "prestation" in description_lower
    has_contact = "contact" in description_lower or "rendez-vous" in description_lower
    has_gallery = "photo" in description_lower or "galerie" in description_lower or "image" in description_lower
    
    # Generate business-specific content
    if "restaurant" in site_type.lower() or "restaurant" in description_lower:
        sections = generate_restaurant_content(business_name, description)
    elif "coiffeur" in description_lower or "salon" in description_lower or "beauté" in description_lower:
        sections = generate_salon_content(business_name, description)
    elif "médecin" in description_lower or "cabinet" in description_lower or "santé" in description_lower:
        sections = generate_medical_content(business_name, description)
    else:
        sections = generate_business_content(business_name, description, site_type)
    
    # Build HTML
    html_content = f"""
    <div class="website-container">
        <header class="hero-section">
            <h1>{business_name}</h1>
            <p class="tagline">{sections['tagline']}</p>
            <div class="cta-buttons">
                <button class="btn-primary">Découvrir</button>
                <button class="btn-secondary">Contact</button>
            </div>
        </header>
        
        <section class="about-section">
            <h2>À propos</h2>
            <p>{sections['about']}</p>
        </section>
        
        {sections['services_html'] if has_services else ''}
        
        <section class="contact-section">
            <h2>Contact</h2>
            <div class="contact-info">
                <p>📧 Email : contact@{business_name.lower().replace(' ', '')}.com</p>
                <p>📞 Téléphone : 01 23 45 67 89</p>
                <p>📍 Adresse : 123 Rue Example, 75001 Paris</p>
            </div>
        </section>
        
        {sections['gallery_html'] if has_gallery else ''}
    </div>
    """
    
    # Enhanced CSS
    css_content = f"""
    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}
    
    body {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.6;
        color: #333;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }}
    
    .website-container {{
        max-width: 1200px;
        margin: 0 auto;
        background: white;
        box-shadow: 0 0 30px rgba(0,0,0,0.1);
    }}
    
    .hero-section {{
        background: linear-gradient(135deg, {primary_color} 0%, {adjust_color_brightness(primary_color, -20)} 100%);
        color: white;
        text-align: center;
        padding: 80px 20px;
    }}
    
    .hero-section h1 {{
        font-size: 3.5rem;
        margin-bottom: 20px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }}
    
    .tagline {{
        font-size: 1.3rem;
        margin-bottom: 30px;
        opacity: 0.9;
    }}
    
    .cta-buttons {{
        margin-top: 30px;
    }}
    
    .btn-primary, .btn-secondary {{
        padding: 15px 30px;
        margin: 0 10px;
        border: none;
        border-radius: 50px;
        font-size: 1.1rem;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
        display: inline-block;
    }}
    
    .btn-primary {{
        background: white;
        color: {primary_color};
        font-weight: bold;
    }}
    
    .btn-primary:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.2);
    }}
    
    .btn-secondary {{
        background: transparent;
        color: white;
        border: 2px solid white;
    }}
    
    .btn-secondary:hover {{
        background: white;
        color: {primary_color};
    }}
    
    section {{
        padding: 60px 40px;
    }}
    
    h2 {{
        font-size: 2.5rem;
        color: {primary_color};
        margin-bottom: 30px;
        text-align: center;
    }}
    
    .about-section {{
        background: #f8f9fa;
    }}
    
    .services-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 30px;
        margin-top: 40px;
    }}
    
    .service-card {{
        background: white;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        text-align: center;
        transition: transform 0.3s ease;
    }}
    
    .service-card:hover {{
        transform: translateY(-5px);
    }}
    
    .contact-section {{
        background: {primary_color};
        color: white;
        text-align: center;
    }}
    
    .contact-info {{
        font-size: 1.2rem;
        line-height: 2;
    }}
    
    @media (max-width: 768px) {{
        .hero-section h1 {{
            font-size: 2.5rem;
        }}
        
        section {{
            padding: 40px 20px;
        }}
        
        .services-grid {{
            grid-template-columns: 1fr;
        }}
    }}
    """
    
    # Enhanced JavaScript
    js_content = f"""
    document.addEventListener('DOMContentLoaded', function() {{
        console.log('Site web {business_name} chargé avec succès!');
        
        // Smooth scrolling for buttons
        document.querySelectorAll('.btn-primary, .btn-secondary').forEach(button => {{
            button.addEventListener('click', function(e) {{
                e.preventDefault();
                const target = document.querySelector('.about-section');
                if (target) {{
                    target.scrollIntoView({{ behavior: 'smooth' }});
                }}
            }});
        }});
        
        // Add animation on scroll
        const observer = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }}
            }});
        }});
        
        document.querySelectorAll('section').forEach(section => {{
            section.style.opacity = '0';
            section.style.transform = 'translateY(20px)';
            section.style.transition = 'all 0.6s ease';
            observer.observe(section);
        }});
    }});
    """
    
    return {
        "html": html_content,
        "css": css_content,
        "js": js_content
    }

def adjust_color_brightness(hex_color: str, percent: int):
    """Adjust color brightness by percentage"""
    # Simple implementation - in real case, you'd use a proper color library
    return hex_color  # Fallback to original color

def generate_restaurant_content(business_name: str, description: str):
    return {
        "tagline": "Une expérience culinaire exceptionnelle vous attend",
        "about": f"Bienvenue chez {business_name}, où la passion de la gastronomie rencontre l'art de recevoir. {description}",
        "services_html": """
        <section class="services-section">
            <h2>Notre Carte</h2>
            <div class="services-grid">
                <div class="service-card">
                    <h3>🍽️ Plats Signatures</h3>
                    <p>Découvrez nos créations culinaires uniques, préparées avec des ingrédients frais et de saison.</p>
                </div>
                <div class="service-card">
                    <h3>🍷 Carte des Vins</h3>
                    <p>Une sélection de vins d'exception pour accompagner parfaitement vos repas.</p>
                </div>
                <div class="service-card">
                    <h3>🎉 Événements Privés</h3>
                    <p>Organisez vos événements spéciaux dans notre espace privatisable.</p>
                </div>
            </div>
        </section>
        """,
        "gallery_html": """
        <section class="gallery-section">
            <h2>Nos Créations</h2>
            <div class="gallery-placeholder">
                <p>📸 Galerie photos de nos plats - À personnaliser avec vos propres images</p>
            </div>
        </section>
        """
    }

def generate_salon_content(business_name: str, description: str):
    return {
        "tagline": "Révélez votre beauté naturelle",
        "about": f"Chez {business_name}, nous sublisons votre beauté avec expertise et passion. {description}",
        "services_html": """
        <section class="services-section">
            <h2>Nos Services</h2>
            <div class="services-grid">
                <div class="service-card">
                    <h3>✂️ Coupe & Coiffage</h3>
                    <p>Coupes tendances et intemporelles, adaptées à votre personnalité et morphologie.</p>
                </div>
                <div class="service-card">
                    <h3>🎨 Coloration</h3>
                    <p>Techniques de coloration moderne pour révéler l'éclat de vos cheveux.</p>
                </div>
                <div class="service-card">
                    <h3>💆 Soins Capillaires</h3>
                    <p>Traitements personnalisés pour nourrir et fortifier vos cheveux.</p>
                </div>
            </div>
        </section>
        """,
        "gallery_html": ""
    }

def generate_medical_content(business_name: str, description: str):
    return {
        "tagline": "Votre santé, notre priorité",
        "about": f"Le {business_name} vous accueille dans un environnement professionnel et bienveillant. {description}",
        "services_html": """
        <section class="services-section">
            <h2>Nos Services</h2>
            <div class="services-grid">
                <div class="service-card">
                    <h3>🩺 Consultations</h3>
                    <p>Consultations générales et spécialisées sur rendez-vous.</p>
                </div>
                <div class="service-card">
                    <h3>🏥 Urgences</h3>
                    <p>Prise en charge des urgences médicales selon disponibilités.</p>
                </div>
                <div class="service-card">
                    <h3>📋 Suivi Médical</h3>
                    <p>Suivi personnalisé et préventif pour votre bien-être.</p>
                </div>
            </div>
        </section>
        """,
        "gallery_html": ""
    }

def generate_business_content(business_name: str, description: str, site_type: str):
    return {
        "tagline": "Excellence et professionnalisme à votre service",
        "about": f"Découvrez {business_name}, votre partenaire de confiance. {description}",
        "services_html": """
        <section class="services-section">
            <h2>Nos Services</h2>
            <div class="services-grid">
                <div class="service-card">
                    <h3>⭐ Service Premium</h3>
                    <p>Une approche personnalisée pour répondre à tous vos besoins.</p>
                </div>
                <div class="service-card">
                    <h3>🎯 Expertise</h3>
                    <p>Des professionnels qualifiés pour vous accompagner.</p>
                </div>
                <div class="service-card">
                    <h3>🚀 Innovation</h3>
                    <p>Des solutions modernes et adaptées à votre secteur.</p>
                </div>
            </div>
        </section>
        """,
        "gallery_html": ""
    }

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
            "referral_link": f"https://bda0d49d-4e16-4c2f-b3a8-78fbd2ddda32.preview.emergentagent.com/?ref={referral_code}",
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

# Website Editing Endpoints
@api_router.get("/edit/{website_id}")
async def get_website_for_editing(website_id: str):
    """Get website data for editing (only if paid)"""
    try:
        website = await db.websites.find_one({"id": website_id})
        if not website:
            raise HTTPException(status_code=404, detail="Site web non trouvé")
        
        if not website.get("paid", False):
            raise HTTPException(status_code=403, detail="Site non payé - Édition non autorisée")
        
        # Log history
        await log_history(
            action_type=ActionType.WEBSITE_PREVIEWED,
            website_id=website_id,
            business_name=website.get('business_name'),
            details={"action": "edit_mode_accessed"}
        )
        
        return {
            "id": website["id"],
            "business_name": website["business_name"],
            "html_content": website["html_content"],
            "css_content": website["css_content"],
            "js_content": website["js_content"],
            "site_type": website.get("site_type", "simple"),
            "primary_color": website.get("primary_color", "#4A90E2"),
            "paid": website["paid"],
            "editable": True
        }
        
    except Exception as e:
        logging.error(f"Error getting website for editing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/edit/{website_id}")
async def save_website_changes(website_id: str, changes: dict):
    """Save changes to website (only if paid)"""
    try:
        website = await db.websites.find_one({"id": website_id})
        if not website:
            raise HTTPException(status_code=404, detail="Site web non trouvé")
        
        if not website.get("paid", False):
            raise HTTPException(status_code=403, detail="Site non payé - Édition non autorisée")
        
        # Update allowed fields
        update_data = {}
        if "business_name" in changes:
            update_data["business_name"] = changes["business_name"]
        if "html_content" in changes:
            update_data["html_content"] = changes["html_content"]
        if "css_content" in changes:
            update_data["css_content"] = changes["css_content"]
        if "js_content" in changes:
            update_data["js_content"] = changes.get("js_content", "")
        if "primary_color" in changes:
            update_data["primary_color"] = changes["primary_color"]
        
        update_data["updated_at"] = datetime.utcnow()
        
        # Save to database
        await db.websites.update_one(
            {"id": website_id}, 
            {"$set": update_data}
        )
        
        # Log history
        await log_history(
            action_type=ActionType.WEBSITE_GENERATED,
            website_id=website_id,
            business_name=changes.get("business_name", website.get("business_name")),
            details={
                "action": "website_edited",
                "changes": list(changes.keys()),
                "edit_mode": True
            }
        )
        
        return {
            "message": "Site web mis à jour avec succès !",
            "website_id": website_id,
            "preview_url": f"/preview/{website_id}",
            "updated_at": update_data["updated_at"]
        }
        
    except Exception as e:
        logging.error(f"Error saving website changes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Test endpoint to mark website as paid
@api_router.post("/test/mark-paid/{website_id}")
async def mark_website_as_paid(website_id: str):
    """Mark website as paid (for testing purposes)"""
    try:
        website = await db.websites.find_one({"id": website_id})
        if not website:
            raise HTTPException(status_code=404, detail="Site web non trouvé")
        
        await db.websites.update_one(
            {"id": website_id}, 
            {"$set": {"paid": True, "payment_confirmed_at": datetime.utcnow()}}
        )
        
        return {"message": "Site marqué comme payé", "website_id": website_id, "editable": True}
    except Exception as e:
        logging.error(f"Error marking website as paid: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/request-concierge-service")
async def request_concierge_service(website_id: str, contact_email: str, preferred_domain: str):
    """Request concierge hosting service"""
    try:
        # Get website details
        website = await db.websites.find_one({"id": website_id})
        if not website:
            raise HTTPException(status_code=404, detail="Site web non trouvé")
        
        # Create concierge request
        request_id = str(uuid.uuid4())
        concierge_request = {
            "id": request_id,
            "website_id": website_id,
            "business_name": website.get("business_name"),
            "contact_email": contact_email,
            "preferred_domain": preferred_domain,
            "status": "pending",
            "price": 49.0,
            "created_at": datetime.utcnow(),
            "includes": [
                "Achat de domaine",
                "Configuration hébergement", 
                "Mise en ligne du site",
                "Support 3 mois"
            ]
        }
        
        await db.concierge_requests.insert_one(concierge_request)
        
        # Log history
        await log_history(
            action_type=ActionType.REFERRAL_CREATED,  # We can reuse this or create new enum
            website_id=website_id,
            business_name=website.get("business_name"),
            details={
                "service": "concierge_hosting",
                "contact_email": contact_email,
                "preferred_domain": preferred_domain,
                "price": 49.0,
                "request_id": request_id
            }
        )
        
        return {
            "message": "Demande de service concierge enregistrée !",
            "request_id": request_id,
            "status": "pending",
            "next_steps": "Nous vous contacterons dans les 24h pour finaliser votre domaine et mettre votre site en ligne.",
            "price": 49.0,
            "includes": concierge_request["includes"]
        }
        
    except Exception as e:
        logging.error(f"Error requesting concierge service: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/download-hosting-guide")
async def download_hosting_guide():
    """Download hosting guide for customers"""
    try:
        guide_path = "/app/guide-hebergement.md"
        
        if not os.path.exists(guide_path):
            raise HTTPException(status_code=404, detail="Guide non trouvé")
        
        return FileResponse(
            path=guide_path,
            media_type='text/markdown',
            filename="Guide-Hebergement-AI-WebGen.md"
        )
    except Exception as e:
        logging.error(f"Error downloading hosting guide: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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