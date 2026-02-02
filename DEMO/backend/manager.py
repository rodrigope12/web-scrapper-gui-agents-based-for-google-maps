from .database import SessionLocal, Job, GridCell, GridStatus, JobStatus, Result
from .scraper.grid_system import GridSystem
import geojson
import json

class JobManager:
    def __init__(self):
        self.db = SessionLocal()

    def create_job(self, name, polygon_feature_collection, keywords=None):
        """
        Creates a new job and initializes the first grid cell(s) (one per keyword).
        """
        if keywords is None or len(keywords) == 0:
            keywords = ["generic"]

        # Calculate bounding box of the entire polygon
        # This is a simplification. Ideally we take the user's polygon and split it.
        # For now, let's assume the user draws one polygon.
        
        # We need to extract the coordinates from the GeoJSON
        try:
            feature = polygon_feature_collection['features'][0]
            geometry = feature['geometry']
            coords = geometry['coordinates'][0] # List of [lon, lat]
        except (KeyError, IndexError):
            raise ValueError("Invalid GeoJSON Format")

        # Calculate Bounds
        lons = [p[0] for p in coords]
        lats = [p[1] for p in coords]
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)

        # Create Job Entry
        new_job = Job(
            name=name,
            status=JobStatus.PENDING,
            polygon_geojson=polygon_feature_collection,
            keywords_json=keywords,
            total_grids=len(keywords), # Start with N grids
            completed_grids=0
        )
        self.db.add(new_job)
        self.db.commit()
        self.db.refresh(new_job)

        # Create Initial Grid Cells (One big box PER KEYWORD)
        for keyword in keywords:
            initial_cell = GridCell(
                job_id=new_job.id,
                status=GridStatus.PENDING,
                coordinates_json=json.dumps([min_lon, min_lat, max_lon, max_lat]),
                search_query=keyword
            )
            self.db.add(initial_cell)
        
        self.db.commit()

        return new_job

    def get_pending_cells(self):
        return self.db.query(GridCell).filter(GridCell.status == GridStatus.PENDING).all()

    def mark_cell_processing(self, cell_id):
        cell = self.db.query(GridCell).filter(GridCell.id == cell_id).first()
        if cell:
            cell.status = GridStatus.PROCESSING
            self.db.commit()

    def mark_cell_completed(self, cell_id, results_count=0):
        cell = self.db.query(GridCell).filter(GridCell.id == cell_id).first()
        if cell:
            cell.status = GridStatus.COMPLETED
            # Update Job Progress logic here
            self.db.commit()

    def add_subgrids(self, parent_cell_id, new_bboxes):
        """
        If a cell needs splitting, we mark it as completed (or split) and add children.
        """
        parent = self.db.query(GridCell).filter(GridCell.id == parent_cell_id).first()
        job_id = parent.job_id
        
        for bbox in new_bboxes:
            # bbox is (min_lon, min_lat, max_lon, max_lat)
            new_cell = GridCell(
                job_id=job_id,
                status=GridStatus.PENDING,
                coordinates_json=json.dumps(bbox),
                search_query=parent.search_query
            )
            self.db.add(new_cell)
        
        self.db.commit()
