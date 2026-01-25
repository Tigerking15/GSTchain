"""
Authentication module for GSTchain
Handles user registration and login for business users and auditors
Uses MongoDB Atlas for user storage and JWT for session management
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import os
import bcrypt
from jose import jwt, JWTError
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from dotenv import load_dotenv

load_dotenv()

# --------------------------------------------------
# MongoDB Connection
# --------------------------------------------------
MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI)
db = client.gstchain

# Collections
business_users = db.business_users
auditors = db.auditors

# Create unique indexes for email
business_users.create_index("email", unique=True)
auditors.create_index("email", unique=True)

# --------------------------------------------------
# JWT Configuration
# --------------------------------------------------
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_secret_key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

security = HTTPBearer()

# --------------------------------------------------
# Pydantic Models
# --------------------------------------------------

class BusinessUserRegister(BaseModel):
    email: EmailStr
    password: str
    company_name: str
    gstin: str
    phone: Optional[str] = None

class AuditorRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    license_number: str
    organization: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_type: str
    user_email: str
    user_name: str

# --------------------------------------------------
# Helper Functions
# --------------------------------------------------

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    payload = decode_token(token)
    return payload

# --------------------------------------------------
# Router
# --------------------------------------------------
router = APIRouter(prefix="/auth", tags=["Authentication"])

# --------------------------------------------------
# Business User Endpoints
# --------------------------------------------------

@router.post("/register/business", response_model=TokenResponse)
def register_business(user: BusinessUserRegister):
    """Register a new business user"""
    
    # Check if user already exists
    if business_users.find_one({"email": user.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user document
    user_doc = {
        "email": user.email,
        "password_hash": hash_password(user.password),
        "company_name": user.company_name,
        "gstin": user.gstin,
        "phone": user.phone,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    try:
        result = business_users.insert_one(user_doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Generate token
    token = create_access_token({
        "sub": user.email,
        "user_type": "business",
        "user_id": str(result.inserted_id)
    })
    
    return TokenResponse(
        access_token=token,
        user_type="business",
        user_email=user.email,
        user_name=user.company_name
    )

@router.post("/login/business", response_model=TokenResponse)
def login_business(credentials: UserLogin):
    """Login as business user"""
    
    user = business_users.find_one({"email": credentials.email})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Generate token
    token = create_access_token({
        "sub": user["email"],
        "user_type": "business",
        "user_id": str(user["_id"])
    })
    
    return TokenResponse(
        access_token=token,
        user_type="business",
        user_email=user["email"],
        user_name=user["company_name"]
    )

# --------------------------------------------------
# Auditor Endpoints
# --------------------------------------------------

@router.post("/register/auditor", response_model=TokenResponse)
def register_auditor(user: AuditorRegister):
    """Register a new auditor"""
    
    # Check if user already exists
    if auditors.find_one({"email": user.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user document
    user_doc = {
        "email": user.email,
        "password_hash": hash_password(user.password),
        "full_name": user.full_name,
        "license_number": user.license_number,
        "organization": user.organization,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    try:
        result = auditors.insert_one(user_doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Generate token
    token = create_access_token({
        "sub": user.email,
        "user_type": "auditor",
        "user_id": str(result.inserted_id)
    })
    
    return TokenResponse(
        access_token=token,
        user_type="auditor",
        user_email=user.email,
        user_name=user.full_name
    )

@router.post("/login/auditor", response_model=TokenResponse)
def login_auditor(credentials: UserLogin):
    """Login as auditor"""
    
    user = auditors.find_one({"email": credentials.email})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Generate token
    token = create_access_token({
        "sub": user["email"],
        "user_type": "auditor",
        "user_id": str(user["_id"])
    })
    
    return TokenResponse(
        access_token=token,
        user_type="auditor",
        user_email=user["email"],
        user_name=user["full_name"]
    )

# --------------------------------------------------
# Protected Endpoints
# --------------------------------------------------

@router.get("/me")
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user info"""
    user_type = current_user.get("user_type")
    email = current_user.get("sub")
    
    if user_type == "business":
        user = business_users.find_one({"email": email})
        if user:
            return {
                "user_type": "business",
                "email": user["email"],
                "company_name": user["company_name"],
                "gstin": user["gstin"],
                "phone": user.get("phone")
            }
    elif user_type == "auditor":
        user = auditors.find_one({"email": email})
        if user:
            return {
                "user_type": "auditor",
                "email": user["email"],
                "full_name": user["full_name"],
                "license_number": user["license_number"],
                "organization": user.get("organization")
            }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )

@router.post("/logout")
def logout():
    """Logout endpoint (client should clear token)"""
    return {"message": "Logged out successfully"}
