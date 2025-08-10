#!/usr/bin/env python3
"""
Simple test script for authentication flow
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def test_auth_flow():
    # Test phone number
    phone = "+919342044743"
    
    print("=== Testing Authentication Flow ===")
    
    # 1. Send OTP
    print("\n1. Sending OTP...")
    response = requests.post(
        f"{BASE_URL}/api/auth/send-otp",
        json={"phone_number": phone}
    )
    
    if response.status_code == 200:
        print("✅ OTP sent successfully")
        print(f"Response: {response.json()}")
    else:
        print(f"❌ Failed to send OTP: {response.status_code}")
        print(f"Error: {response.text}")
        return
    
    # 2. For testing purposes, we'll use a dummy OTP
    # In real scenario, you'd get this from SMS
    print("\n2. Testing with dummy OTP...")
    response = requests.post(
        f"{BASE_URL}/api/auth/verify-otp",
        json={"phone_number": phone, "otp": "123456"}
    )
    
    if response.status_code == 200:
        print("✅ OTP verification successful")
        print(f"Response: {response.json()}")
    else:
        print(f"❌ OTP verification failed: {response.status_code}")
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_auth_flow()
