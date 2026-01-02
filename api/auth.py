"""
Authentication Module - JWT-based authentication with role-based access.
Provides secure authentication for Enterprise deployments.
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import secrets
import hashlib

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from shared.logger import get_logger

logger = get_logger(__name__)


# JWT support
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    logger.warning("jwt_not_available", message="Install PyJWT for authentication support")


class UserRole(Enum):
    """User roles for access control"""
    ADMIN = "admin"
    RESEARCHER = "researcher"
    VIEWER = "viewer"


@dataclass
class User:
    """User model"""
    id: str
    email: str
    role: UserRole
    is_active: bool = True
    created_at: datetime = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role.value,
            "is_active": self.is_active
        }


@dataclass
class TokenData:
    """JWT token payload"""
    user_id: str
    email: str
    role: str
    exp: datetime


class AuthConfig:
    """Authentication configuration"""
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = int(os.getenv("JWT_EXPIRY_HOURS", "24"))


class AuthenticationManager:
    """
    Manages authentication and authorization.
    
    Features:
    - JWT token generation and validation
    - Role-based access control
    - Password hashing
    - Token refresh
    """
    
    def __init__(self, config: Optional[AuthConfig] = None):
        self.config = config or AuthConfig()
        
        # In-memory user store (use database in production)
        self._users: Dict[str, Dict[str, Any]] = {}
        
        # Initialize default admin
        self._init_default_admin()
    
    def _init_default_admin(self):
        """Create default admin user"""
        admin_email = os.getenv("ADMIN_EMAIL", "admin@research.local")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        
        self._users["admin"] = {
            "id": "admin",
            "email": admin_email,
            "password_hash": self._hash_password(admin_password),
            "role": UserRole.ADMIN,
            "is_active": True,
            "created_at": datetime.utcnow()
        }
    
    def _hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = self.config.SECRET_KEY[:16]
        return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return self._hash_password(password) == hashed
    
    def create_user(
        self,
        email: str,
        password: str,
        role: UserRole = UserRole.RESEARCHER
    ) -> User:
        """Create a new user"""
        user_id = secrets.token_urlsafe(8)
        
        self._users[user_id] = {
            "id": user_id,
            "email": email,
            "password_hash": self._hash_password(password),
            "role": role,
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        
        logger.info("user_created", user_id=user_id, email=email, role=role.value)
        
        return User(
            id=user_id,
            email=email,
            role=role,
            is_active=True,
            created_at=datetime.utcnow()
        )
    
    def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        for user_data in self._users.values():
            if user_data["email"] == email:
                if self.verify_password(password, user_data["password_hash"]):
                    return User(
                        id=user_data["id"],
                        email=user_data["email"],
                        role=user_data["role"],
                        is_active=user_data["is_active"]
                    )
        return None
    
    def create_access_token(self, user: User) -> str:
        """Create JWT access token"""
        if not JWT_AVAILABLE:
            raise RuntimeError("PyJWT not installed")
        
        expire = datetime.utcnow() + timedelta(hours=self.config.ACCESS_TOKEN_EXPIRE_HOURS)
        
        payload = {
            "sub": user.id,
            "email": user.email,
            "role": user.role.value,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.config.SECRET_KEY, algorithm=self.config.ALGORITHM)
        
        logger.info("token_created", user_id=user.id)
        return token
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify and decode JWT token"""
        if not JWT_AVAILABLE:
            raise RuntimeError("PyJWT not installed")
        
        try:
            payload = jwt.decode(token, self.config.SECRET_KEY, algorithms=[self.config.ALGORITHM])
            
            return TokenData(
                user_id=payload["sub"],
                email=payload["email"],
                role=payload["role"],
                exp=datetime.fromtimestamp(payload["exp"])
            )
        except jwt.ExpiredSignatureError:
            logger.warning("token_expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning("token_invalid", error=str(e))
            return None
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        user_data = self._users.get(user_id)
        if user_data:
            return User(
                id=user_data["id"],
                email=user_data["email"],
                role=user_data["role"],
                is_active=user_data["is_active"]
            )
        return None
    
    def refresh_token(self, token: str) -> Optional[str]:
        """Refresh access token"""
        token_data = self.verify_token(token)
        if token_data:
            user = self.get_user(token_data.user_id)
            if user and user.is_active:
                return self.create_access_token(user)
        return None


# Global auth manager
_auth_manager: Optional[AuthenticationManager] = None


def get_auth_manager() -> AuthenticationManager:
    """Get or create auth manager"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthenticationManager()
    return _auth_manager


# FastAPI dependencies
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """Get current authenticated user"""
    if credentials is None:
        return None
    
    auth_manager = get_auth_manager()
    token_data = auth_manager.verify_token(credentials.credentials)
    
    if token_data is None:
        return None
    
    return auth_manager.get_user(token_data.user_id)


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Require authenticated user"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    auth_manager = get_auth_manager()
    token_data = auth_manager.verify_token(credentials.credentials)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = auth_manager.get_user(token_data.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user


def require_role(allowed_roles: list[UserRole]):
    """Dependency factory for role-based access"""
    async def role_checker(user: User = Depends(require_auth)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {user.role.value} not authorized"
            )
        return user
    return role_checker


# Convenience dependencies
require_admin = require_role([UserRole.ADMIN])
require_researcher = require_role([UserRole.ADMIN, UserRole.RESEARCHER])
