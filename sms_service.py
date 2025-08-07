# sms_service.py

from twilio.rest import Client
import os
import logging
from twilio.base.exceptions import TwilioRestException
from dotenv import load_dotenv # <-- 1. ADD THIS IMPORT

load_dotenv() # <-- 2. ADD THIS LINE TO LOAD THE .ENV FILE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SMSService:
    def __init__(self):
        # 3. REPLACE config() WITH os.getenv() FOR ALL THREE VARIABLES
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.client = Client(self.account_sid, self.auth_token)
    
    def send_otp(self, phone_number: str, otp: str) -> bool:
        """Send OTP via SMS using Twilio"""
        try:
            message_body = f"Your food delivery app verification code is: {otp}. Valid for 5 minutes. Do not share this code with anyone."
            
            message = self.client.messages.create(
                body=message_body,
                from_=self.twilio_phone_number,
                to=phone_number
            )
            
            logger.info(f"SMS sent successfully to {phone_number}. Message SID: {message.sid}")
            return True
            
        except TwilioRestException as e:
            logger.error(f"Failed to send SMS to {phone_number}: {str(e)}")
            return False
    
    def send_welcome_message(self, phone_number: str) -> bool:
        """Send welcome message after successful verification"""
        try:
            message_body = "Welcome to our Food Delivery App! Your phone number has been verified successfully. Enjoy ordering delicious food!"
            
            message = self.client.messages.create(
                body=message_body,
                from_=self.twilio_phone_number,
                to=phone_number
            )
            
            logger.info(f"Welcome SMS sent to {phone_number}. Message SID: {message.sid}")
            return True
            
        except TwilioRestException as e:
            logger.error(f"Failed to send welcome SMS to {phone_number}: {str(e)}")
            return False

# Create a global instance
sms_service = SMSService()