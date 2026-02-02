import pandas as pd
import io
from sqlalchemy.orm import Session
from backend.database.models import PlaceResult
import logging

logger = logging.getLogger(__name__)

class ExportService:
    @staticmethod
    def export_job(job_id: int, db: Session, format: str = 'csv') -> tuple[io.BytesIO, str]:
        """
        Exports job results to a file-like object.
        Returns (buffer, filename).
        """
        # Query Data
        results = db.query(PlaceResult).filter(PlaceResult.job_id == job_id).all()
        
        if not results:
            logger.warning(f"No results found for job {job_id}")
            # Return empty df
            df = pd.DataFrame(columns=[
                "Name", "Category", "Address", "Phone", "Website", 
                "Rating", "Reviews", "Latitude", "Longitude", "Place Type", "Link"
            ])
        else:
            # Convert to DataFrame
            data = []
            for r in results:
                data.append({
                    "Name": r.name,
                    "Category": r.category,
                    "Address": r.address,
                    "Phone": r.phone,
                    "Website": r.website,
                    "Rating": r.rating,
                    "Reviews": r.reviews_count,
                    "Latitude": r.latitude,
                    "Longitude": r.longitude,
                    "Place Type": r.place_type,
                    "Link": f"https://www.google.com/maps/place/?q=place_id:{r.google_id}" if r.google_id else ""
                })
            df = pd.DataFrame(data)

        # Generate Buffer
        buffer = io.BytesIO()
        filename = f"job_{job_id}_export.{format}"

        if format == 'csv':
            df.to_csv(buffer, index=False, encoding='utf-8-sig')
            media_type = "text/csv"
        elif format == 'xlsx':
            # Requires openpyxl
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            raise ValueError("Unsupported format")

        buffer.seek(0)
        return buffer, filename, media_type
