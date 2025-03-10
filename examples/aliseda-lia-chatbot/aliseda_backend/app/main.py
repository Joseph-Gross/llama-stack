from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg
from app.routers import chat

app = FastAPI(
    title="Aliseda Inmobiliaria LIA Chatbot API",
    description="API for Aliseda Inmobiliaria's custom LIA chatbot integration with Llama Stack",
    version="1.0.0"
)

# Configure CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend dev server
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {
        "message": "Welcome to Aliseda Inmobiliaria LIA Chatbot API",
        "docs": "/docs",
        "version": "1.0.0"
    }
