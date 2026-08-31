from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.orchestration.pipeline import DataAnalysisPipeline

app = FastAPI(title="EDA-Guider", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pipeline
pipeline = DataAnalysisPipeline()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

@app.post("/analyze")
async def analyze(file_path: str):
    """Analyze uploaded file"""
    # Implementation to be added
    pass
