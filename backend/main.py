# Added import for dotenv
import logging
import os
from typing import List

from beanie import Document, Indexed, init_beanie
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

# Added: Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection string
MONGO_URI = os.getenv("MONGODB_URI")
if not MONGO_URI:
    logger.error("MONGODB_URI environment variable is not set!")
    raise ValueError("MONGODB_URI environment variable is not set!")

# Added: Debug print to check if MONGO_URI is loaded correctly
logger.info(f"MONGODB_URI: {MONGO_URI}")


# Beanie document model
class Coworker(Document):
    name: Indexed(str)
    role: str
    salary: float

    class Settings:
        name = "coworkers"


# Pydantic model for request validation
class CoworkerCreate(BaseModel):
    name: str
    role: str
    salary: float


# Initialize Beanie
async def init_db():
    try:
        app.state.client = AsyncIOMotorClient(MONGO_URI)
        await init_beanie(database=app.state.client.fastapi, document_models=[Coworker])
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise


@app.on_event("startup")
async def startup_event():
    await init_db()


@app.get("/db-check")
async def check_database_connection():
    try:
        collections = await app.state.client.fastapi.list_collection_names()
        return {"status": "connected", "collections": collections}
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Database connection failed: {str(e)}"
        )


@app.post("/coworkers", response_model=Coworker)
async def create_coworker(coworker: CoworkerCreate):
    new_coworker = Coworker(**coworker.dict())
    await new_coworker.insert()
    return new_coworker


@app.get("/coworkers", response_model=List[Coworker])
async def list_coworkers():
    return await Coworker.find_all().to_list()


@app.get("/coworkers/{id}", response_model=Coworker)
async def get_coworker(id: str):
    coworker = await Coworker.get(id)
    if not coworker:
        raise HTTPException(status_code=404, detail="Coworker not found")
    return coworker


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
