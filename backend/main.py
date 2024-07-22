import logging
import os
import traceback
from typing import List, Optional

from bson import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
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
    logger.error("MONGODB_URI environment variable is not set!")
    raise ValueError("MONGODB_URI environment variable is not set!")

logger.info(f"MONGODB_URI: {MONGO_URI}")

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
    try:
        await client.admin.command("ping")
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        logger.error(traceback.format_exc())
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
    try:
        logger.debug(
            f"Received request with search={search}, department={department}, sort_by={sort_by}, limit={limit}"
        )

        query = {}
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"role": {"$regex": search, "$options": "i"}},
                {"department": {"$regex": search, "$options": "i"}},
            ]
        if department:
            query["department"] = department

        logger.debug(f"Constructed query: {query}")

        sort_dict = [(sort_by, 1)] if sort_by else [("name", 1)]
        logger.debug(f"Sort dictionary: {sort_dict}")

        cursor = coworkers_collection.find(query).sort(sort_dict).limit(limit)
        coworkers = await cursor.to_list(length=limit)

        # Convert ObjectId to string for each document
        for coworker in coworkers:
            coworker["id"] = str(coworker["_id"])
            del coworker["_id"]

        logger.debug(f"Found {len(coworkers)} coworkers")

        return coworkers
    except Exception as e:
        logger.error(f"Error in list_coworkers: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/coworkers", response_model=Coworker)
async def create_coworker(coworker: CoworkerCreate):
    try:
        new_coworker = coworker.dict()
        result = await coworkers_collection.insert_one(new_coworker)
        new_coworker["id"] = str(result.inserted_id)
        logger.info(f"Created new coworker: {new_coworker}")
        return new_coworker
    except Exception as e:
        logger.error(f"Error in create_coworker: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/departments")
async def get_departments():
    try:
        departments = await coworkers_collection.distinct("department")
        return {"departments": departments}
    except Exception as e:
        logger.error(f"Error in get_departments: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
