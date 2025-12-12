from fastapi import HTTPException, status
from datetime import datetime
from bson import ObjectId
from app.models import OrgCreate, OrgUpdate
from app.db import get_db, create_org_collection, drop_org_collection, rename_and_sync_collection
from app.utils import hash_password

class OrganizationService:
    """
    Service layer for handling Organization-related business logic.
    Decouples the controller (routes) from the database and complex processing.
    """

    @staticmethod
    async def create_organization(payload: OrgCreate):
        """
        Creates a new organization, admin user, and dynamic collection.
        """
        db = get_db()
        org_name = payload.organization_name.strip().lower()

        # 1. Validation: Ensure organization is unique
        existing = await db.organizations.find_one({"organization_name": org_name})
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization already exists")

        collection_name = f"org_{org_name}"
        
        # 2. Dynamic Resource Creation: Create Collection
        await create_org_collection(org_name)

        # 3. Admin Creation
        admin_doc = {
            "email": payload.email,
            "password": hash_password(payload.password),
            "role": "admin",
            "organization": org_name,
        }
        res = await db.admins.insert_one(admin_doc)

        # 4. Metadata Creation
        org_doc = {
            "organization_name": org_name,
            "collection_name": collection_name,
            "admin_id": str(res.inserted_id),
            "created_at": datetime.utcnow(),
        }
        await db.organizations.insert_one(org_doc)

        return {
            "organization_name": org_name,
            "collection_name": collection_name,
            "admin_id": str(res.inserted_id)
        }

    @staticmethod
    async def get_organization(organization_name: str):
        """
        Retrieves organization details by name.
        """
        db = get_db()
        org = await db.organizations.find_one({"organization_name": organization_name.strip().lower()})
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
        
        # Format for response
        org["admin_id"] = str(org.get("admin_id"))
        if "_id" in org:
            org["_id"] = str(org["_id"])
        return org

    @staticmethod
    async def update_organization(current_admin: dict, payload: OrgUpdate):
        """
        Updates an organization (name, email, password).
        Handles complex renaming logic including Data Sync.
        """
        db = get_db()
        target_org_name = current_admin["org_id"]
        
        # 1. Verify existence
        org = await db.organizations.find_one({"organization_name": target_org_name})
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

        new_org_name = payload.organization_name.strip().lower()
        
        # 2. Handle RENAME (Critical Path)
        if new_org_name != target_org_name:
            # Check uniqueness
            existing = await db.organizations.find_one({"organization_name": new_org_name})
            if existing:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New organization name already exists")
            
            new_collection_name = f"org_{new_org_name}"
            
            # Update Org Metadata
            await db.organizations.update_one(
                {"_id": org["_id"]}, 
                {"$set": {"organization_name": new_org_name, "collection_name": new_collection_name}}
            )
            # Update Admin Link
            await db.admins.update_one(
                {"_id": ObjectId(current_admin["admin_id"])},
                {"$set": {"organization": new_org_name}}
            )
            
            # Sync Data (Copy old coll -> new coll -> drop old)
            await rename_and_sync_collection(target_org_name, new_org_name)
            
            # Update local reference for subsequent steps
            target_org_name = new_org_name

        # 3. Handle Admin Credentials Update
        if payload.email or payload.password:
            update_fields = {}
            if payload.email:
                update_fields["email"] = payload.email
            if payload.password:
                update_fields["password"] = hash_password(payload.password)
            
            if update_fields:
                await db.admins.update_one({"_id": ObjectId(current_admin["admin_id"])}, {"$set": update_fields})

        # 4. Fetch and Return Updated Object
        updated_org = await db.organizations.find_one({"organization_name": target_org_name})
        updated_org["admin_id"] = str(updated_org["admin_id"])
        updated_org["_id"] = str(updated_org["_id"])
        return updated_org

    @staticmethod
    async def delete_organization(organization_name: str, current_admin: dict):
        """
        Deletes an organization and all its resources.
        Enforces ownership authorization.
        """
        # 1. Authorization Check
        if current_admin["org_id"] != organization_name.strip().lower():
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to delete this organization")

        db = get_db()
        org_name = organization_name.strip().lower()
        
        org = await db.organizations.find_one({"organization_name": org_name})
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

        # 2. Cleanup Resources
        await drop_org_collection(org_name)
        await db.admins.delete_one({"_id": ObjectId(org["admin_id"])})
        await db.organizations.delete_one({"organization_name": org_name})

        return {"status": "deleted", "organization": org_name}
