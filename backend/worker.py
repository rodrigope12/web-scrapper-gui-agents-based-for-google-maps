import time
import json
import logging
import concurrent.futures
from sqlalchemy.orm import Session
from .database import SessionLocal, GridCell, GridStatus, Result, Job, engine
from .scraper.agent import ScraperAgent
from .scraper.grid_system import GridSystem
from .core.proxies import ProxyManager
from .core.system_monitor import SystemMonitor

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MAX_RESULTS_THRESHOLD = 50 # Google often hides results > 60-100. If we hit 50, we split to be safe.
MAX_RETRIES = 3
CONCURRENCY = 2 # Number of simultaneous Chrome instances

class WorkerPool:
    def __init__(self, concurrency=CONCURRENCY):
        self.concurrency = concurrency
        self.proxy_manager = ProxyManager()
        self.system_monitor = SystemMonitor()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=concurrency)
        self.active_tasks = 0
        self.running = True

    def start(self):
        logger.info(f"Worker Pool started with {self.concurrency} threads.")
        try:
            while self.running:
                # 0. Check System Health
                if self.system_monitor.should_throttle():
                    logger.warning("System load too high. Pausing worker for 10 seconds.")
                    time.sleep(10)
                    continue

                # 1. Get Pending Task
                task_id = self._lease_task()
                if task_id:
                    # 2. Submit to pool
                    self.executor.submit(self._run_task, task_id)
                else:
                    time.sleep(5)
        except KeyboardInterrupt:
            logger.info("Stopping worker pool...")
            self.running = False
            self.executor.shutdown(wait=False)

    def _lease_task(self):
        """
        Atomically (sort of) pick a task and mark it processing.
        """
        db = SessionLocal()
        try:
            # Simple locking mechanism: Update status immediately
            # In production, use SELECT FOR UPDATE
            task = db.query(GridCell).filter(GridCell.status == GridStatus.PENDING).first()
            if task:
                task.status = GridStatus.PROCESSING
                db.commit()
                logger.info(f"Leased task {task.id}")
                return task.id
            return None
        except Exception as e:
            db.rollback()
            logger.error(f"Error leasing task: {e}")
            return None
        finally:
            db.close()

    def _run_task(self, cell_id):
        process_grid_cell(cell_id, self.proxy_manager)

def process_grid_cell(cell_id: int, proxy_manager: ProxyManager):
    db: Session = SessionLocal()
    agent = None
    
    try:
        # Re-fetch cell details
        cell = db.query(GridCell).filter(GridCell.id == cell_id).first()
        if not cell: return

        # Decode bbox
        try:
            bbox = json.loads(cell.coordinates_json)
        except:
            logger.error(f"Invalid JSON for cell {cell_id}")
            cell.status = GridStatus.FAILED
            db.commit()
            return

        min_lon, min_lat, max_lon, max_lat = bbox
        lat, lon = GridSystem.get_lat_lon_center(min_lon, min_lat, max_lon, max_lat)

        logger.info(f"Agent starting for Cell {cell_id} at {lat}, {lon}")

        # Initialize Agent
        try:
            agent = ScraperAgent(headless=False, proxy_manager=proxy_manager) # Headless=False for better evasion (UC supports headless=new now, but False is safest)
            results = agent.search_area(lat, lon, query=cell.search_query or "Restaurants")
        except Exception as e:
            # Handle potential crash
            logger.error(f"Agent crashed for cell {cell_id}: {e}")
            cell.attempts = (cell.attempts or 0) + 1
            cell.last_error = str(e)
            if cell.attempts < MAX_RETRIES:
                cell.status = GridStatus.PENDING # Retry
                logger.info(f"Retrying cell {cell_id} (Attempt {cell.attempts})")
            else:
                cell.status = GridStatus.FAILED
            db.commit()
            return

        # Logic for splitting vs completion
        should_split = False
        if len(results) >= MAX_RESULTS_THRESHOLD:
             should_split = True
        
        if should_split:
            logger.info(f"Results {len(results)} >= Threshold. Splitting cell {cell_id}.")
            sub_boxes = GridSystem.split_bbox(min_lon, min_lat, max_lon, max_lat)
            
            # Add sub-cells
            for box in sub_boxes:
                new_cell = GridCell(
                    job_id=cell.job_id,
                    status=GridStatus.PENDING,
                    coordinates_json=json.dumps(box),
                    search_query=cell.search_query
                )
                db.add(new_cell)
            
            cell.status = GridStatus.COMPLETED
            db.commit()
        else:
            # Save final results
            logger.info(f"Saving {len(results)} results for cell {cell_id}.")
            for r in results:
                try:
                    # DEDUPLICATION CHECK
                    place_id = r.get('place_id')
                    exists = False
                    if place_id:
                        # Check if we already have this place_id for this job
                        existing = db.query(Result).filter(
                            Result.job_id == cell.job_id,
                            Result.place_id == place_id
                        ).first()
                        if existing:
                            exists = True
                    
                    if not exists:
                        res = Result(
                            job_id=cell.job_id,
                            place_id=place_id,
                            name=r.get('name'),
                            address=r.get('address_raw'),
                            category=r.get('category'),
                            rating=r.get('rating'), # Agent returns float
                            reviews_count=r.get('reviews'), # Agent returns int
                            latitude=r.get('latitude') if r.get('latitude') else lat,
                            longitude=r.get('longitude') if r.get('longitude') else lon,
                            phone=r.get('phone'),
                            place_type=r.get('place_type'),
                            website=r.get('url')
                        )
                        db.add(res)
                except Exception as e:
                    logger.warning(f"Error saving result: {e}")
            
            # Update job statistics
            job = db.query(Job).filter(Job.id == cell.job_id).first()
            if job:
                job.completed_grids = (job.completed_grids or 0) + 1
            
            cell.status = GridStatus.COMPLETED
            db.commit()

    except Exception as e:
        logger.critical(f"Critical worker error on cell {cell_id}: {e}")
        if cell:
            cell.status = GridStatus.FAILED
            cell.last_error = str(e)
            db.commit()
    finally:
        if agent:
            agent.close()
        db.close()

if __name__ == "__main__":
    pool = WorkerPool(concurrency=2)
    pool.start()
