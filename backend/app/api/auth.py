from fastapi import APIRouter, Depends, HTTPException, Header, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import jwt
import logging
import os
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from typing import Optional

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Encryption for API keys
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key())
cipher_suite = Fernet(ENCRYPTION_KEY)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


# Pydantic schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    username: str
    is_guest: bool = False


class TokenData(BaseModel):
    username: str
    user_id: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_guest: bool
    created_at: datetime
    last_login: Optional[datetime]


class UserLogin(BaseModel):
    username: str
    password: str


class APIKeyCreate(BaseModel):
    provider: str  # openai, anthropic, gemini
    key_name: Optional[str] = None
    api_key: str


class APIKeyResponse(BaseModel):
    id: str
    provider: str
    key_name: Optional[str]
    created_at: datetime
    last_used: Optional[datetime]
    is_active: bool
    usage_count: int


class GuestAPIKeys(BaseModel):
    openai_key: Optional[str] = None
    anthropic_key: Optional[str] = None
    gemini_key: Optional[str] = None


# Import models and database
from app.core.database import get_engine, SessionLocal
from app.models.repository import (
    User,
    APIKey,
    UserRepository,
    UserSQL,
    APIKeySQL,
    UserRepositorySQL,
)


# Utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key for secure storage"""
    return cipher_suite.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an API key"""
    return cipher_suite.decrypt(encrypted_key.encode()).decode()


async def get_user_by_username(username: str) -> Optional[User]:
    """Get user by username from database"""
    try:
        # Try MongoDB first, fallback to SQLite
        try:
            engine = await get_engine()
            if engine:
                user = await engine.find_one(User, User.username == username)
                return user
        except Exception:
            pass

        # Fallback to SQLite
        db = SessionLocal()
        try:
            user_sql = db.query(UserSQL).filter(UserSQL.username == username).first()
            if user_sql:
                # Convert SQLAlchemy model to ODMantic model
                # Set id field to match the SQLAlchemy model's id
                return User(
                    id=str(user_sql.id),  # Convert to string for ObjectId compatibility
                    username=user_sql.username,
                    email=user_sql.email,
                    full_name=user_sql.full_name,
                    hashed_password=user_sql.hashed_password,
                    is_active=user_sql.is_active,
                    is_guest=user_sql.is_guest,
                    created_at=user_sql.created_at,
                    last_login=user_sql.last_login,
                )
            return None
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error getting user by username: {e}")
        return None


async def get_user_by_id(user_id: str) -> Optional[User]:
    """Get user by ID from database"""
    try:
        # Try MongoDB first, fallback to SQLite
        try:
            engine = await get_engine()
            if engine:
                from bson import ObjectId

                user = await engine.find_one(User, User.id == ObjectId(user_id))
                return user
        except Exception:
            pass

        # Fallback to SQLite
        db = SessionLocal()
        try:
            user_sql = db.query(UserSQL).filter(UserSQL.id == user_id).first()
            if user_sql:
                # Convert SQLAlchemy model to ODMantic model
                # Note: Don't set id field as ODMantic will auto-generate ObjectId
                return User(
                    id=str(user_sql.id),  # type: ignore
                    username=user_sql.username,  # type: ignore
                    email=user_sql.email,  # type: ignore
                    full_name=user_sql.full_name,  # type: ignore
                    hashed_password=user_sql.hashed_password,  # type: ignore
                    is_active=user_sql.is_active,  # type: ignore
                    is_guest=user_sql.is_guest,  # type: ignore
                    created_at=user_sql.created_at,  # type: ignore
                    last_login=user_sql.last_login,  # type: ignore
                )
            return None
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error getting user by ID: {e}")
        return None


async def create_user(user_data: UserCreate) -> User:
    """Create a new user"""
    try:
        # Try MongoDB first, fallback to SQLite
        engine = None
        try:
            engine = await get_engine()
        except Exception:
            pass

        if not engine:
            # Use SQLite fallback
            db = SessionLocal()
            try:
                # Check if user already exists
                existing_user = (
                    db.query(UserSQL)
                    .filter(UserSQL.username == user_data.username)
                    .first()
                )
                if existing_user:
                    raise HTTPException(
                        status_code=400, detail="Username already exists"
                    )

                existing_email = (
                    db.query(UserSQL).filter(UserSQL.email == user_data.email).first()
                )
                if existing_email:
                    raise HTTPException(status_code=400, detail="Email already exists")

                # Create new user
                hashed_password = get_password_hash(user_data.password)
                user_sql = UserSQL(
                    username=user_data.username,
                    email=user_data.email,
                    full_name=user_data.full_name,
                    hashed_password=hashed_password,
                    is_active=True,
                    is_guest=False,
                )

                db.add(user_sql)
                db.commit()
                db.refresh(user_sql)

                # Convert SQLAlchemy model to ODMantic model
                # Note: Don't set id field as ODMantic will auto-generate ObjectId
                return User(
                    username=user_sql.username,
                    email=user_sql.email,
                    full_name=user_sql.full_name,
                    hashed_password=user_sql.hashed_password,
                    is_active=user_sql.is_active,
                    is_guest=user_sql.is_guest,
                    created_at=user_sql.created_at,
                    last_login=user_sql.last_login,
                )
            finally:
                db.close()
        else:
            # Use MongoDB
            # Check if user already exists
            existing_user = await engine.find_one(
                User, User.username == user_data.username
            )
            if existing_user:
                raise HTTPException(status_code=400, detail="Username already exists")

            existing_email = await engine.find_one(User, User.email == user_data.email)
            if existing_email:
                raise HTTPException(status_code=400, detail="Email already exists")

            # Create new user
            hashed_password = get_password_hash(user_data.password)
            user = User(
                username=user_data.username,
                email=user_data.email,
                full_name=user_data.full_name,
                hashed_password=hashed_password,
                is_active=True,
                is_guest=False,
            )

            await engine.save(user)
            return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")


async def create_guest_user() -> User:
    """Create a temporary guest user"""
    try:
        # Try MongoDB first, fallback to SQLite
        engine = None
        try:
            engine = await get_engine()
        except Exception:
            pass

        if not engine:
            # Use SQLite fallback
            db = SessionLocal()
            try:
                # Generate unique guest username
                guest_number = datetime.utcnow().timestamp()
                username = f"guest_{int(guest_number)}"

                user_sql = UserSQL(
                    username=username,
                    email=f"{username}@guest.temp",
                    full_name="Guest User",
                    hashed_password="",  # No password for guests
                    is_active=True,
                    is_guest=True,
                )

                db.add(user_sql)
                db.commit()
                db.refresh(user_sql)

                # Convert SQLAlchemy model to ODMantic model
                # Note: Don't set id field as ODMantic will auto-generate ObjectId
                return User(
                    username=user_sql.username,
                    email=user_sql.email,
                    full_name=user_sql.full_name,
                    hashed_password=user_sql.hashed_password,
                    is_active=user_sql.is_active,
                    is_guest=user_sql.is_guest,
                    created_at=user_sql.created_at,
                    last_login=user_sql.last_login,
                )
            finally:
                db.close()
        else:
            # Use MongoDB
            # Generate unique guest username
            guest_number = datetime.utcnow().timestamp()
            username = f"guest_{int(guest_number)}"

            user = User(
                username=username,
                email=f"{username}@guest.temp",
                full_name="Guest User",
                hashed_password="",  # No password for guests
                is_active=True,
                is_guest=True,
            )

            await engine.save(user)
            return user
    except Exception as e:
        logger.error(f"Error creating guest user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create guest user")


async def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user with username/password"""
    try:
        user = await get_user_by_username(username)
        if not user or not user.is_active:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        # Update last login
        user.last_login = datetime.utcnow()

        # Try MongoDB first, fallback to SQLite
        engine = None
        try:
            engine = await get_engine()
        except Exception:
            pass

        if not engine:
            # Use SQLite fallback - update the user's last login directly in SQLite
            db = SessionLocal()
            try:
                # Find the user by username since we can't use the ODMantic user.id
                user_sql = (
                    db.query(UserSQL).filter(UserSQL.username == username).first()
                )
                if user_sql:
                    user_sql.last_login = datetime.utcnow()
                    db.commit()
                    # Return the updated user with the correct SQLite ID
                    return User(
                        id=user_sql.id,
                        username=user_sql.username,
                        email=user_sql.email,
                        full_name=user_sql.full_name,
                        hashed_password=user_sql.hashed_password,
                        is_active=user_sql.is_active,
                        is_guest=user_sql.is_guest,
                        created_at=user_sql.created_at,
                        last_login=user_sql.last_login,
                    )
                return None
            finally:
                db.close()
        else:
            # Use MongoDB
            await engine.save(user)
            return user
    except Exception as e:
        logger.error(f"Error authenticating user: {e}")
        return None


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def verify_token(token: str) -> User:
    """Verify a JWT token and return the user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, user_id=user_id)
    except jwt.PyJWTError:
        raise credentials_exception

    user = await get_user_by_username(token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current authenticated user from token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, user_id=user_id)
    except jwt.PyJWTError:
        raise credentials_exception

    user = await get_user_by_username(token_data.username)
    if user is None or not user.is_active:
        raise credentials_exception
    return user


async def get_current_user_optional(
    authorization: Optional[str] = Header(default=None),
) -> Optional[User]:
    """Return the authenticated user if a valid Bearer token is provided, otherwise None."""

    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None

    try:
        return await verify_token(token)
    except HTTPException:
        return None
    except Exception as exc:
        logger.debug(f"Optional auth token verification failed: {exc}")
        return None


# Authentication endpoints
@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    try:
        user = await create_user(user_data)
        return UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_guest=user.is_guest,
            created_at=user.created_at,
            last_login=user.last_login,
        )
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise


@router.post("/login", response_model=Token)
async def login_user(user_data: UserLogin):
    """Login user with username and password"""
    user = await authenticate_user(user_data.username, user_data.password)
    if not user:
        logger.warning(f"Failed login attempt for user: {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(
        data={"sub": user.username, "user_id": str(user.id)}
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=str(user.id),
        username=user.username,
        is_guest=user.is_guest,
    )


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 compatible login endpoint"""
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username, "user_id": str(user.id)}
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=str(user.id),
        username=user.username,
        is_guest=user.is_guest,
    )


@router.post("/guest", response_model=Token)
async def create_guest_session():
    """Create a guest user session"""
    try:
        user = await create_guest_user()
        access_token = create_access_token(
            data={"sub": user.username, "user_id": str(user.id)}
        )
        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=str(user.id),
            username=user.username,
            is_guest=True,
        )
    except Exception as e:
        logger.error(f"Guest session creation failed: {e}")
        raise


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_guest=current_user.is_guest,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
    )


# API Key management endpoints
@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    api_key_data: APIKeyCreate, current_user: User = Depends(get_current_user)
):
    """Create/update an API key for the current user"""
    try:
        engine = await get_engine()

        # Encrypt the API key
        encrypted_key = encrypt_api_key(api_key_data.api_key)

        # Check if key already exists for this provider
        existing_key = await engine.find_one(
            APIKey,
            APIKey.user_id == current_user.id,
            APIKey.provider == api_key_data.provider,
            APIKey.key_name == api_key_data.key_name,
        )

        if existing_key:
            # Update existing key
            existing_key.encrypted_key = encrypted_key
            existing_key.is_active = True
            await engine.save(existing_key)
            api_key_obj = existing_key
        else:
            # Create new key
            api_key_obj = APIKey(
                user_id=current_user.id,
                provider=api_key_data.provider,
                key_name=api_key_data.key_name,
                encrypted_key=encrypted_key,
                is_active=True,
            )
            await engine.save(api_key_obj)

        return APIKeyResponse(
            id=str(api_key_obj.id),
            provider=api_key_obj.provider,
            key_name=api_key_obj.key_name,
            created_at=api_key_obj.created_at,
            last_used=api_key_obj.last_used,
            is_active=api_key_obj.is_active,
            usage_count=api_key_obj.usage_count,
        )
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to create API key")


@router.get("/api-keys", response_model=list[APIKeyResponse])
async def get_user_api_keys(current_user: User = Depends(get_current_user)):
    """Get all API keys for the current user"""
    try:
        engine = await get_engine()
        api_keys = await engine.find(APIKey, APIKey.user_id == current_user.id)

        return [
            APIKeyResponse(
                id=str(key.id),
                provider=key.provider,
                key_name=key.key_name,
                created_at=key.created_at,
                last_used=key.last_used,
                is_active=key.is_active,
                usage_count=key.usage_count,
            )
            for key in api_keys
        ]
    except Exception as e:
        logger.error(f"Error getting API keys: {e}")
        raise HTTPException(status_code=500, detail="Failed to get API keys")


@router.delete("/api-keys/{key_id}")
async def delete_api_key(key_id: str, current_user: User = Depends(get_current_user)):
    """Delete an API key"""
    try:
        engine = await get_engine()
        api_key = await engine.get(APIKey, key_id)

        if not api_key or api_key.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="API key not found")

        await engine.delete(api_key)
        return {"message": "API key deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete API key")


# Utility function to get API key for a user
async def get_user_api_key(user_id: str, provider: str) -> Optional[str]:
    """Get decrypted API key for user and provider"""
    try:
        engine = await get_engine()
        api_key = await engine.find_one(
            APIKey,
            APIKey.user_id == user_id,
            APIKey.provider == provider,
            APIKey.is_active == True,
        )

        if not api_key:
            return None

        # Update usage
        api_key.last_used = datetime.utcnow()
        api_key.usage_count += 1
        await engine.save(api_key)

        return decrypt_api_key(api_key.encrypted_key)
    except Exception as e:
        logger.error(f"Error getting user API key: {e}")
        return None


# Guest API key handling
@router.post("/guest/api-keys")
async def set_guest_api_keys(
    api_keys: GuestAPIKeys, current_user: User = Depends(get_current_user)
):
    """Set API keys for guest session (temporary, not stored)"""
    if not current_user.is_guest:
        raise HTTPException(status_code=403, detail="Only available for guest users")

    try:
        # For guests, we'll store the API keys in session or cache temporarily
        # This is a simplified implementation - you might want to use Redis or session storage
        from app.core.database import cache_service

        session_key = f"guest_api_keys:{current_user.id}"
        api_key_data = {}

        if api_keys.openai_key:
            api_key_data["openai"] = encrypt_api_key(api_keys.openai_key)
        if api_keys.anthropic_key:
            api_key_data["anthropic"] = encrypt_api_key(api_keys.anthropic_key)
        if api_keys.gemini_key:
            api_key_data["gemini"] = encrypt_api_key(api_keys.gemini_key)

        # Store in cache with 24-hour TTL for guest sessions
        import json

        await cache_service.set(session_key, json.dumps(api_key_data), ttl=86400)

        return {
            "message": "API keys set for guest session",
            "providers_set": list(api_key_data.keys()),
            "expires_in": "24 hours",
        }
    except Exception as e:
        logger.error(f"Error setting guest API keys: {e}")
        raise HTTPException(status_code=500, detail="Failed to set guest API keys")


@router.get("/guest/api-keys")
async def get_guest_api_keys(current_user: User = Depends(get_current_user)):
    """Get available API key providers for guest session"""
    if not current_user.is_guest:
        raise HTTPException(status_code=403, detail="Only available for guest users")

    try:
        from app.core.database import cache_service
        import json

        session_key = f"guest_api_keys:{current_user.id}"
        cached_data = await cache_service.get(session_key)

        if cached_data:
            api_key_data = json.loads(cached_data)
            return {
                "providers_available": list(api_key_data.keys()),
                "total_providers": len(api_key_data),
            }
        else:
            return {"providers_available": [], "total_providers": 0}
    except Exception as e:
        logger.error(f"Error getting guest API keys: {e}")
        return {"providers_available": [], "total_providers": 0}


async def get_guest_api_key(user_id: str, provider: str) -> Optional[str]:
    """Get API key for guest user from cache"""
    try:
        from app.core.database import cache_service
        import json

        session_key = f"guest_api_keys:{user_id}"
        cached_data = await cache_service.get(session_key)

        if cached_data:
            api_key_data = json.loads(cached_data)
            encrypted_key = api_key_data.get(provider)
            if encrypted_key:
                return decrypt_api_key(encrypted_key)

        return None
    except Exception as e:
        logger.error(f"Error getting guest API key: {e}")
        return None


# Updated utility function that handles both regular and guest users
async def get_api_key_for_user(user: User, provider: str) -> Optional[str]:
    """Get API key for user (handles both regular and guest users)"""
    if user.is_guest:
        return await get_guest_api_key(str(user.id), provider)
    else:
        return await get_user_api_key(str(user.id), provider)


async def user_has_provider_key(user: User, provider: str) -> bool:
    """Check whether the user (including guests) has an active API key for the provider."""
    if user.is_guest:
        guest_key = await get_guest_api_key(str(user.id), provider)
        return guest_key is not None

    try:
        engine = await get_engine()
        if engine:
            api_key = await engine.find_one(
                APIKey,
                APIKey.user_id == str(user.id),
                APIKey.provider == provider,
                APIKey.is_active == True,
            )
            return api_key is not None
    except Exception as exc:
        logger.debug(
            "Failed to determine provider key availability for user %s: %s",
            user.id,
            exc,
        )

    return False
