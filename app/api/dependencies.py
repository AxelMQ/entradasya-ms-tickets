from typing import Any, Dict, Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token

security_scheme = HTTPBearer(auto_error=False)


async def verify_internal_token_or_jwt(
    x_internal_token: Optional[str] = Header(None, alias="X-Internal-Token"),
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Dict[str, Any]:
    """
    Validates either the X-Internal-Token header or a Bearer JWT.
    Used for inter-service communication (e.g. from ms-orders or ms-checkin).
    """
    # 1. Check internal token
    if x_internal_token and x_internal_token == settings.INTERNAL_TOKEN:
        return {"type": "internal", "service": "internal-service"}

    # 2. Check Bearer JWT
    if auth and auth.credentials:
        payload = decode_access_token(auth.credentials)
        return {"type": "jwt", "payload": payload}

    # If neither provided or internal token mismatch
    if x_internal_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token interno inválido",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Autenticación requerida: proporcione X-Internal-Token o token Bearer",
        headers={"WWW-Authenticate": "Bearer"},
    )
