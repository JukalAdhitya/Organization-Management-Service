from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class OrgCreate(BaseModel):
    organization_name: str = Field(..., min_length=3)
    email: EmailStr
    password: str = Field(..., min_length=6)

class OrgUpdate(BaseModel):
    organization_name: str
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class OrgOut(BaseModel):
    organization_name: str
    collection_name: str
    admin_id: str

class AdminLogin(BaseModel):
    email: EmailStr
    password: str
