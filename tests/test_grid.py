import unittest
from backend.scraper.grid_system import GridSystem

class TestGridSystem(unittest.TestCase):
    def test_split_bbox(self):
        # 0,0 to 10,10
        min_lon, min_lat, max_lon, max_lat = 0, 0, 10, 10
        sub_grids = GridSystem.split_bbox(min_lon, min_lat, max_lon, max_lat)
        
        self.assertEqual(len(sub_grids), 4)
        
        # Check Q1 (Top Left: 0, 5, 5, 10)
        # Note: Logic in util was:
        # q1 = (min_lon, mid_lat, mid_lon, max_lat)
        # mid_lon = 5, mid_lat = 5
        # q1 = (0, 5, 5, 10)
        self.assertEqual(sub_grids[0], (0, 5, 5, 10))

    def test_center_calc(self):
        lat, lon = GridSystem.get_lat_lon_center(0, 0, 10, 10)
        self.assertEqual(lat, 5)
        self.assertEqual(lon, 5)

if __name__ == '__main__':
    unittest.main()
