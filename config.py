# /home/asus/projects/delivery-management/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # This will load variables from the .env file.
    # The variable names must match exactly (case-insensitive).
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    DATABASE_URL: str
    
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    OTP_EXPIRE_MINUTES: int

# Create a single instance that the rest of your app can import
settings = Settings()