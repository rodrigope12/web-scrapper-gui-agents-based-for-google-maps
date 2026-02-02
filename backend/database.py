from sqlalchemy import create_engine, Column, Integer, String, Float, JSON, Enum, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum
import os

# Create data directory if it doesn't exist
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "scraper.db")

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class JobStatus(enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"

class GridStatus(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    polygon_geojson = Column(JSON)  # Store the user-defined area
    keywords_json = Column(JSON, default=[]) # Store list of keywords
    total_grids = Column(Integer, default=0)
    completed_grids = Column(Integer, default=0)

    grid_cells = relationship("GridCell", back_populates="job")
    results = relationship("Result", back_populates="job")

class GridCell(Base):
    __tablename__ = "grid_cells"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    status = Column(Enum(GridStatus), default=GridStatus.PENDING)
    coordinates_json = Column(JSON)  # The bounding box or polygon for this cell
    search_query = Column(String)    # e.g., "Restaurants"
    attempts = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)

    job = relationship("Job", back_populates="grid_cells")

class Result(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    place_id = Column(String, index=True, nullable=True) # Google's Place ID if available
    name = Column(String)
    address = Column(String)
    category = Column(String)
    rating = Column(Float, nullable=True)
    reviews_count = Column(Integer, nullable=True)
    phone = Column(String, nullable=True)
    place_type = Column(String, nullable=True) # Business vs Residence
    website = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="results")

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
