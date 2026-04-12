from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routes import auth_router, payments_router


# Create DB tables on startup
Base.metadata.create_all(bind=engine)

# Create FastAPI app instance
app = FastAPI(
    title="ReceiptPro",
    description="Receipt processing and payment verification API",
    version="1.0.0"
)

# Configure CORS to accept requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://developer1-2.github.io/Climb/ReceiptPro/receiptpro-integrated.html"],
    allow_credentials=False,
    allow_methods=["PUT", "POST", "GET", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(payments_router)


@app.get("/", tags=["root"])
def read_root():
    """Root endpoint to verify API is running."""
    return {"message": "ReceiptPro API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
