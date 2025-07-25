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
            print("🎉 All tests passed! History system is working correctly.")
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