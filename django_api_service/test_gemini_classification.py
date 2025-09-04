#!/usr/bin/env python3
"""
Test script to demonstrate Gemini AI classification for IT issues.
Run this after setting up your GEMINI_API_KEY environment variable.
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/Users/minasenel/Desktop/django_api_service')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

from issues.serializers import IssueSerializer

def test_classification():
    """Test various prompts to see how Gemini classifies them"""
    
    test_cases = [
        # Valid IT issues
        "My laptop keyboard is not working properly",
        "VPN keeps disconnecting every 10 minutes", 
        "Can't log into my work email account",
        "Printer is showing paper jam error",
        "WiFi connection is very slow",
        "Outlook crashes when I try to send large attachments",
        "My computer fan is making loud noise and running slowly",
        
        # Non-IT issues (should be rejected)
        "My faucet is broken and leaking water",
        "My car won't start in the morning",
        "Hello, how are you today?",
        "I need help with my garden",
        "The air conditioning in my office is too cold",
        "I want to book a vacation",
        
        # Edge cases
        "Computer issue",  # Too vague
        "My musluk is broken",  # Turkish for faucet
    ]
    
    print("Testing Gemini AI Classification for IT Issues")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{test_case}'")
        
        try:
            # Test classification
            is_valid = IssueSerializer.classify_with_gemini(test_case)
            print(f"   Classification: {'✅ VALID IT ISSUE' if is_valid else '❌ NOT IT ISSUE'}")
            
            if is_valid:
                # Test categorization
                category = IssueSerializer.categorize_with_gemini(test_case)
                print(f"   Category: {category}")
                
        except Exception as e:
            print(f"   Error: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    # Check if API key is set
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ GEMINI_API_KEY environment variable not set!")
        print("Please set your Gemini API key:")
        print("export GEMINI_API_KEY='your_api_key_here'")
        sys.exit(1)
    
    test_classification()
