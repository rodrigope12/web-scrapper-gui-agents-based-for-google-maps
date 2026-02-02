import unittest
import json
import os
from backend.database import SessionLocal, Job, GridCell, Result, init_db
from backend.manager import JobManager
from backend.worker import process_grid_cell
from backend.scraper.agent import ScraperAgent

class TestWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize DB
        init_db()
        cls.db = SessionLocal()
        cls.manager = JobManager()

    def test_full_scrape_cycle(self):
        # 1. Create a Job (Central Park area)
        # 0.01 deg is roughly 1km
        min_lon, min_lat = -73.97, 40.77
        max_lon, max_lat = -73.96, 40.78
        
        polygon = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [min_lon, min_lat],
                        [max_lon, min_lat],
                        [max_lon, max_lat],
                        [min_lon, max_lat],
                        [min_lon, min_lat]
                    ]]
                }
            }]
        }

        job = self.manager.create_job("Test Job", polygon)
        self.assertIsNotNone(job.id)

        # 2. Get Pending Cell
        pending = self.manager.get_pending_cells()
        self.assertGreater(len(pending), 0)
        task = pending[0]

        # 3. Process Cell (Headless)
        # We override search query to something specific to ensure results
        task.search_query = "Coffee"
        self.db.commit()

        print(f"Running scraper on cell {task.id}...")
        process_grid_cell(task.id, headless=True)

        # 4. Verify Results
        results = self.db.query(Result).filter(Result.job_id == job.id).all()
        print(f"Scraped {len(results)} results.")
        
        # We expect at least *some* results for Coffee in Central Park/Upper East Side
        self.assertGreater(len(results), 0)
        
        # Verify Cell Status
        self.db.refresh(task)
        self.assertEqual(str(task.status.value), "COMPLETED")

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

if __name__ == '__main__':
    unittest.main()
