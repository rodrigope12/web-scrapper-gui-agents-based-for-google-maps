import logging
import asyncio
from fastapi import FastAPI, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from backend.database.models import init_db, Job, GridCell
from backend.core.agent_manager import AgentManager
from backend.core.config_manager import ConfigManager

# Config Manager Global
config_manager = ConfigManager()

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API")

# Database
engine = init_db()
def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()

# Agent Manager Global
manager = AgentManager(max_agents=2)

@asynccontextmanager
async def lifespan(app: FastAPI):
# Startup
    logger.info("Starting up API...")
    
    # Initialize Config
    if not config_manager.is_configured():
        logger.warning("System NOT configured. Waiting for user setup via GUI.")
    else:
        logger.info("System configured. Initializing agents...")
        # Load proxies into global proxy/agent manager if needed
        # (The AgentManager will fetch from ConfigManager or we inject it)
        pass 

    await manager.initialize()
    asyncio.create_task(manager.start_loop())
    yield
    # Shutdown
    logger.info("Shutting down API...")
    await manager.shutdown()

app = FastAPI(title="Maps Scraper API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For Electron dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "active_agents": sum(manager.active_agents.values())}

@app.get("/system/status")
def get_system_status():
    """Returns whether the system is fully configured."""
    return {
        "configured": config_manager.is_configured(),
        "has_proxies": len(config_manager.get_proxies()) > 0,
        "has_captcha_key": bool(config_manager.get_captcha_key())
    }

class SetupRequest(BaseModel):
    two_captcha_key: str
    proxies: List[str]

@app.post("/system/setup")
def setup_system(data: SetupRequest):
    """Saves configuration and initializes system."""
    try:
        config_manager.save_config(data.two_captcha_key, data.proxies)
        return {"status": "Configuration saved", "configured": True}
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        return {"error": str(e)}

# --- Saved Queries Endpoints ---

@app.get("/config/queries")
def get_saved_queries():
    return config_manager.get_saved_queries()

class QueryRequest(BaseModel):
    query: str

@app.post("/config/queries")
def add_saved_query(data: QueryRequest):
    config_manager.add_saved_query(data.query)
    return {"status": "added", "queries": config_manager.get_saved_queries()}

@app.delete("/config/queries/{query}")
def remove_saved_query(query: str):
    config_manager.remove_saved_query(query)
    return {"status": "removed", "queries": config_manager.get_saved_queries()}

from pydantic import BaseModel
from typing import List
from shapely.geometry import Polygon, Point, mapping
import json

class JobCreateRequest(BaseModel):
    name: str
    search_term: str
    polygon: List[List[float]] # List of [lat, lon]

@app.post("/jobs/")
def create_job(request: JobCreateRequest, db: Session = Depends(get_db)):
    """Create a new scraping job from a Polygon."""
    
    # Convert input [Lat, Lon] -> Shapely Polygon (Lon, Lat)
    # Note: Leaflet/Google Maps usually provides [Lat, Lon]. Shapely uses (x, y) = (Lon, Lat)
    try:
        # Pydantic validates it's a list floats
        # Create Polygon from points. 
        # Ensure it's closed? Shapely handles it or we append start to end.
        points_lon_lat = [(p[1], p[0]) for p in request.polygon]
        if len(points_lon_lat) < 3:
             # Basic validation
             return {"error": "Polygon must have at least 3 points"}
             
        poly = Polygon(points_lon_lat)
        
        # Get GeoJSON for storage
        geojson_str = json.dumps(mapping(poly))
        
        # Create Job
        job = Job(
            name=request.name,
            search_term=request.search_term,
            polygon_geojson=geojson_str,
            status="PENDING"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Create Initial Root Cell (Bounding Box)
        min_lon, min_lat, max_lon, max_lat = poly.bounds
        
        initial_cell = GridCell(
            job_id=job.id,
            lat_min=min_lat, lat_max=max_lat,
            lon_min=min_lon, lon_max=max_lon,
            status="PENDING",
            level=0
        )
        db.add(initial_cell)
        db.commit()
        
        return {"status": "Job created", "job_id": job.id}
        
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        return {"error": str(e)}

@app.get("/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    return job

from fastapi.responses import StreamingResponse
import io
import csv

@app.get("/jobs/{job_id}/export")
def export_job_data(job_id: int, format: str = 'csv', db: Session = Depends(get_db)):
    """Exports job results as CSV or Excel."""
    try:
        from backend.core.export_service import ExportService
        
        buffer, filename, media_type = ExportService.export_job(job_id, db, format)
        
        headers = {
            "Content-Disposition": f"attachment; filename={filename}"
        }
        
        return StreamingResponse(buffer, media_type=media_type, headers=headers)
    except Exception as e:
        logger.error(f"Export failed: {e}")
        return {"error": str(e)}
