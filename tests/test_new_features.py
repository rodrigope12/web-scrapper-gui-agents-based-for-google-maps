import sys
import os
import json
import unittest
from unittest.mock import MagicMock, patch

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.manager import JobManager
from backend.database import init_db, Job, GridCell, SessionLocal, Result
from backend.scraper.agent import ScraperAgent

class TestScraperImprovements(unittest.TestCase):
    def setUp(self):
        # Use in-memory DB for testing
        # Patching the DB engine in database.py would be best, but for now we rely on the implementation 
        # using the file. ideally we'd switch to sqlite:///:memory: but the import runs on load.
        # We'll just check logic here.
        pass

    def test_keywords_job_creation(self):
        """Verify that creating a job with keywords creates multiple initial grids."""
        manager = JobManager()
        
        # Test Data
        name = "Test Job Keywords"
        polygon = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-74.0060, 40.7128],
                        [-74.0050, 40.7128],
                        [-74.0050, 40.7138],
                        [-74.0060, 40.7138],
                        [-74.0060, 40.7128]
                    ]]
                }
            }]
        }
        keywords = ["pizza", "burgers", "sushi"]
        
        # Action
        job = manager.create_job(name, polygon, keywords)
        
        # Assertions
        self.assertEqual(job.total_grids, 3)
        self.assertEqual(len(job.keywords_json), 3)
        
        # Check Grids
        db = SessionLocal()
        grids = db.query(GridCell).filter(GridCell.job_id == job.id).all()
        self.assertEqual(len(grids), 3)
        
        queries = [g.search_query for g in grids]
        self.assertIn("pizza", queries)
        self.assertIn("burgers", queries)
        self.assertIn("sushi", queries)
        
        print("\u2705 Keywords Job Creation Passed")
        db.close()

    @patch('backend.scraper.agent.uc.Chrome')
    def test_agent_selectors_and_options(self, mock_driver):
        """Verify agent loads selectors and sets chrome options."""
        mock_driver.return_value = MagicMock()
        
        agent = ScraperAgent(headless=True)
        
        # Verify Selectors loaded
        self.assertIsNotNone(agent.selectors)
        self.assertIn('feed', agent.selectors)
        self.assertEqual(agent.selectors['card_css'], "div[role='article']")
        
        print("\u2705 Agent Selectors Load Passed")

    def test_place_id_extraction(self):
        """Verify logic for extracting place_id from URL."""
        # We can't easily test the full selenium flow without browser, 
        # but we can test the helper method if we exposed it or test via subclassing/mocking.
        # Let's test the helper _parse_coords_from_url which we touched, 
        # and standard logic (unfortunately Logic is inside extract_detailed_results).
        
        # Let's instantiate agent with mock driver
        with patch('backend.scraper.agent.uc.Chrome') as mock_uc:
            mock_uc.return_value = MagicMock()
            agent = ScraperAgent(headless=True)
            
            # Simulated Feed Element and Card
            mock_card = MagicMock()
            mock_link = MagicMock()
            mock_link.get_attribute.return_value = "https://www.google.com/maps/place/Joes+Pizza/data=!4m7!3m6!1s0x0:0x12345abcdef!8m2!3d40.7!4d-74.0?hl=en"
            
            mock_card.find_element.return_value = mock_link
            mock_card.get_attribute.return_value = "Joe's Pizza"
            mock_card.text = "Joe's Pizza\n4.5(2.0K) · Pizza · $$"
            
            mock_feed = MagicMock()
            mock_feed.find_elements.return_value = [mock_card]
            
            # Run extraction
            results = agent.extract_detailed_results(mock_feed)
            
            self.assertEqual(len(results), 1)
            res = results[0]
            self.assertEqual(res['name'], "Joe's Pizza")
            self.assertEqual(res['latitude'], 40.7)
            self.assertIn('0x12345abcdef', res['url']) # Verify URL is preserved
            self.assertEqual(res['place_id'], "https://www.google.com/maps/place/Joes+Pizza/data=!4m7!3m6!1s0x0:0x12345abcdef!8m2!3d40.7!4d-74.0") # Based on splitting '?'
            
            print("\u2705 Place ID Extraction Logic Passed")

if __name__ == '__main__':
    # Initialize DB (creates file if needed)
    init_db()
    unittest.main()
