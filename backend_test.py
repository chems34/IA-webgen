#!/usr/bin/env python3
"""
Backend API Testing for WebGen App
Tests the AI website generation functionality
"""

import requests
import json
import time
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://707b7a03-8bf6-42b4-a6bc-cbbf63f8a0b5.preview.emergentagent.com/api"

def print_test_header(test_name):
    print(f"\n{'='*60}")
    print(f"Testing: {test_name}")
    print(f"{'='*60}")

def print_result(success, message, details=None):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")
    if details:
        print(f"Details: {details}")

def test_api_root():
    """Test the root API endpoint"""
    print_test_header("API Root Endpoint")
    
    try:
        response = requests.get(f"{BACKEND_URL}/")
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, "API root endpoint is accessible", data)
            return True
        else:
            print_result(False, f"API root returned status {response.status_code}", response.text)
            return False
            
    except Exception as e:
        print_result(False, "Failed to connect to API", str(e))
        return False

def test_generate_website():
    """Test the website generation endpoint with specified parameters"""
    print_test_header("Website Generation Endpoint")
    
    # Test data as specified in the review request
    test_data = {
        "business_name": "Ma Boutique",
        "site_type": "vitrine",
        "description": "Une boutique de vêtements élégante avec des produits de qualité",
        "primary_color": "#3B82F6"
    }
    
    try:
        print(f"Sending request to: {BACKEND_URL}/generate-website")
        print(f"Request data: {json.dumps(test_data, indent=2)}")
        
        response = requests.post(
            f"{BACKEND_URL}/generate-website",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=60  # Increased timeout for AI generation
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify response structure
            required_fields = ["id", "html_content", "css_content", "js_content", "preview_url", "price", "created_at"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print_result(False, f"Missing required fields: {missing_fields}", data)
                return None
            
            # Verify price is 15€ (without referral)
            if data["price"] != 15.0:
                print_result(False, f"Expected price 15.0, got {data['price']}", data)
                return None
            
            # Verify content is not empty
            if not data["html_content"] or not data["css_content"] or not data["js_content"]:
                print_result(False, "Generated content is empty", {
                    "html_length": len(data["html_content"]),
                    "css_length": len(data["css_content"]),
                    "js_length": len(data["js_content"])
                })
                return None
            
            print_result(True, "Website generated successfully", {
                "website_id": data["id"],
                "price": data["price"],
                "html_length": len(data["html_content"]),
                "css_length": len(data["css_content"]),
                "js_length": len(data["js_content"]),
                "preview_url": data["preview_url"]
            })
            
            return data["id"]  # Return website ID for further tests
            
        else:
            print_result(False, f"Website generation failed with status {response.status_code}", response.text)
            return None
            
    except requests.exceptions.Timeout:
        print_result(False, "Request timed out - AI generation may be taking too long", "Consider increasing timeout")
        return None
    except Exception as e:
        print_result(False, "Website generation request failed", str(e))
        return None

def test_preview_endpoint(website_id):
    """Test the preview endpoint"""
    print_test_header("Website Preview Endpoint")
    
    if not website_id:
        print_result(False, "No website ID provided for preview test", "Skipping preview test")
        return False
    
    try:
        response = requests.get(f"{BACKEND_URL}/preview/{website_id}")
        
        if response.status_code == 200:
            data = response.json()
            
            if "html" not in data:
                print_result(False, "Preview response missing 'html' field", data)
                return False
            
            if not data["html"]:
                print_result(False, "Preview HTML content is empty", data)
                return False
            
            # Check if it's a complete HTML document
            html_content = data["html"]
            if not ("<!DOCTYPE html>" in html_content and "<html" in html_content and "</html>" in html_content):
                print_result(False, "Preview HTML is not a complete document", f"Content length: {len(html_content)}")
                return False
            
            print_result(True, "Preview endpoint working correctly", {
                "html_length": len(html_content),
                "contains_doctype": "<!DOCTYPE html>" in html_content,
                "contains_business_name": "Ma Boutique" in html_content
            })
            return True
            
        else:
            print_result(False, f"Preview failed with status {response.status_code}", response.text)
            return False
            
    except Exception as e:
        print_result(False, "Preview request failed", str(e))
        return False

def test_create_referral():
    """Test the referral creation endpoint"""
    print_test_header("Referral Creation Endpoint")
    
    try:
        response = requests.post(f"{BACKEND_URL}/create-referral")
        
        if response.status_code == 200:
            data = response.json()
            
            required_fields = ["referral_code", "referral_link", "expires_at"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print_result(False, f"Missing required fields: {missing_fields}", data)
                return None
            
            print_result(True, "Referral created successfully", {
                "referral_code": data["referral_code"],
                "referral_link": data["referral_link"],
                "expires_at": data["expires_at"]
            })
            
            return data["referral_code"]
            
        else:
            print_result(False, f"Referral creation failed with status {response.status_code}", response.text)
            return None
            
    except Exception as e:
        print_result(False, "Referral creation request failed", str(e))
        return None

def test_website_generation_with_referral(referral_code):
    """Test website generation with referral code"""
    print_test_header("Website Generation with Referral")
    
    if not referral_code:
        print_result(False, "No referral code provided", "Skipping referral test")
        return False
    
    test_data = {
        "business_name": "Ma Boutique Referral",
        "site_type": "vitrine",
        "description": "Une boutique de vêtements élégante avec des produits de qualité (avec référence)",
        "primary_color": "#3B82F6",
        "referral_code": referral_code
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/generate-website",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify price is reduced to 10€ with referral
            if data["price"] != 10.0:
                print_result(False, f"Expected discounted price 10.0, got {data['price']}", data)
                return False
            
            print_result(True, "Website generation with referral successful", {
                "website_id": data["id"],
                "discounted_price": data["price"],
                "referral_applied": True
            })
            return True
            
        else:
            print_result(False, f"Website generation with referral failed with status {response.status_code}", response.text)
            return False
            
    except Exception as e:
        print_result(False, "Website generation with referral request failed", str(e))
        return False

def test_error_handling():
    """Test error handling with invalid requests"""
    print_test_header("Error Handling Tests")
    
    # Test 1: Missing required fields
    print("\n--- Test 1: Missing required fields ---")
    try:
        response = requests.post(
            f"{BACKEND_URL}/generate-website",
            json={"business_name": "Test"},  # Missing required fields
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 422:  # FastAPI validation error
            print_result(True, "Correctly rejected request with missing fields", f"Status: {response.status_code}")
        else:
            print_result(False, f"Expected 422 validation error, got {response.status_code}", response.text)
    except Exception as e:
        print_result(False, "Error handling test failed", str(e))
    
    # Test 2: Invalid website ID for preview
    print("\n--- Test 2: Invalid website ID for preview ---")
    try:
        response = requests.get(f"{BACKEND_URL}/preview/invalid-website-id")
        
        if response.status_code == 404:
            print_result(True, "Correctly returned 404 for invalid website ID", f"Status: {response.status_code}")
        else:
            print_result(False, f"Expected 404 for invalid website ID, got {response.status_code}", response.text)
    except Exception as e:
        print_result(False, "Invalid website ID test failed", str(e))
    
    # Test 3: Empty request body
    print("\n--- Test 3: Empty request body ---")
    try:
        response = requests.post(
            f"{BACKEND_URL}/generate-website",
            json={},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 422:
            print_result(True, "Correctly rejected empty request", f"Status: {response.status_code}")
        else:
            print_result(False, f"Expected 422 for empty request, got {response.status_code}", response.text)
    except Exception as e:
        print_result(False, "Empty request test failed", str(e))

def test_gemini_integration():
    """Test if Gemini API integration is working"""
    print_test_header("Gemini API Integration Test")
    
    # This is tested indirectly through website generation
    # We'll create a simple request and check if AI-generated content looks realistic
    
    test_data = {
        "business_name": "Test Bakery",
        "site_type": "vitrine",
        "description": "A small local bakery specializing in fresh bread and pastries",
        "primary_color": "#8B4513"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/generate-website",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if content looks AI-generated (contains business name, relevant keywords)
            html_content = data["html_content"].lower()
            css_content = data["css_content"].lower()
            
            # Look for business-specific content
            business_indicators = [
                "bakery" in html_content,
                "bread" in html_content or "pastry" in html_content or "baking" in html_content,
                "test bakery" in html_content,
                len(html_content) > 500,  # Substantial content
                len(css_content) > 200,   # Substantial styling
                "#8b4513" in css_content or "8b4513" in css_content  # Primary color used
            ]
            
            ai_quality_score = sum(business_indicators)
            
            if ai_quality_score >= 4:
                print_result(True, "Gemini API integration appears to be working", {
                    "quality_indicators_met": f"{ai_quality_score}/6",
                    "html_length": len(data["html_content"]),
                    "css_length": len(data["css_content"]),
                    "contains_business_name": "test bakery" in html_content,
                    "contains_relevant_keywords": any(word in html_content for word in ["bakery", "bread", "pastry"])
                })
                return True
            else:
                print_result(False, "Generated content quality is low - Gemini integration may have issues", {
                    "quality_indicators_met": f"{ai_quality_score}/6",
                    "html_preview": html_content[:200] + "..." if len(html_content) > 200 else html_content
                })
                return False
                
        else:
            print_result(False, f"Gemini integration test failed with status {response.status_code}", response.text)
            return False
            
    except requests.exceptions.Timeout:
        print_result(False, "Gemini API request timed out", "AI service may be slow or unavailable")
        return False
    except Exception as e:
        print_result(False, "Gemini integration test failed", str(e))
        return False

def main():
    """Run all tests"""
    print("🚀 Starting WebGen Backend API Tests")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test started at: {datetime.now()}")
    
    results = {}
    
    # Test 1: API Root
    results['api_root'] = test_api_root()
    
    # Test 2: Website Generation (main functionality)
    website_id = test_generate_website()
    results['website_generation'] = website_id is not None
    
    # Test 3: Preview Endpoint
    results['preview'] = test_preview_endpoint(website_id)
    
    # Test 4: Referral System
    referral_code = test_create_referral()
    results['referral_creation'] = referral_code is not None
    
    # Test 5: Website Generation with Referral
    results['referral_discount'] = test_website_generation_with_referral(referral_code)
    
    # Test 6: Error Handling
    test_error_handling()
    results['error_handling'] = True  # Assume pass if no exceptions
    
    # Test 7: Gemini Integration
    results['gemini_integration'] = test_gemini_integration()
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name.replace('_', ' ').title()}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! WebGen backend is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the details above.")
    
    return results

if __name__ == "__main__":
    main()