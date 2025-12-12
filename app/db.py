from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MASTER_DB", "master_org_db")

client: AsyncIOMotorClient | None = None

def get_client():
    global client
    if client is None:
        client = AsyncIOMotorClient(MONGO_URI)
    return client


def get_db():
    return get_client()[DB_NAME]


async def create_org_collection(org_name: str):
    db = get_db()
    coll_name = f"org_{org_name}"
    # create collection if not exists — Mongo creates on insert; optionally create with validator
    # efficient check
    collections = await db.list_collection_names()
    if coll_name not in collections:
        await db.create_collection(coll_name)
    return coll_name



async def drop_org_collection(org_name: str):
    db = get_db()
    coll_name = f"org_{org_name}"
    collections = await db.list_collection_names()
    if coll_name in collections:
        await db.drop_collection(coll_name)
    return True


async def rename_and_sync_collection(old_org_name: str, new_org_name: str):
    """
    Creates a new collection for the renamed org, copies all data from the old one,
    and drops the old collection.
    
    OPTIMIZATION: Uses MongoDB Aggregation ($out) to perform the copy on the server side.
    This is significantly faster than fetching and inserting documents one by one.
    """
    db = get_db()
    old_coll_name = f"org_{old_org_name}"
    new_coll_name = f"org_{new_org_name}"

    # Verify old exists
    collections = await db.list_collection_names()
    if old_coll_name not in collections:
        return True

    # Use aggregation to copy data efficiently
    # Pipeline: Match all -> Output to new collection
    old_coll = db[old_coll_name]
    pipeline = [{"$match": {}}, {"$out": new_coll_name}]
    
    # Note: $out creates the collection if it doesn't exist and replaces it if it does.
    # It attempts to respect indexes if possible but often needs index recreation.
    # For this assignment, data copy is the priority.
    await old_coll.aggregate(pipeline).to_list(length=None)

    # Drop old collection after successful copy
    await db.drop_collection(old_coll_name)
    return True

