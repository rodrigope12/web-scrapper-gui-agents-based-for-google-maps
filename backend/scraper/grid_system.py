import math
from shapely.geometry import box, Polygon, Point

class GridSystem:
    def __init__(self):
        pass

    @staticmethod
    def split_bbox(min_lon, min_lat, max_lon, max_lat):
        """
        Splits a bounding box into 4 smaller sub-boxes.
        Returns a list of tuples: (min_lon, min_lat, max_lon, max_lat)
        """
        mid_lon = (min_lon + max_lon) / 2
        mid_lat = (min_lat + max_lat) / 2

        # Quadrant 1 (Top Left)
        q1 = (min_lon, mid_lat, mid_lon, max_lat)
        # Quadrant 2 (Top Right)
        q2 = (mid_lon, mid_lat, max_lon, max_lat)
        # Quadrant 3 (Bottom Left)
        q3 = (min_lon, min_lat, mid_lon, mid_lat)
        # Quadrant 4 (Bottom Right)
        q4 = (mid_lon, min_lat, max_lon, mid_lat)

        return [q1, q2, q3, q4]

    @staticmethod
    def get_lat_lon_center(min_lon, min_lat, max_lon, max_lat):
        return (min_lat + max_lat) / 2, (min_lon + max_lon) / 2

    @staticmethod
    def is_bbox_in_polygon(bbox_tuple, polygon_coords):
        """
        Checks if a bounding box intersects with the user-defined polygon.
        Optimization: We don't want to search areas completely outside the polygon.
        """
        min_lon, min_lat, max_lon, max_lat = bbox_tuple
        bbox_poly = box(min_lon, min_lat, max_lon, max_lat)
        
        # Create Shapely polygon mainly to handle the input format
        # Assumes polygon_coords is a list of [lon, lat]
        user_poly = Polygon(polygon_coords)

        return user_poly.intersects(bbox_poly)
