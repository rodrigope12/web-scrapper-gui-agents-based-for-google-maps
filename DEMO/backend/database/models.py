from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Job(Base):
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    search_term = Column(String, nullable=False, default="Business") # What to search for
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="PENDING")  # PENDING, RUNNING, PAUSED, COMPLETED, FAILED
    polygon_geojson = Column(Text, nullable=False)  # Storing the full polygon shape
    total_grid_cells = Column(Integer, default=0)
    completed_grid_cells = Column(Integer, default=0)
    
    grid_cells = relationship("GridCell", back_populates="job", cascade="all, delete-orphan")

class GridCell(Base):
    __tablename__ = 'grid_cells'

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=False)
    
    # Bounding Box Coordinates
    lat_min = Column(Float, nullable=False)
    lat_max = Column(Float, nullable=False)
    lon_min = Column(Float, nullable=False)
    lon_max = Column(Float, nullable=False)
    
    status = Column(String, default="PENDING") # PENDING, PROCESSING, COMPLETED, OVERFLOW (needs split)
    last_scanned = Column(DateTime, nullable=True)
    
    # Hierarchy for grid splitting (Quadtree)
    parent_id = Column(Integer, ForeignKey('grid_cells.id'), nullable=True)
    level = Column(Integer, default=0)  # Depth level (0 = root)
    
    job = relationship("Job", back_populates="grid_cells")
    children = relationship("GridCell", backref="parent", remote_side=[id])

class PlaceResult(Base):
    __tablename__ = 'place_results'

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id'))
    
    # Google Maps Data
    google_id = Column(String, unique=True, index=True) # CID or Data ID
    name = Column(String, nullable=False)
    category = Column(String)
    address = Column(String)
    phone = Column(String)
    website = Column(String)
    rating = Column(Float)
    reviews_count = Column(Integer)
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Metadata
    scraped_at = Column(DateTime, default=datetime.utcnow)
    raw_data = Column(JSON) # Store full scraped dump just in case

    job = relationship("Job")

def init_db(db_path='sqlite:///data/scraper.db'):
    engine = create_engine(db_path)
    Base.metadata.create_all(engine)
    return engine
