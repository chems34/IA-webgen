#!/usr/bin/env python3
"""
Backend API Test Suite for AI WebGen History System
Tests all history APIs and core functionality
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any

class AIWebGenTester:
    def __init__(self, base_url="https://4050c07e-4f45-4312-9f54-7a61029439f8.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_data = {}

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")

    def make_request(self, method: str, endpoint: str, data: Dict[Any, Any] = None, params: Dict[str, Any] = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, params=params, timeout=30)
            else:
                return False, {}, 0
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            return response.status_code < 400, response_data, response.status_code
            
        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}, 0

    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, data, status = self.make_request('GET', '/')
        expected_message = "Website Generator API is running!"
        
        if success and data.get('message') == expected_message:
            self.log_test("Root API Endpoint", True, f"Status: {status}")
        else:
            self.log_test("Root API Endpoint", False, f"Status: {status}, Data: {data}")

    def test_templates_endpoint(self):
        """Test templates endpoint"""
        success, data, status = self.make_request('GET', '/templates')
        
        if success and 'templates' in data and len(data['templates']) > 0:
            self.log_test("Templates Endpoint", True, f"Found {len(data['templates'])} templates")
            self.test_data['templates'] = data['templates']
        else:
            self.log_test("Templates Endpoint", False, f"Status: {status}, Data: {data}")

    def test_create_referral(self):
        """Test referral creation"""
        success, data, status = self.make_request('POST', '/create-referral')
        
        if success and 'referral_code' in data and 'referral_link' in data:
            self.log_test("Create Referral", True, f"Code: {data['referral_code']}")
            self.test_data['referral_code'] = data['referral_code']
        else:
            self.log_test("Create Referral", False, f"Status: {status}, Data: {data}")

    def test_generate_from_template(self):
        """Test website generation from template"""
        if not self.test_data.get('templates'):
            self.log_test("Generate from Template", False, "No templates available")
            return
        
        template_key = self.test_data['templates'][0]['key']
        request_data = {
            "template_key": template_key,
            "business_name": "Test Restaurant",
            "primary_color": "#FF5722",
            "referral_code": self.test_data.get('referral_code')
        }
        
        success, data, status = self.make_request('POST', '/generate-from-template', request_data)
        
        if success and 'id' in data and 'html_content' in data:
            self.log_test("Generate from Template", True, f"Website ID: {data['id']}")
            self.test_data['website_id'] = data['id']
            self.test_data['website_price'] = data.get('price', 15.0)
        else:
            self.log_test("Generate from Template", False, f"Status: {status}, Data: {data}")

    def test_preview_website(self):
        """Test website preview"""
        if not self.test_data.get('website_id'):
            self.log_test("Preview Website", False, "No website ID available")
            return
        
        success, data, status = self.make_request('GET', f'/preview/{self.test_data["website_id"]}')
        
        if success and 'html' in data and len(data['html']) > 100:
            self.log_test("Preview Website", True, f"HTML length: {len(data['html'])}")
        else:
            self.log_test("Preview Website", False, f"Status: {status}, Data: {data}")

    def test_create_payment(self):
        """Test payment creation"""
        if not self.test_data.get('website_id'):
            self.log_test("Create Payment", False, "No website ID available")
            return
        
        request_data = {
            "website_id": self.test_data['website_id'],
            "referral_code": self.test_data.get('referral_code')
        }
        
        success, data, status = self.make_request('POST', '/paypal/create-payment-url', request_data)
        
        if success and 'payment_url' in data and 'amount' in data:
            self.log_test("Create Payment", True, f"Amount: {data['amount']}€")
            self.test_data['payment_url'] = data['payment_url']
        else:
            self.log_test("Create Payment", False, f"Status: {status}, Data: {data}")

    def test_history_endpoints(self):
        """Test all history-related endpoints"""
        
        # Test get all history
        success, data, status = self.make_request('GET', '/history', params={'limit': 10, 'skip': 0})
        if success and 'history' in data and 'total' in data:
            self.log_test("Get All History", True, f"Total entries: {data['total']}, Retrieved: {len(data['history'])}")
            self.test_data['history_entries'] = data['history']
        else:
            self.log_test("Get All History", False, f"Status: {status}, Data: {data}")

        # Test history stats
        success, data, status = self.make_request('GET', '/history/stats')
        if success and 'total_activities' in data and 'action_counts' in data:
            self.log_test("History Stats", True, f"Total activities: {data['total_activities']}")
            self.test_data['history_stats'] = data
        else:
            self.log_test("History Stats", False, f"Status: {status}, Data: {data}")

        # Test user history (if we have entries)
        if self.test_data.get('history_entries') and len(self.test_data['history_entries']) > 0:
            user_session = self.test_data['history_entries'][0].get('user_session')
            if user_session:
                success, data, status = self.make_request('GET', f'/history/user/{user_session}')
                if success and 'history' in data and 'user_session' in data:
                    self.log_test("Get User History", True, f"User: {user_session[:8]}..., Entries: {len(data['history'])}")
                else:
                    self.log_test("Get User History", False, f"Status: {status}, Data: {data}")
            else:
                self.log_test("Get User History", False, "No user_session found in history entries")
        else:
            self.log_test("Get User History", False, "No history entries available for testing")

    def test_admin_endpoints(self):
        """Test admin endpoints"""
        
        # Test admin stats
        success, data, status = self.make_request('GET', '/admin/stats')
        if success and 'total_websites' in data and 'total_revenue' in data:
            self.log_test("Admin Stats", True, f"Websites: {data['total_websites']}, Revenue: {data['total_revenue']}€")
        else:
            self.log_test("Admin Stats", False, f"Status: {status}, Data: {data}")

        # Test admin websites
        success, data, status = self.make_request('GET', '/admin/websites', params={'limit': 5, 'skip': 0})
        if success and 'websites' in data:
            self.log_test("Admin Websites", True, f"Retrieved: {len(data['websites'])} websites")
        else:
            self.log_test("Admin Websites", False, f"Status: {status}, Data: {data}")

    def test_history_cleanup(self):
        """Test history cleanup (careful with this one)"""
        # Only test with a very high days_old value to avoid deleting real data
        success, data, status = self.make_request('DELETE', '/history/cleanup', params={'days_old': 365})
        if success and 'deleted_count' in data:
            self.log_test("History Cleanup", True, f"Deleted: {data['deleted_count']} entries")
        else:
            self.log_test("History Cleanup", False, f"Status: {status}, Data: {data}")

    def test_concierge_service(self):
        """Test the new concierge hosting service"""
        print("\n🤝 Testing Concierge Service...")
        
        # We need a website ID to test with
        if not self.test_data.get('website_id'):
            self.test_generate_from_template()
        
        website_id = self.test_data.get('website_id')
        if not website_id:
            self.log_test("Concierge Service Setup", False, "No website ID available")
            return
        
        # Test concierge service request
        request_data = {
            "website_id": website_id,
            "contact_email": "test@example.com", 
            "preferred_domain": "mon-site-test.com"
        }
        
        # Make request using query parameters (as per the API signature)
        url = f"{self.api_url}/request-concierge-service"
        try:
            response = requests.post(url, params=request_data, timeout=30)
            success = response.status_code < 400
            try:
                data = response.json()
            except:
                data = {"raw_response": response.text}
            status = response.status_code
        except requests.exceptions.RequestException as e:
            success, data, status = False, {"error": str(e)}, 0
        
        if success and 'request_id' in data and data.get('price') == 49.0:
            self.log_test("Concierge Service Request", True, f"Request ID: {data['request_id']}, Price: {data['price']}€")
            self.test_data['concierge_request_id'] = data['request_id']
            
            # Verify the response includes expected fields
            expected_fields = ['message', 'status', 'next_steps', 'includes']
            missing_fields = [field for field in expected_fields if field not in data]
            if not missing_fields:
                self.log_test("Concierge Service Response Fields", True, "All expected fields present")
            else:
                self.log_test("Concierge Service Response Fields", False, f"Missing fields: {missing_fields}")
        else:
            self.log_test("Concierge Service Request", False, f"Status: {status}, Data: {data}")

    def test_hosting_guide_download(self):
        """Test the hosting guide download"""
        print("\n📚 Testing Hosting Guide Download...")
        
        # Test the hosting guide download endpoint
        url = f"{self.api_url}/download-hosting-guide"
        try:
            response = requests.get(url, timeout=30)
            success = response.status_code == 200
            
            if success:
                # Check if it's a file download
                content_type = response.headers.get('content-type', '')
                content_disposition = response.headers.get('content-disposition', '')
                
                if 'text/markdown' in content_type or 'Guide-Hebergement' in content_disposition:
                    self.log_test("Hosting Guide Download", True, f"Guide downloaded, size: {len(response.content)} bytes")
                    
                    # Check if content looks like markdown
                    content_preview = response.text[:200] if hasattr(response, 'text') else str(response.content[:200])
                    if '#' in content_preview or 'hébergement' in content_preview.lower():
                        self.log_test("Hosting Guide Content", True, "Content appears to be valid markdown guide")
                    else:
                        self.log_test("Hosting Guide Content", False, f"Content doesn't look like guide: {content_preview}")
                else:
                    self.log_test("Hosting Guide Download", False, f"Unexpected content type: {content_type}")
            else:
                self.log_test("Hosting Guide Download", False, f"Status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.log_test("Hosting Guide Download", False, f"Request failed: {str(e)}")

    def test_download_website(self):
        """Test website download functionality"""
        print("\n📥 Testing Website Download...")
        
        # We need a paid website to test download
        if not self.test_data.get('paid_website_id'):
            # Create and mark a website as paid
            if not self.test_data.get('website_id'):
                self.test_generate_from_template()
            
            website_id = self.test_data.get('website_id')
            if website_id:
                success, data, status = self.make_request('POST', f'/test/mark-paid/{website_id}')
                if success:
                    self.test_data['paid_website_id'] = website_id
        
        paid_website_id = self.test_data.get('paid_website_id')
        if not paid_website_id:
            self.log_test("Website Download Setup", False, "No paid website available")
            return
        
        # Test download
        url = f"{self.api_url}/download/{paid_website_id}"
        try:
            response = requests.get(url, timeout=30)
            success = response.status_code == 200
            
            if success:
                content_type = response.headers.get('content-type', '')
                if 'application/zip' in content_type:
                    self.log_test("Website Download", True, f"ZIP file downloaded, size: {len(response.content)} bytes")
                else:
                    self.log_test("Website Download", False, f"Unexpected content type: {content_type}")
            else:
                self.log_test("Website Download", False, f"Status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.log_test("Website Download", False, f"Request failed: {str(e)}")

    def test_new_hosting_features_integration(self):
        """Test the complete hosting workflow integration"""
        print("\n🌐 Testing Complete Hosting Workflow...")
        
        # Step 1: Generate website
        if not self.test_data.get('website_id'):
            self.test_generate_from_template()
        
        website_id = self.test_data.get('website_id')
        if not website_id:
            self.log_test("Hosting Workflow - Website Generation", False, "Could not generate website")
            return
        
        # Step 2: Mark as paid (simulate payment)
        success, data, status = self.make_request('POST', f'/test/mark-paid/{website_id}')
        if not success:
            self.log_test("Hosting Workflow - Payment", False, f"Could not mark as paid: {status}")
            return
        
        # Step 3: Download website
        url = f"{self.api_url}/download/{website_id}"
        try:
            response = requests.get(url, timeout=30)
            download_success = response.status_code == 200
        except:
            download_success = False
        
        if not download_success:
            self.log_test("Hosting Workflow - Download", False, "Could not download website")
            return
        
        # Step 4: Test concierge service request
        concierge_data = {
            "website_id": website_id,
            "contact_email": "workflow-test@example.com",
            "preferred_domain": "workflow-test.com"
        }
        
        url = f"{self.api_url}/request-concierge-service"
        try:
            response = requests.post(url, params=concierge_data, timeout=30)
            concierge_success = response.status_code < 400
        except:
            concierge_success = False
        
        # Step 5: Test guide download
        url = f"{self.api_url}/download-hosting-guide"
        try:
            response = requests.get(url, timeout=30)
            guide_success = response.status_code == 200
        except:
            guide_success = False
        
        # Evaluate complete workflow
        if download_success and concierge_success and guide_success:
            self.log_test("Complete Hosting Workflow", True, "All hosting features working together")
        else:
            failures = []
            if not download_success: failures.append("download")
            if not concierge_success: failures.append("concierge")
            if not guide_success: failures.append("guide")
            self.log_test("Complete Hosting Workflow", False, f"Failed components: {', '.join(failures)}")

    def test_editing_endpoints(self):
        """Test the new website editing functionality"""
        print("\n🎨 Testing Website Editing System...")
        
        # First, we need a website to test with
        if not self.test_data.get('website_id'):
            # Create a test website first
            self.test_generate_from_template()
        
        website_id = self.test_data.get('website_id')
        if not website_id:
            self.log_test("Website Editing Setup", False, "No website ID available for editing tests")
            return
        
        # Test 1: Try to access editing for unpaid website (should fail)
        success, data, status = self.make_request('GET', f'/edit/{website_id}')
        if not success and status == 403:
            self.log_test("Edit Unpaid Website (Expected Failure)", True, f"Correctly blocked with status {status}")
        else:
            self.log_test("Edit Unpaid Website (Expected Failure)", False, f"Should have failed with 403, got {status}")
        
        # Test 2: Mark website as paid using test endpoint
        success, data, status = self.make_request('POST', f'/test/mark-paid/{website_id}')
        if success and data.get('editable') == True:
            self.log_test("Mark Website as Paid", True, f"Website {website_id} marked as paid")
            self.test_data['paid_website_id'] = website_id
        else:
            self.log_test("Mark Website as Paid", False, f"Status: {status}, Data: {data}")
            return
        
        # Test 3: Now try to access editing for paid website (should succeed)
        success, data, status = self.make_request('GET', f'/edit/{website_id}')
        if success and data.get('editable') == True and 'html_content' in data:
            self.log_test("Get Website for Editing", True, f"Retrieved editable website data")
            self.test_data['original_html'] = data['html_content']
            self.test_data['original_css'] = data['css_content']
        else:
            self.log_test("Get Website for Editing", False, f"Status: {status}, Data: {data}")
            return
        
        # Test 4: Save changes to the website
        changes = {
            "business_name": "Mon Site Test Modifié",
            "primary_color": "#E74C3C",
            "html_content": "<div><h1>Mon Site Test Modifié</h1><p>Site modifié avec succès!</p></div>",
            "css_content": "body{font-family:Arial;background:#f0f0f0;color:#E74C3C;}"
        }
        
        success, data, status = self.make_request('PUT', f'/edit/{website_id}', changes)
        if success and 'message' in data and data.get('website_id') == website_id:
            self.log_test("Save Website Changes", True, f"Changes saved successfully")
        else:
            self.log_test("Save Website Changes", False, f"Status: {status}, Data: {data}")
        
        # Test 5: Verify changes were saved by getting the website again
        success, data, status = self.make_request('GET', f'/edit/{website_id}')
        if success and data.get('business_name') == "Mon Site Test Modifié" and data.get('primary_color') == "#E74C3C":
            self.log_test("Verify Saved Changes", True, f"Changes persisted correctly")
        else:
            self.log_test("Verify Saved Changes", False, f"Changes not persisted correctly")
        
        # Test 6: Test with the specific test data provided
        test_website_id = "63d691e0-dcc3-44d5-8cc6-f1d9c08fca2b"
        
        # Mark the test website as paid
        success, data, status = self.make_request('POST', f'/test/mark-paid/{test_website_id}')
        if success:
            self.log_test("Mark Test Website as Paid", True, f"Test website {test_website_id} marked as paid")
            
            # Try to access it for editing
            success, data, status = self.make_request('GET', f'/edit/{test_website_id}')
            if success and data.get('editable') == True:
                self.log_test("Access Test Website for Editing", True, f"Test website accessible for editing")
            else:
                self.log_test("Access Test Website for Editing", False, f"Status: {status}, Data: {data}")
        else:
            self.log_test("Mark Test Website as Paid", False, f"Could not mark test website as paid: {status}")

    def test_specific_test_case(self):
        """Test the specific scenario mentioned in the request"""
        print("\n🎯 Testing Specific Test Case...")
        
        # Test data from the request
        test_website_id = "63d691e0-dcc3-44d5-8cc6-f1d9c08fca2b"
        test_business_name = "Mon Site Test"
        test_color = "#E74C3C"
        
        # Step 1: Generate a website with template "simple"
        request_data = {
            "template_key": "simple",
            "business_name": test_business_name,
            "primary_color": test_color
        }
        
        success, data, status = self.make_request('POST', '/generate-from-template', request_data)
        if success and 'id' in data:
            generated_id = data['id']
            self.log_test("Generate Test Website", True, f"Generated website: {generated_id}")
            
            # Step 2: Mark as paid
            success, data, status = self.make_request('POST', f'/test/mark-paid/{generated_id}')
            if success:
                self.log_test("Mark Generated Website as Paid", True, f"Website marked as paid")
                
                # Step 3: Access editor
                success, data, status = self.make_request('GET', f'/edit/{generated_id}')
                if success and data.get('editable') == True:
                    self.log_test("Access Editor for Generated Website", True, f"Editor accessible")
                    
                    # Step 4: Test modifications
                    modifications = {
                        "business_name": test_business_name,
                        "primary_color": test_color,
                        "html_content": f"<div><h1>{test_business_name}</h1><p>Site web modifié avec l'éditeur!</p><section><h2>Contact</h2><p>Contactez-nous!</p></section></div>"
                    }
                    
                    success, data, status = self.make_request('PUT', f'/edit/{generated_id}', modifications)
                    if success:
                        self.log_test("Test Modifications", True, f"Modifications saved successfully")
                    else:
                        self.log_test("Test Modifications", False, f"Failed to save modifications: {status}")
                else:
                    self.log_test("Access Editor for Generated Website", False, f"Editor not accessible: {status}")
            else:
                self.log_test("Mark Generated Website as Paid", False, f"Failed to mark as paid: {status}")
        else:
            self.log_test("Generate Test Website", False, f"Failed to generate website: {status}")

    def verify_history_logging(self):
        """Verify that actions are being logged in history"""
        print("\n🔍 Verifying History Logging...")
        
        # Get current history count
        success, data, status = self.make_request('GET', '/history/stats')
        if not success:
            self.log_test("History Logging Verification", False, "Could not get initial stats")
            return
        
        initial_count = data.get('total_activities', 0)
        print(f"📊 Initial history count: {initial_count}")
        
        # Perform an action that should be logged (create referral)
        success, data, status = self.make_request('POST', '/create-referral')
        if not success:
            self.log_test("History Logging Verification", False, "Could not create referral for logging test")
            return
        
        # Check if history count increased
        success, data, status = self.make_request('GET', '/history/stats')
        if success:
            new_count = data.get('total_activities', 0)
            if new_count > initial_count:
                self.log_test("History Logging Verification", True, f"Count increased from {initial_count} to {new_count}")
            else:
                self.log_test("History Logging Verification", False, f"Count did not increase: {initial_count} -> {new_count}")
        else:
            self.log_test("History Logging Verification", False, "Could not get updated stats")

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting AI WebGen Backend Tests...")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Basic API tests
        print("\n📡 Testing Basic API Endpoints...")
        self.test_root_endpoint()
        self.test_templates_endpoint()
        
        # Referral and website generation
        print("\n🎁 Testing Referral System...")
        self.test_create_referral()
        
        print("\n🌐 Testing Website Generation...")
        self.test_generate_from_template()
        self.test_preview_website()
        self.test_create_payment()
        
        # NEW: Website editing tests
        print("\n🎨 Testing Website Editing System...")
        self.test_editing_endpoints()
        self.test_specific_test_case()
        
        # History system tests
        print("\n📜 Testing History System...")
        self.test_history_endpoints()
        
        # Admin endpoints
        print("\n👑 Testing Admin Endpoints...")
        self.test_admin_endpoints()
        
        # History logging verification
        self.verify_history_logging()
        
        # Cleanup test (be careful)
        print("\n🗑️ Testing History Cleanup...")
        self.test_history_cleanup()
        
        # Final results
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed! Website editing system is working correctly.")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed. Check the issues above.")
            return 1

def main():
    """Main test runner"""
    tester = AIWebGenTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())