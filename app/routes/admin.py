from fastapi import APIRouter, HTTPException, status
from app.models import AdminLogin
from app.db import get_db
from app.utils import verify_password
from app.auth import create_access_token

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/login")
async def admin_login(payload: AdminLogin):
    db = get_db()
    admin = await db.admins.find_one({"email": payload.email})
    if not admin or not verify_password(payload.password, admin["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # look up org id
    org = await db.organizations.find_one({"admin_id": str(admin["_id"])})
    # The snippet used org["organization_name"] as org_id claim, let's stick to that or use actual ID.
    # The snippet: payload = {"admin_id": str(admin["_id"]), "org_id": org["organization_name"]}
    if not org:
        # Should not happen for a valid admin but good for safety
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Organization linkage error")
        
    token_payload = {"admin_id": str(admin["_id"]), "org_id": org["organization_name"]}
    token = create_access_token(token_payload)
    return {"access_token": token, "token_type": "bearer"}
    