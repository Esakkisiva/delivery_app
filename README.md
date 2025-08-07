# Food Delivery App - Login API

A FastAPI-based authentication system with phone number verification using SMS OTP for a food delivery application.

## Features

- 📱 Phone number-based authentication
- 🔐 Secure OTP generation and hashing
- 📨 SMS delivery via Twilio
- 🔑 JWT token-based session management
- 🗄️ MySQL database integration
- ✅ Phone number validation
- 🔄 OTP resend functionality

## Tech Stack

- **Backend**: FastAPI
- **Database**: MySQL with SQLAlchemy ORM
- **SMS Service**: Twilio
- **Authentication**: JWT tokens
- **Password Hashing**: bcrypt
- **Environment Management**: python-decouple

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Database Setup

Create a MySQL database and update the `.env` file with your database credentials:

```sql
CREATE DATABASE delivery_app;
```

### 3. Environment Configuration

Update the `.env` file with your actual credentials:

```env
# Database Configuration
DATABASE_URL=mysql+pymysql://your_username:your_password@localhost:3306/delivery_app

# Twilio SMS Configuration (Get from https://console.twilio.com/)
TWILIO_ACCOUNT_SID=your_actual_twilio_account_sid
TWILIO_AUTH_TOKEN=your_actual_twilio_auth_token
TWILIO_PHONE_NUMBER=your_actual_twilio_phone_number

# JWT Configuration
SECRET_KEY=your_super_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OTP Configuration
OTP_EXPIRE_MINUTES=5
```

### 4. Run the Application

```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### 1. Initiate Login (Send OTP)
```http
POST /auth/login
Content-Type: application/json

{
    "phone_number": "+1234567890"
}
```

### 2. Verify OTP
```http
POST /auth/verify-otp
Content-Type: application/json

{
    "phone_number": "+1234567890",
    "otp": "123456"
}
```

### 3. Resend OTP
```http
POST /auth/resend-otp
Content-Type: application/json

{
    "phone_number": "+1234567890"
}
```

### 4. Get Current User
```http
GET /auth/me
Authorization: Bearer <your_jwt_token>
```

## Security Features

1. **OTP Hashing**: All OTPs are hashed using bcrypt before storage
2. **OTP Expiration**: OTPs expire after 5 minutes
3. **Single Use**: OTPs can only be used once
4. **JWT Tokens**: Secure session management with JWT
5. **Phone Validation**: Comprehensive phone number format validation

## Database Schema

### Users Table
- `id`: Primary key
- `phone_number`: Unique phone number
- `is_verified`: Verification status
- `created_at`: Account creation timestamp
- `updated_at`: Last update timestamp

### OTPs Table
- `id`: Primary key
- `phone_number`: Associated phone number
- `hashed_otp`: Bcrypt hashed OTP
- `created_at`: OTP generation timestamp
- `expires_at`: OTP expiration timestamp
- `is_used`: Usage status

## Testing the API

You can test the API using the interactive documentation at `http://localhost:8000/docs` or use curl:

```bash
# 1. Request OTP
curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"phone_number": "+1234567890"}'

# 2. Verify OTP (replace 123456 with actual OTP received)
curl -X POST "http://localhost:8000/auth/verify-otp" \
     -H "Content-Type: application/json" \
     -d '{"phone_number": "+1234567890", "otp": "123456"}'
```

## Error Handling

The API includes comprehensive error handling for:
- Invalid phone number formats
- Expired OTPs
- Invalid OTPs
- SMS delivery failures
- Database connection issues
- Authentication errors

## Production Considerations

1. **Environment Variables**: Ensure all sensitive data is in environment variables
2. **Database Security**: Use proper database credentials and connection pooling
3. **Rate Limiting**: Implement rate limiting for OTP requests
4. **Logging**: Add comprehensive logging for monitoring
5. **SSL/TLS**: Use HTTPS in production
6. **SMS Costs**: Monitor Twilio usage to control SMS costs
