"""
============================================
AKASIA v2.2 - API Backend Server
============================================
Asisten Akademik Berbasis AI untuk UHO

Features:
- Chat dengan streaming response
- Feedback system (👍/👎)
- Related questions suggestions
- Document management

Jalankan dengan: python api.py
Server akan berjalan di http://localhost:8000
============================================
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from rag_engine import RAGEngine
from typing import List, Optional
import uvicorn
import shutil
import os
import json
import asyncio
from app import extract_text_from_pdf
from datetime import datetime

# Inisialisasi FastAPI dengan metadata
app = FastAPI(
    title="AKASIA API",
    description="Asisten Akademik Berbasis AI untuk Universitas Halu Oleo",
    version="2.5.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = RAGEngine()

class ChatMessage(BaseModel):
    role: str  # "user" or "ai"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None  # v2.5: Conversation history

class FeedbackRequest(BaseModel):
    query: str
    response: str
    rating: str  # "up" or "down"
    confidence: Optional[int] = None

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "UHO Academic Chatbot API is running"}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    async def generate():
        # Always reload vectorstore to ensure latest documents are used
        engine.vectorstore = engine.load_existing_vectorstore()
        if not engine.vectorstore:
            yield json.dumps({"response": "Knowledge base belum tersedia. Silakan upload dokumen terlebih dahulu di halaman Admin."}) + "\n"
            return

        # v2.5: Pass conversation history to query_stream
        history = [(m.role, m.content) for m in request.history] if request.history else []
        for chunk in engine.query_stream(request.message, history=history):
             yield json.dumps(chunk) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")

@app.post("/api/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Submit feedback for a chat response (thumbs up/down)"""
    try:
        # Store feedback in metadata
        if "feedback_history" not in engine.metadata:
            engine.metadata["feedback_history"] = []
        
        feedback_entry = {
            "query": request.query[:200],  # Limit length
            "response": request.response[:500],
            "rating": request.rating,
            "confidence": request.confidence,
            "timestamp": datetime.now().isoformat()
        }
        
        engine.metadata["feedback_history"].append(feedback_entry)
        
        # Keep only last 500 feedbacks
        if len(engine.metadata["feedback_history"]) > 500:
            engine.metadata["feedback_history"] = engine.metadata["feedback_history"][-500:]
        
        # Update totals
        if "feedback_stats" not in engine.metadata:
            engine.metadata["feedback_stats"] = {"thumbs_up": 0, "thumbs_down": 0}
        
        if request.rating == "up":
            engine.metadata["feedback_stats"]["thumbs_up"] += 1
        else:
            engine.metadata["feedback_stats"]["thumbs_down"] += 1
        
        engine.save_metadata()
        
        return {"status": "success", "message": "Feedback recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/feedback/stats")
async def get_feedback_stats():
    """Get feedback statistics"""
    stats = engine.metadata.get("feedback_stats", {"thumbs_up": 0, "thumbs_down": 0})
    total = stats["thumbs_up"] + stats["thumbs_down"]
    
    return {
        "thumbs_up": stats["thumbs_up"],
        "thumbs_down": stats["thumbs_down"],
        "total": total,
        "satisfaction_rate": round(stats["thumbs_up"] / max(total, 1) * 100, 1),
        "recent_feedback": engine.metadata.get("feedback_history", [])[-10:]
    }

@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    all_text = ""
    processed_count = 0
    total_size = 0
    filenames = []
    
    for file in files:
        try:
            # Save temp file
            temp_filename = f"temp_{file.filename}"
            with open(temp_filename, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
                file_size = len(content)
                total_size += file_size
                
            class MockFile:
                def __init__(self, path, original_name, size):
                    with open(path, "rb") as f:
                        self.data = f.read()
                    self.name = original_name
                    self.size = size
                def getvalue(self):
                    return self.data
            
            mock_file = MockFile(temp_filename, file.filename, file_size)
            text = extract_text_from_pdf(mock_file)
            
            if text:
                all_text += f"\n\n=== {file.filename} ===\n\n{text}"
                processed_count += 1
                filenames.append(file.filename)
                
            os.remove(temp_filename)
            
        except Exception as e:
            print(f"Error processing {file.filename}: {e}")
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
            continue

    if all_text:
        # Pass metadata to create_vectorstore
        combined_filename = ", ".join(filenames) if len(filenames) > 1 else filenames[0]
        success = engine.create_vectorstore(all_text, combined_filename, total_size)
        if success:
            return {
                "status": "success", 
                "processed": processed_count,
                "filenames": filenames,
                "total_size": total_size
            }
    
    raise HTTPException(status_code=500, detail="Failed to process documents")

@app.get("/api/documents")
async def get_documents():
    """Get list of all uploaded documents"""
    documents = engine.get_documents()
    return {"documents": documents}

@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document by ID"""
    success = engine.delete_document(doc_id)
    if success:
        return {"status": "success", "message": f"Document {doc_id} deleted"}
    raise HTTPException(status_code=404, detail="Document not found")

@app.get("/api/stats")
async def get_stats():
    """Get statistics for admin dashboard"""
    stats = engine.get_stats()
    
    # Calculate vector DB size (approximate from FAISS index)
    faiss_size = 0
    if os.path.exists("./faiss_index"):
        for f in os.listdir("./faiss_index"):
            faiss_size += os.path.getsize(os.path.join("./faiss_index", f))
    
    stats["vector_db_size_bytes"] = faiss_size
    return stats

@app.get("/api/analytics")
async def get_analytics():
    """Get detailed analytics for dashboard"""
    from datetime import datetime, timedelta
    from collections import Counter
    
    # Load query history
    query_history = engine.metadata.get("query_history", [])
    
    # Get hourly stats for last 24 hours
    now = datetime.now()
    hourly_stats = []
    for i in range(24, 0, -1):
        hour_start = now - timedelta(hours=i)
        hour_end = now - timedelta(hours=i-1)
        count = sum(1 for q in query_history 
                    if hour_start.isoformat() <= q.get("timestamp", "") < hour_end.isoformat())
        hourly_stats.append({
            "time": hour_start.strftime("%H:%M"),
            "queries": count
        })
    
    # Get daily stats for last 7 days
    daily_stats = []
    for i in range(7, 0, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0)
        day_end = (now - timedelta(days=i-1)).replace(hour=0, minute=0, second=0)
        count = sum(1 for q in query_history 
                    if day_start.isoformat() <= q.get("timestamp", "") < day_end.isoformat())
        daily_stats.append({
            "day": day_start.strftime("%a"),
            "date": day_start.strftime("%d/%m"),
            "queries": count
        })
    
    # Get popular questions (simplified categorization)
    question_categories = {
        "Masa Studi": ["masa studi", "lama kuliah", "berapa tahun", "durasi"],
        "SKS": ["sks", "kredit", "beban studi"],
        "Wisuda": ["wisuda", "lulus", "kelulusan", "yudisium"],
        "IPK/IPS": ["ipk", "ips", "nilai", "prestasi"],
        "Cuti": ["cuti", "tidak aktif", "izin"],
        "KRS": ["krs", "rencana studi", "mata kuliah"],
        "Jadwal": ["jadwal", "kalender", "tanggal", "kapan"],
        "Syarat": ["syarat", "ketentuan", "aturan", "peraturan"]
    }
    
    category_counts = Counter()
    for q in query_history:
        query_lower = q.get("query", "").lower()
        for category, keywords in question_categories.items():
            if any(kw in query_lower for kw in keywords):
                category_counts[category] += 1
                break
        else:
            category_counts["Lainnya"] += 1
    
    popular_topics = [
        {"topic": topic, "count": count, "percentage": round(count / max(len(query_history), 1) * 100)}
        for topic, count in category_counts.most_common(8)
    ]
    
    # Recent queries (last 10)
    recent_queries = [
        {"query": q.get("query", "")[:50], "timestamp": q.get("timestamp", "")}
        for q in sorted(query_history, key=lambda x: x.get("timestamp", ""), reverse=True)[:10]
    ]
    
    return {
        "hourly_stats": hourly_stats,
        "daily_stats": daily_stats,
        "popular_topics": popular_topics,
        "recent_queries": recent_queries,
        "total_queries_today": sum(1 for q in query_history 
                                    if q.get("timestamp", "").startswith(now.strftime("%Y-%m-%d"))),
        "total_queries_week": sum(1 for q in query_history 
                                   if (now - timedelta(days=7)).isoformat() <= q.get("timestamp", ""))
    }

@app.post("/api/clear-knowledge-base")
async def clear_knowledge_base():
    """Clear all documents and reset the knowledge base"""
    try:
        # Clear vectorstore
        if os.path.exists("./faiss_index"):
            shutil.rmtree("./faiss_index")
        
        # Clear metadata
        engine.metadata = {
            "documents": [],
            "total_queries": 0,
            "last_query_at": None
        }
        engine.save_metadata()
        engine.vectorstore = None
        
        return {"status": "success", "message": "Knowledge base cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
