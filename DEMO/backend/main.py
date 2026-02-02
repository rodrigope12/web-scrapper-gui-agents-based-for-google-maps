from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn
import os
import io
import pandas as pd
import requests
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from fastapi.responses import Response, StreamingResponse

from .database import init_db, SessionLocal, Job, Result
from .manager import JobManager
from .core.config_manager import ConfigManager
from .core.system_monitor import SystemMonitor
from .core.data_cleaner import DataCleaner

app = FastAPI(title="Google Maps Scraper Backend")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB & Config
init_db()
manager = JobManager()
config_mgr = ConfigManager()
system_monitor = SystemMonitor()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Pydantic Models ---
class JobCreateRequest(BaseModel):
    name: str
    polygon: Dict[str, Any] # GeoJSON FeatureCollection
    keywords: List[str] = ["generic"]

class SavedQueryCreate(BaseModel):
    query: str

class SavedQueryUpdate(BaseModel):
    query: str

class ProfileCreate(BaseModel):
    name: str
    fields: List[str]

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    fields: Optional[List[str]] = None

class PerformanceConfig(BaseModel):
    max_concurrency: int
    request_delay: float
    random_delay: bool

class SetupConfig(BaseModel):
    two_captcha_key: str
    proxies: List[str]

class SelectorUpdate(BaseModel):
    selectors: Dict[str, str]

# --- Root ---
@app.get("/")
def read_root():
    return {"status": "running", "message": "Backend is active"}

# --- Jobs API ---
@app.post("/jobs")
def create_job(request: JobCreateRequest):
    try:
        job = manager.create_job(request.name, request.polygon, request.keywords)
        return {"job_id": job.id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/jobs")
def list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(Job).all()
    return [{
        "id": j.id,
        "name": j.name,
        "status": j.status.value,
        "created_at": j.created_at.isoformat(),
        "total_grids": j.total_grids,
        "completed_grids": j.completed_grids,
        "results_count": len(j.results)
    } for j in jobs]

@app.get("/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "id": job.id,
        "name": job.name,
        "status": job.status.value,
        "created_at": job.created_at.isoformat(),
        "total_grids": job.total_grids,
        "completed_grids": job.completed_grids,
        "results": len(job.results)
    }

@app.get("/jobs/{job_id}/results")
def get_job_results(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return [{
        "name": r.name,
        "address": r.address,
        "category": r.category,
        "rating": r.rating,
        "reviews": r.reviews_count,
        "phone": r.phone,
        "place_type": r.place_type,
        "website": r.website,
        "lat": r.latitude,
        "lon": r.longitude
    } for r in job.results]

@app.get("/jobs/{job_id}/export")
def export_job_results(job_id: int, format: str = "json", clean_phones: bool = False, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if not job.results:
        raise HTTPException(status_code=400, detail="No results to export")

    clean_data_list = []
    for r in job.results:
        # 1. Base Data
        row = {
            "Name": r.name,
            "Address": r.address,
            "Category": r.category,
            "Rating": r.rating,
            "Reviews": r.reviews_count,
            "Phone": r.phone,
            "Website": r.website,
            "Latitude": r.latitude,
            "Longitude": r.longitude,
            "Place Type": r.place_type
        }

        # 2. Smart Cleaning
        if clean_phones and row["Phone"]:
             row["Phone"] = DataCleaner.normalize_phone(row["Phone"])

        clean_data_list.append(row)

    df = pd.DataFrame(clean_data_list)

    if format.lower() == "csv":
        stream = io.StringIO()
        df.to_csv(stream, index=False)
        response = Response(content=stream.getvalue(), media_type="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename={job.name}_results.csv"
        return response

    elif format.lower() in ["excel", "xlsx"]:
        stream = io.BytesIO()
        df.to_excel(stream, index=False, engine='openpyxl')
        stream.seek(0)
        return StreamingResponse(
            stream, 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={job.name}_results.xlsx"}
        )
    
    else:
        return df.to_dict(orient="records")

@app.post("/jobs/{job_id}/start")
def start_job(job_id: int):
    return {"status": "started", "job_id": job_id, "message": "Worker will pick up pending grids automatically."}

# --- Configuration API: Saved Queries ---
@app.get("/config/queries")
def get_saved_queries():
    return config_mgr.get_saved_queries()

@app.post("/config/queries")
def add_saved_query(q: SavedQueryCreate):
    return config_mgr.add_saved_query(q.query)

@app.put("/config/queries/{query_id}")
def update_saved_query(query_id: str, q: SavedQueryUpdate):
    success = config_mgr.update_saved_query(query_id, q.query)
    if not success:
        raise HTTPException(status_code=404, detail="Query not found")
    return {"status": "updated"}

@app.delete("/config/queries/{query_id}")
def delete_saved_query(query_id: str):
    config_mgr.remove_saved_query(query_id)
    return {"status": "deleted"}

# --- Configuration API: Profiles ---
@app.get("/config/profiles")
def get_profiles():
    return config_mgr.get_profiles()

@app.post("/config/profiles")
def create_profile(p: ProfileCreate):
    return config_mgr.add_profile(p.name, p.fields)

@app.put("/config/profiles/{profile_id}")
def update_profile(profile_id: str, p: ProfileUpdate):
    updates = {k: v for k, v in p.dict().items() if v is not None}
    success = config_mgr.update_profile(profile_id, updates)
    if not success:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"status": "updated"}

@app.put("/config/profiles/{profile_id}/default")
def set_default_profile(profile_id: str):
    config_mgr.set_default_profile(profile_id)
    return {"status": "default set"}

@app.delete("/config/profiles/{profile_id}")
def delete_profile(profile_id: str):
    config_mgr.remove_profile(profile_id)
    return {"status": "deleted"}

# --- Configuration API: Performance ---
@app.get("/config/performance")
def get_performance_config():
    return config_mgr.get_performance_config()

@app.post("/config/performance")
def update_performance_config(p: PerformanceConfig):
    config_mgr.update_performance_config(p.max_concurrency, p.request_delay, p.random_delay)
    return {"status": "updated"}

# --- Configuration API: Selectors ---
@app.get("/config/selectors")
def get_selectors():
    try:
        path = os.path.join(os.path.dirname(__file__), 'scraper', 'selectors.json')
        if not os.path.exists(path):
             return {}
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/config/selectors")
def update_selectors(update: SelectorUpdate):
    try:
        path = os.path.join(os.path.dirname(__file__), 'scraper', 'selectors.json')
        with open(path, 'w') as f:
            json.dump(update.selectors, f, indent=4)
        return {"status": "updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- System API ---
@app.post("/system/setup")
def setup_system(config: SetupConfig):
    config_mgr.save_config(config.two_captcha_key, config.proxies)
    return {"status": "Configuration saved"}

@app.get("/system/check")
def system_check():
    checks = {
        "internet": False,
        "chrome_driver": False
    }
    
    # Check Internet
    try:
        requests.get("https://www.google.com", timeout=3)
        checks["internet"] = True
    except:
        pass

    # Check Driver Import
    try:
        import undetected_chromedriver as uc
        checks["chrome_driver"] = True
    except ImportError:
        pass

    return checks

@app.get("/system/health")
def system_health():
    return system_monitor.get_health()

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
