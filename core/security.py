import json
import hashlib
import os
import logging
from fastapi import HTTPException, status, Depends
from fastapi.security import APIKeyHeader, HTTPBasic, HTTPBasicCredentials, HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger("Security")

SECRETS_FILE = "secrets.json"
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
http_bearer = HTTPBearer(auto_error=False)
security = HTTPBasic()


def load_secrets():
    if not os.path.exists(SECRETS_FILE):
        return {"api_keys": {}, "users": {
            "admin": "ziva_admin_password"}}
    with open(SECRETS_FILE, "r") as f:
        return json.load(f)


def save_secrets(data):
    with open(SECRETS_FILE, "w") as f:
        json.dump(data, f, indent=4)


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


async def verify_api_key(
    api_key: str = Depends(api_key_header),
    bearer: HTTPAuthorizationCredentials = Depends(http_bearer)
):
    """Validates API Key (Header or Bearer) for programmatic access."""
    secrets_data = load_secrets()
    
    # Extract token from Header or Bearer
    token_to_verify = api_key
    if not token_to_verify and bearer:
        token_to_verify = bearer.credentials
        
    hashed = hash_key(token_to_verify) if token_to_verify else ""

    valid = False
    for name, stored_hash in secrets_data.get("api_keys", {}).items():
        if stored_hash == hashed:
            valid = True
            break

    if not valid:
        if token_to_verify:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Key",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing API Key",
            )
    return True


def verify_dashboard_access(
        credentials: HTTPBasicCredentials = Depends(security)):
    """Validates Basic Auth for Dashboard."""
    secrets_data = load_secrets()
    users = secrets_data.get("users", {})

    if credentials.username not in users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    if users[credentials.username] != credentials.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username