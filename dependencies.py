# /home/asus/projects/delivery-management/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# Import our own modules
from database import get_db
import models.auth_models as models
import security
from security import TokenData

# This is the same scheme we defined in the router before
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/verify-otp")

def get_current_active_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> models.User:
    """
    Decodes the JWT access token, gets the user ID, and returns the full User object from the database.
    This function will be the single source for protecting our endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = security.verify_token(token, credentials_exception)
    user = db.query(models.User).filter(models.User.id == int(token_data.id)).first()
    if user is None:
        raise credentials_exception
    if not user.is_verified:
        raise HTTPException(status_code=400, detail="User is not verified")
    return user