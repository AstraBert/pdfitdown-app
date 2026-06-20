import os
from functools import lru_cache

import jwt
from fastapi import HTTPException, Request


@lru_cache()
def get_jwks_client():
    JWKS_URL = f"https://api.workos.com/sso/jwks/{os.getenv('WORKOS_CLIENT_ID')}"
    return jwt.PyJWKClient(JWKS_URL)


def verify_token(request: Request) -> dict:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid Authorization header"
        )

    token = auth_header.split(" ")[1]

    try:
        jwks_client = get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=f"https://api.workos.com/user_management/{os.getenv('WORKOS_CLIENT_ID')}",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
