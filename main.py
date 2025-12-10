from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings

# Initialize FastAPI app
app = FastAPI(
    title="MarqetFi API",
    description="MarqetFi API design",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to MarqetFi API",
        "docs": "/docs",
        "health": "/api/health"
    }

# Run with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=settings.port,
        reload=settings.environment == "development"
    )