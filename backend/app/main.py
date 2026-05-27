from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, comparisons, configs, repositories

app = FastAPI(title="Code Comparison API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(repositories.router)
app.include_router(comparisons.router)
app.include_router(configs.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
