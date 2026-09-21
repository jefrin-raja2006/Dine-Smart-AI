"""Password hashing, JWT access tokens, role authorization and rate limiting."""

import threading
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Callable

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database.connection import get_db
from app.models.models import User

JWT_ALGORITHM = "HS256"

MAX_PASSWORD_BYTES = 72
MIN_PASSWORD_LENGTH = 8


# =========================================================
# PASSWORDS
# =========================================================

def password_problem(password: str) -> str | None:
    """Return a human-readable reason a password is unacceptable."""

    if len(password) < MIN_PASSWORD_LENGTH:
        return (
            f"Password must contain at least "
            f"{MIN_PASSWORD_LENGTH} characters"
        )

    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        return (
            f"Password is too long "
            f"(maximum {MAX_PASSWORD_BYTES} bytes)"
        )

    return None


def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashed.encode("utf-8"),
        )
    except ValueError:
        return False


# Used so "unknown email" takes approximately the same time
# as "wrong password".
_DUMMY_HASH = hash_password(
    "dinesmart-timing-equaliser"
)


def burn_password_check(password: str) -> None:
    verify_password(
        password[:MAX_PASSWORD_BYTES],
        _DUMMY_HASH,
    )


# =========================================================
# JWT ACCESS TOKENS
# =========================================================

def create_access_token(
    user_id: int,
    role: str = "customer",
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT containing the user ID and role."""

    now = datetime.now(timezone.utc)

    lifetime = expires_delta or timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + lifetime,
    }

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> int:
    """Return the user ID inside a valid token."""

    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[JWT_ALGORITHM],
        options={
            "require": [
                "exp",
                "sub",
            ]
        },
    )

    return int(payload["sub"])


# =========================================================
# AUTH DEPENDENCIES
# =========================================================

_bearer = HTTPBearer(
    auto_error=False
)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )


def _user_from_credentials(
    credentials: HTTPAuthorizationCredentials | None,
    db: Session,
) -> User | None:

    if credentials is None:
        return None

    try:
        user_id = decode_access_token(
            credentials.credentials
        )

    except jwt.ExpiredSignatureError:
        raise _unauthorized(
            "Session expired. Please log in again."
        )

    except (
        jwt.PyJWTError,
        ValueError,
    ):
        raise _unauthorized(
            "Invalid authentication token"
        )

    user = db.get(
        User,
        user_id,
    )

    if user is None:
        raise _unauthorized(
            "Account no longer exists"
        )

    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        _bearer
    ),
    db: Session = Depends(get_db),
) -> User:
    """Require a valid bearer token."""

    user = _user_from_credentials(
        credentials,
        db,
    )

    if user is None:
        raise _unauthorized(
            "Not authenticated"
        )

    return user


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        _bearer
    ),
    db: Session = Depends(get_db),
) -> User | None:
    """Allow both authenticated and anonymous requests."""

    return _user_from_credentials(
        credentials,
        db,
    )


# =========================================================
# ROLE AUTHORIZATION
# =========================================================

def require_roles(
    *allowed_roles: str,
) -> Callable:

    allowed = {
        role.lower()
        for role in allowed_roles
    }

    def dependency(
        current_user: User = Depends(
            get_current_user
        ),
    ) -> User:

        user_role = (
            current_user.role or "customer"
        ).lower()

        if user_role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Access denied. "
                    "Required role: "
                    + ", ".join(
                        sorted(allowed)
                    )
                ),
            )

        return current_user

    return dependency


def require_customer(
    current_user: User = Depends(
        require_roles("customer")
    ),
) -> User:
    """Allow only customers."""

    return current_user


def require_owner(
    current_user: User = Depends(
        require_roles("owner")
    ),
) -> User:
    """Allow only restaurant owners."""

    return current_user


def require_admin(
    current_user: User = Depends(
        require_roles("admin")
    ),
) -> User:
    """Allow only administrators."""

    return current_user


def require_owner_or_admin(
    current_user: User = Depends(
        require_roles(
            "owner",
            "admin",
        )
    ),
) -> User:
    """Allow restaurant owners or administrators."""

    return current_user


# =========================================================
# RATE LIMITING
# =========================================================

class RateLimiter:
    """Sliding-window in-memory rate limiter."""

    def __init__(
        self,
        max_events: int,
        window_seconds: int,
    ):
        self.max_events = max_events
        self.window_seconds = window_seconds

        self._events: dict[
            str,
            deque[float]
        ] = {}

        self._lock = threading.Lock()

    def _prune(
        self,
        key: str,
        now: float,
    ) -> deque[float]:

        events = self._events.setdefault(
            key,
            deque(),
        )

        cutoff = (
            now - self.window_seconds
        )

        while (
            events
            and events[0] <= cutoff
        ):
            events.popleft()

        if not events:
            self._events.pop(
                key,
                None,
            )
            return deque()

        return events

    def retry_after(
        self,
        key: str,
    ) -> int:

        now = time.monotonic()

        with self._lock:

            events = self._prune(
                key,
                now,
            )

            if len(events) < self.max_events:
                return 0

            return max(
                1,
                int(
                    events[0]
                    + self.window_seconds
                    - now
                ) + 1,
            )

    def hit(
        self,
        key: str,
    ) -> None:

        now = time.monotonic()

        with self._lock:

            self._prune(
                key,
                now,
            )

            self._events.setdefault(
                key,
                deque(),
            ).append(now)

    def clear(
        self,
        key: str,
    ) -> None:

        with self._lock:
            self._events.pop(
                key,
                None,
            )

    def reset_all(self) -> None:

        with self._lock:
            self._events.clear()


login_limiter = RateLimiter(
    settings.login_max_failures,
    settings.login_window_seconds,
)

register_limiter = RateLimiter(
    settings.register_max_per_window,
    settings.register_window_seconds,
)