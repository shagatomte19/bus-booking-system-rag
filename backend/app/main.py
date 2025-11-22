from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import buses, bookings, providers
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Bus Booking System API",
    description="API for bus ticket booking with RAG-powered provider information",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(buses.router)
app.include_router(bookings.router)
app.include_router(providers.router)


@app.get("/")
def root():
    """
    Root endpoint
    """
    return {
        "message": "Bus Booking System API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)