import logging
import os
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

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

MONGO_URI = os.getenv("MONGODB_URI")
if not MONGO_URI:
    raise ValueError("MONGODB_URI environment variable is not set!")

client = AsyncIOMotorClient(MONGO_URI)
db = client.fastapi
coworkers_collection = db.coworkers


class CoworkerCreate(BaseModel):
    name: str
    role: str
    department: str
    salary: float = Field(gt=0)


class Coworker(CoworkerCreate):
    id: str


@app.on_event("startup")
async def startup_event():
    """
    Startup event handler that checks the MongoDB connection.
    """
    try:
        await client.admin.command("ping")
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise


@app.get("/coworkers", response_model=List[Coworker])
async def list_coworkers(
    search: Optional[str] = Query(
        None, description="Search term for name, role, or department"
    ),
    department: Optional[str] = Query(None, description="Filter by department"),
    sort_by: Optional[str] = Query(None, description="Field to sort by"),
    limit: int = Query(10, ge=1, le=100, description="Number of results to return"),
):
    """
    Retrieve a list of coworkers based on search criteria, department, sorting, and limit.
    """
    try:
        query = {}
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"role": {"$regex": search, "$options": "i"}},
                {"department": {"$regex": search, "$options": "i"}},
            ]
        if department:
            query["department"] = department

        sort_dict = [(sort_by, 1)] if sort_by else [("name", 1)]
        cursor = coworkers_collection.find(query).sort(sort_dict).limit(limit)
        coworkers = await cursor.to_list(length=limit)

        for coworker in coworkers:
            coworker["id"] = str(coworker["_id"])
            del coworker["_id"]

        return coworkers
    except Exception as e:
        logger.error(f"Error in list_coworkers: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/coworkers", response_model=Coworker)
async def create_coworker(coworker: CoworkerCreate):
    """
    Create a new coworker entry in the database.
    """
    try:
        new_coworker = coworker.dict()
        result = await coworkers_collection.insert_one(new_coworker)
        new_coworker["id"] = str(result.inserted_id)
        logger.info(f"Created new coworker: {new_coworker['name']}")
        return new_coworker
    except Exception as e:
        logger.error(f"Error in create_coworker: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/departments")
async def get_departments():
    """
    Retrieve a list of unique departments from the coworkers collection.
    """
    try:
        departments = await coworkers_collection.distinct("department")
        return {"departments": departments}
    except Exception as e:
        logger.error(f"Error in get_departments: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
