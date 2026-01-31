import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from src.api_v1 import router as router_v1
from src.config import settings

app = FastAPI()

app.include_router(router_v1, prefix=settings.api_v1_prefix)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
