import asyncio
import logging
from typing import List, Dict
from sqlalchemy.orm import Session
from backend.database.models import Job, GridCell, PlaceResult, init_db
from backend.core.scraper_agent import ScraperAgent
from backend.core.grid_manager import GridManager

# Engine
engine = init_db()

class AgentManager:
    """
    Orchestrates the scraping process.
    - Manages a pool of ScraperAgents.
    - Fetches pending GridCells from DB.
    - Assigns cells to available agents.
    - Handles results and splitting.
    """
    def __init__(self, max_agents: int = 2):
        self.max_agents = max_agents
        self.agents: List[ScraperAgent] = []
        self.active_agents: Dict[int, bool] = {} # ID -> Busy Status
        self.lock = asyncio.Lock()
        self.logger = logging.getLogger("AgentManager")
        self.running = False

    async def initialize(self):
        """Starts the worker agents."""
        for i in range(self.max_agents):
            agent = ScraperAgent(agent_id=i, headless=True)
            await agent.start()
            self.agents.append(agent)
            self.active_agents[i] = False
        self.running = True
        self.logger.info(f"Initialized {self.max_agents} agents.")

    async def get_next_cell(self, db: Session):
        """Fetches the next PENDING grid cell."""
        return db.query(GridCell).filter(GridCell.status == "PENDING").first()

    async def start_loop(self):
        """Main loop that assigns tasks to agents."""
        self.logger.info("Starting Manager Loop...")
        while self.running:
            with Session(engine) as db:
                available_agent_id = next((aid for aid, busy in self.active_agents.items() if not busy), None)
                
                if available_agent_id is not None:
                    cell = await self.get_next_cell(db)
                    if cell:
                        # Mark as processing immediately
                        cell.status = "PROCESSING"
                        db.commit()
                        
                        agent = self.agents[available_agent_id]
                        self.active_agents[available_agent_id] = True
                        
                        # Run in background task
                        asyncio.create_task(self.process_cell(agent, cell.id))
                    else:
                        # No tasks, wait
                        await asyncio.sleep(2)
                else:
                    # All agents busy
                    await asyncio.sleep(1)

    async def process_cell(self, agent: ScraperAgent, cell_id: int):
        """Worker function to process a single cell."""
        self.logger.info(f"Agent {agent.id} processing cell {cell_id}")
        
        with Session(engine) as db:
            cell = db.query(GridCell).filter(GridCell.id == cell_id).first()
            if not cell:
                self.active_agents[agent.id] = False
                return

            try:
                center = GridManager.get_center(cell)
                lat, lon = map(float, center.split(','))
                
                # Get Search Term from Job
                search_term = cell.job.search_term
                
                # Scrape
                results = await agent.search_area(search_term, lat, lon)
                
                # Filter results by Polygon (Client side verification)
                import json
                from shapely.geometry import shape
                polygon = None
                if cell.job.polygon_geojson:
                    try:
                        polygon = shape(json.loads(cell.job.polygon_geojson))
                        results = GridManager.filter_results(results, polygon)
                    except Exception as ex:
                        self.logger.error(f"Failed to parse polygon: {ex}")

                results_count = len(results)
                
                # TODO: Save results to DB (PlaceResult)
                # self.save_results(db, cell.job_id, results)
                
                if GridManager.should_split(results_count, limit=100) and cell.level < 4: # Max depth 4
                     # Split
                     sub_cells_data = GridManager.split_cell(cell, polygon)
                     for sc_data in sub_cells_data:
                         new_cell = GridCell(
                             job_id=cell.job_id,
                             lat_min=sc_data['lat_min'], lat_max=sc_data['lat_max'],
                             lon_min=sc_data['lon_min'], lon_max=sc_data['lon_max'],
                             status="PENDING",
                             parent_id=cell.id,
                             level=cell.level + 1
                         )
                         db.add(new_cell)
                     cell.status = "SPLIT"
                else:
                    cell.status = "COMPLETED"
                
                cell.last_scanned = datetime.utcnow()
                db.commit()

            except Exception as e:
                self.logger.error(f"Error processing cell {cell_id}: {e}")
                cell.status = "FAILED" # Simplification
                db.commit()
            
            finally:
                self.active_agents[agent.id] = False

    async def shutdown(self):
        self.running = False
        for agent in self.agents:
            await agent.stop()

from datetime import datetime
