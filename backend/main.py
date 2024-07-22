import random
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Item(BaseModel):
    id: int
    name: str


@app.get("/")
async def root():
    return {"message": "Hello from FastAPI!"}


@app.get("/items", response_model=List[Item])
async def get_items():
    items = [
        Item(id=1, name="Item 1"),
        Item(id=2, name="Item 2"),
        Item(id=3, name="Item 3"),
    ]
    return random.sample(items, k=2)  # Return 2 random items


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
