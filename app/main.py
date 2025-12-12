import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

from app.routes import orgs, admin

app = FastAPI(title="Organization Management Service")
app.include_router(orgs.router)
app.include_router(admin.router)

if __name__ == '__main__':
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
