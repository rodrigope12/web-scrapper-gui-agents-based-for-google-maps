from typing import List, Tuple, Optional
from shapely.geometry import Polygon, box, Point
from backend.database.models import GridCell

class GridManager:
    """
    Manages the geographic grid system.
    Splits large areas into smaller sub-grids to ensure full coverage
    when Google Maps limits results (approx 120 per view).
    Supports arbitrary Polygon boundaries.
    """

    @staticmethod
    def split_cell(cell: GridCell, polygon: Optional[Polygon] = None) -> List[dict]:
        """
        Splits a GridCell into 4 equal sub-cells (Quadtree split).
        Returns a list of dictionaries ready to be inserted as new GridCells.
        If a polygon is provided, only returns sub-cells that intersect with it.
        """
        mid_lat = (cell.lat_min + cell.lat_max) / 2
        mid_lon = (cell.lon_min + cell.lon_max) / 2
        
        # Define 4 quadrants
        sub_cells_data = [
            # Top-Left
            {
                "lat_min": mid_lat, "lat_max": cell.lat_max,
                "lon_min": cell.lon_min, "lon_max": mid_lon
            },
            # Top-Right
            {
                "lat_min": mid_lat, "lat_max": cell.lat_max,
                "lon_min": mid_lon, "lon_max": cell.lon_max
            },
            # Bottom-Left
            {
                "lat_min": cell.lat_min, "lat_max": mid_lat,
                "lon_min": cell.lon_min, "lon_max": mid_lon
            },
            # Bottom-Right
            {
                "lat_min": cell.lat_min, "lat_max": mid_lat,
                "lon_min": mid_lon, "lon_max": cell.lon_max
            }
        ]
        
        if not polygon:
            return sub_cells_data

        # Filter by Polygon intersection
        relevant_cells = []
        for data in sub_cells_data:
            cell_box = box(data['lon_min'], data['lat_min'], data['lon_max'], data['lat_max'])
            if polygon.intersects(cell_box):
                relevant_cells.append(data)
                
        return relevant_cells

    @staticmethod
    def should_split(results_count: int, limit: int = 100) -> bool:
        """
        Decides if a split is necessary.
        """
        # If we found e.g. 110+ results, it's safer to split to be sure we aren't cut off.
        return results_count >= limit

    @staticmethod
    def get_center(cell: GridCell) -> str:
        """
        Returns "lat,lon" string for search queries.
        """
        lat = (cell.lat_min + cell.lat_max) / 2
        lon = (cell.lon_min + cell.lon_max) / 2
        return f"{lat},{lon}"

    @staticmethod
    def filter_results(results: List[dict], polygon: Polygon) -> List[dict]:
        """
        Filters scraped results to ensure they are strictly inside the Polygon.
        Assumes results have 'lat' and 'lon' keys.
        """
        if not polygon:
            return results
            
        filtered = []
        for res in results:
            if 'latitude' in res and 'longitude' in res:
                p = Point(res['longitude'], res['latitude'])
                if polygon.contains(p):
                    filtered.append(res)
        return filtered
