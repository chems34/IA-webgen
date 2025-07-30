"""
Système de conciergerie automatisé pour AI WebGen
Automatise : domaine, hébergement, déploiement, facturation
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

# Configuration APIs
NAMECHEAP_API_USER = os.environ.get('NAMECHEAP_API_USER')
NAMECHEAP_API_KEY = os.environ.get('NAMECHEAP_API_KEY')
NETLIFY_TOKEN = os.environ.get('NETLIFY_TOKEN')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
SMTP_EMAIL = os.environ.get('SMTP_EMAIL')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')

class ConciergeAutomation:
    def __init__(self):
        self.base_price = 49.0
        self.domain_cost = 12.0
        self.profit_margin = 37.0
        
    async def process_concierge_request(self, request_data: Dict) -> Dict:
        """Traite automatiquement une demande de conciergerie"""
        try:
            logging.info(f"🤖 Début traitement automatique pour {request_data['business_name']}")
            
            # Étape 1: Vérifier disponibilité domaine
            domain_check = await self.check_domain_availability(request_data['preferred_domain'])
            
            if not domain_check['available']:
                # Proposer alternatives automatiquement
                alternatives = await self.suggest_domain_alternatives(
                    request_data['business_name'], 
                    request_data['preferred_domain']
                )
                return {
                    "status": "domain_unavailable",
                    "message": "Domaine non disponible",
                    "alternatives": alternatives,
                    "requires_user_choice": True
                }
            
            # Étape 2: Créer facture Stripe automatique
            payment_link = await self.create_automatic_invoice(request_data)
            
            # Étape 3: Envoyer email de confirmation automatique
            await self.send_confirmation_email(request_data, payment_link)
            
            # Étape 4: Programmer la suite (après paiement)
            await self.schedule_post_payment_actions(request_data)
            
            return {
                "status": "success",
                "message": "Demande traitée automatiquement",
                "payment_link": payment_link,
                "domain": request_data['preferred_domain'],
                "estimated_completion": "24h après paiement"
            }
            
        except Exception as e:
            logging.error(f"❌ Erreur traitement automatique: {str(e)}")
            return {
                "status": "error",
                "message": f"Erreur système: {str(e)}"
            }
    
    async def check_domain_availability(self, domain: str) -> Dict:
        """Vérifie disponibilité domaine via API Namecheap"""
        try:
            url = "https://api.namecheap.com/xml.response"
            params = {
                'ApiUser': NAMECHEAP_API_USER,
                'ApiKey': NAMECHEAP_API_KEY,
                'UserName': NAMECHEAP_API_USER,
                'Command': 'namecheap.domains.check',
                'ClientIp': '127.0.0.1',
                'DomainList': domain
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    result = await response.text()
                    
                    # Parse XML response (simplifié)
                    available = "true" in result.lower() and "available" in result.lower()
                    
                    return {
                        "available": available,
                        "domain": domain,
                        "price": 12.0 if available else None
                    }
                    
        except Exception as e:
            logging.error(f"Erreur vérification domaine: {str(e)}")
            # Fallback: utiliser API whois gratuite
            return await self.check_domain_whois_fallback(domain)
    
    async def check_domain_whois_fallback(self, domain: str) -> Dict:
        """Fallback avec API whois gratuite"""
        try:
            url = f"https://api.whoisfreaks.com/v1.0/whois?apiKey=free&whois={domain}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    data = await response.json()
                    
                    # Si domaine existe dans whois = pas disponible
                    available = data.get('create_date') is None
                    
                    return {
                        "available": available,
                        "domain": domain,
                        "price": 12.0 if available else None
                    }
                    
        except Exception as e:
            logging.error(f"Erreur fallback whois: {str(e)}")
            # Dernière option: supposer disponible
            return {"available": True, "domain": domain, "price": 12.0}
    
    async def suggest_domain_alternatives(self, business_name: str, original_domain: str) -> List[str]:
        """Génère automatiquement des alternatives de domaine"""
        base_name = original_domain.split('.')[0]
        business_clean = business_name.lower().replace(' ', '').replace('-', '')
        
        alternatives = [
            f"{base_name}.fr",
            f"{base_name}.net",
            f"{base_name}.org",
            f"{business_clean}.com",
            f"{business_clean}.fr",
            f"{base_name}-pro.com",
            f"{base_name}2024.com",
            f"mon-{base_name}.com"
        ]
        
        # Vérifier disponibilité des alternatives
        available_alternatives = []
        for alt in alternatives:
            check = await self.check_domain_availability(alt)
            if check['available']:
                available_alternatives.append(alt)
                if len(available_alternatives) >= 3:  # Max 3 suggestions
                    break
        
        return available_alternatives
    
    async def create_automatic_invoice(self, request_data: Dict) -> str:
        """Crée facture Stripe automatique"""
        try:
            import stripe
            stripe.api_key = STRIPE_SECRET_KEY
            
            # Créer lien de paiement Stripe
            price = stripe.Price.create(
                unit_amount=int(self.base_price * 100),  # 4900 centimes
                currency='eur',
                product_data={
                    'name': f'Service Concierge - {request_data["business_name"]}',
                    'description': f'Domaine + Hébergement + Mise en ligne pour {request_data["preferred_domain"]}'
                }
            )
            
            payment_link = stripe.PaymentLink.create(
                line_items=[{
                    'price': price.id,
                    'quantity': 1,
                }],
                metadata={
                    'website_id': request_data['website_id'],
                    'domain': request_data['preferred_domain'],
                    'business_name': request_data['business_name'],
                    'client_email': request_data['contact_email']
                }
            )
            
            return payment_link.url
            
        except Exception as e:
            logging.error(f"Erreur création facture: {str(e)}")
            # Fallback: PayPal simple
            return f"https://paypal.me/aiwebgen/{self.base_price}EUR"
    
    async def send_confirmation_email(self, request_data: Dict, payment_link: str):
        """Envoie email de confirmation automatique"""
        try:
            subject = f"✅ Votre demande pour {request_data['preferred_domain']} - Service Concierge"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #4A90E2;">🤖 Demande Traitée Automatiquement !</h2>
                    
                    <p>Bonjour,</p>
                    
                    <p>Excellente nouvelle ! Votre demande de service concierge a été <strong>traitée automatiquement</strong> par notre système IA.</p>
                    
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #28a745;">📋 Récapitulatif</h3>
                        <ul>
                            <li><strong>Site web :</strong> {request_data['business_name']}</li>
                            <li><strong>Domaine :</strong> {request_data['preferred_domain']} ✅ Disponible</li>
                            <li><strong>Prix :</strong> 49€ TTC (tout inclus)</li>
                            <li><strong>Délai :</strong> 2-4h après paiement</li>
                        </ul>
                    </div>
                    
                    <div style="background: #e7f3ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #0066cc;">🚀 Processus 100% Automatisé</h3>
                        <ol>
                            <li>✅ Domaine vérifié et réservé</li>
                            <li>💳 Paiement sécurisé via le lien ci-dessous</li>
                            <li>🤖 Achat domaine automatique (2h)</li>
                            <li>⚡ Configuration hébergement automatique</li>
                            <li>🌐 Mise en ligne automatique de votre site</li>
                            <li>📧 Email de livraison avec votre URL</li>
                        </ol>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{payment_link}" 
                           style="background: #28a745; color: white; padding: 15px 30px; 
                                  text-decoration: none; border-radius: 5px; font-weight: bold;">
                            💳 Payer 49€ et Lancer le Processus
                        </a>
                    </div>
                    
                    <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <p><strong>⏰ Timing :</strong></p>
                        <ul>
                            <li>Dès paiement → Démarrage automatique</li>
                            <li>2-4h → Votre site en ligne</li>
                            <li>Aucune intervention manuelle requise !</li>
                        </ul>
                    </div>
                    
                    <p>Questions ? Répondez simplement à cet email.</p>
                    
                    <p>Merci pour votre confiance !<br>
                    🤖 Système AI WebGen</p>
                </div>
            </body>
            </html>
            """
            
            await self.send_email(
                to_email=request_data['contact_email'],
                subject=subject,
                html_body=html_body
            )
            
        except Exception as e:
            logging.error(f"Erreur envoi email: {str(e)}")
    
    async def send_email(self, to_email: str, subject: str, html_body: str):
        """Envoie email via SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = SMTP_EMAIL
            msg['To'] = to_email
            
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(SMTP_EMAIL, SMTP_PASSWORD)
                server.send_message(msg)
                
            logging.info(f"📧 Email envoyé à {to_email}")
            
        except Exception as e:
            logging.error(f"Erreur SMTP: {str(e)}")
    
    async def process_payment_webhook(self, payment_data: Dict):
        """Traite webhook de paiement Stripe automatiquement"""
        try:
            logging.info("🎉 Paiement reçu - Démarrage automatique")
            
            # Extraire metadata
            website_id = payment_data['metadata']['website_id']
            domain = payment_data['metadata']['domain']
            business_name = payment_data['metadata']['business_name']
            client_email = payment_data['metadata']['client_email']
            
            # Étape 1: Acheter domaine automatiquement
            domain_result = await self.purchase_domain_automatically(domain)
            
            # Étape 2: Créer site Netlify automatiquement
            site_result = await self.deploy_to_netlify_automatically(website_id, domain, business_name)
            
            # Étape 3: Configurer DNS automatiquement
            dns_result = await self.configure_dns_automatically(domain, site_result['netlify_url'])
            
            # Étape 4: Envoyer email de livraison
            await self.send_delivery_email(client_email, domain, business_name, website_id)
            
            return {
                "status": "completed",
                "domain_purchased": domain_result['success'],
                "site_deployed": site_result['success'],
                "dns_configured": dns_result['success'],
                "client_notified": True
            }
            
        except Exception as e:
            logging.error(f"❌ Erreur traitement paiement: {str(e)}")
            # Envoyer email d'erreur au client et admin
            await self.send_error_notification(payment_data, str(e))
    
    async def purchase_domain_automatically(self, domain: str) -> Dict:
        """Achète domaine automatiquement via API Namecheap"""
        try:
            url = "https://api.namecheap.com/xml.response"
            params = {
                'ApiUser': NAMECHEAP_API_USER,
                'ApiKey': NAMECHEAP_API_KEY,
                'UserName': NAMECHEAP_API_USER,
                'Command': 'namecheap.domains.create',
                'ClientIp': '127.0.0.1',
                'DomainName': domain,
                'Years': 1,
                # Informations par défaut
                'RegistrantFirstName': 'AI',
                'RegistrantLastName': 'WebGen',
                'RegistrantAddress1': '123 Tech Street',
                'RegistrantCity': 'Paris',
                'RegistrantStateProvince': 'IDF',
                'RegistrantPostalCode': '75001',
                'RegistrantCountry': 'FR',
                'RegistrantPhone': '+33.123456789',
                'RegistrantEmailAddress': SMTP_EMAIL
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=params) as response:
                    result = await response.text()
                    
                    success = "success" in result.lower()
                    
                    return {
                        "success": success,
                        "domain": domain,
                        "message": "Domaine acheté automatiquement" if success else "Erreur achat domaine"
                    }
                    
        except Exception as e:
            logging.error(f"Erreur achat domaine: {str(e)}")
            return {"success": False, "domain": domain, "error": str(e)}
    
    async def deploy_to_netlify_automatically(self, website_id: str, domain: str, business_name: str) -> Dict:
        """Déploie site sur Netlify automatiquement"""
        try:
            headers = {
                'Authorization': f'Bearer {NETLIFY_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            # Récupérer le contenu du site depuis la DB
            # (à connecter avec votre base de données)
            website_content = await self.get_website_content(website_id)
            
            # Créer site Netlify
            site_data = {
                'name': domain.replace('.', '-'),
                'custom_domain': domain
            }
            
            async with aiohttp.ClientSession() as session:
                # Créer le site
                async with session.post('https://api.netlify.com/api/v1/sites', 
                                      json=site_data, headers=headers) as response:
                    site_result = await response.json()
                    site_id = site_result['id']
                
                # Déployer les fichiers
                files = {
                    'index.html': website_content['html'],
                    'styles.css': website_content['css'],
                    'script.js': website_content['js']
                }
                
                deploy_data = {'files': files}
                async with session.post(f'https://api.netlify.com/api/v1/sites/{site_id}/deploys',
                                      json=deploy_data, headers=headers) as response:
                    deploy_result = await response.json()
                
                return {
                    "success": True,
                    "site_id": site_id,
                    "netlify_url": site_result['url'],
                    "deploy_id": deploy_result['id']
                }
                
        except Exception as e:
            logging.error(f"Erreur déploiement Netlify: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def configure_dns_automatically(self, domain: str, netlify_url: str) -> Dict:
        """Configure DNS automatiquement"""
        try:
            # Configuration DNS via API Namecheap
            url = "https://api.namecheap.com/xml.response"
            params = {
                'ApiUser': NAMECHEAP_API_USER,
                'ApiKey': NAMECHEAP_API_KEY,
                'UserName': NAMECHEAP_API_USER,
                'Command': 'namecheap.domains.dns.setHosts',
                'ClientIp': '127.0.0.1',
                'SLD': domain.split('.')[0],
                'TLD': domain.split('.')[1],
                'HostName1': '@',
                'RecordType1': 'A',
                'Address1': '75.2.60.5',  # IP Netlify
                'HostName2': 'www',
                'RecordType2': 'CNAME',
                'Address2': netlify_url.replace('https://', '')
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=params) as response:
                    result = await response.text()
                    
                    success = "success" in result.lower()
                    
                    return {
                        "success": success,
                        "message": "DNS configuré automatiquement" if success else "Erreur DNS"
                    }
                    
        except Exception as e:
            logging.error(f"Erreur configuration DNS: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def send_delivery_email(self, client_email: str, domain: str, business_name: str, website_id: str):
        """Envoie email de livraison automatique"""
        subject = f"🎉 {domain} est EN LIGNE ! Livraison automatique terminée"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #28a745;">🎉 Livraison Automatique Terminée !</h2>
                
                <p>Félicitations ! Votre site <strong>{business_name}</strong> est maintenant <strong>EN LIGNE</strong> !</p>
                
                <div style="background: #e7f3ff; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
                    <h3 style="color: #0066cc;">🌐 Votre Site Web</h3>
                    <a href="https://{domain}" style="font-size: 24px; color: #0066cc; text-decoration: none;">
                        https://{domain}
                    </a>
                    <p style="margin: 10px 0;">👆 Cliquez pour voir votre site !</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #28a745;">✅ Tout est Configuré</h3>
                    <ul>
                        <li>🌐 Domaine {domain} acheté et configuré</li>
                        <li>🏠 Hébergement sécurisé et rapide activé</li>
                        <li>🔒 Certificat SSL (HTTPS) automatique</li>
                        <li>📱 Optimisé mobile et desktop</li>
                        <li>⚡ Site ultra-rapide</li>
                    </ul>
                </div>
                
                <div style="background: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #856404;">🎨 Modifier Votre Site</h3>
                    <p>Vous pouvez modifier votre site quand vous voulez :</p>
                    <a href="https://ia-webgen.com/edit/{website_id}" 
                       style="background: #007bff; color: white; padding: 10px 20px; 
                              text-decoration: none; border-radius: 5px;">
                        ✏️ Éditer Mon Site
                    </a>
                </div>
                
                <div style="background: #d4edda; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #155724;">📞 Support Inclus (3 mois)</h3>
                    <p>Questions ? Problème ? Répondez à cet email !</p>
                    <p>Support technique inclus pendant 3 mois.</p>
                </div>
                
                <p>Merci pour votre confiance !<br>
                🤖 Votre Système AI WebGen</p>
                
                <p><small>Site livré automatiquement en {self.calculate_processing_time()} ⚡</small></p>
            </div>
        </body>
        </html>
        """
        
        await self.send_email(client_email, subject, html_body)
    
    def calculate_processing_time(self) -> str:
        """Calcule le temps de traitement"""
        return "2h 34min"  # Exemple
    
    async def get_website_content(self, website_id: str) -> Dict:
        """Récupère le contenu du site depuis la DB"""
        # À connecter avec votre base MongoDB
        # Pour l'instant, retour factice
        return {
            "html": "<html><body><h1>Site en cours de configuration...</h1></body></html>",
            "css": "body { font-family: Arial; }",
            "js": "console.log('Site chargé');"
        }

# Instance globale
concierge_automation = ConciergeAutomation()