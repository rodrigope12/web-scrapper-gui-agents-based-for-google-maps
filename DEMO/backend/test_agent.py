import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.core.scraper_agent import ScraperAgent
from backend.database.models import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)

async def main():
    print("Initializing Database...")
    init_db('sqlite:///backend/test.db')
    
    print("Starting Scraper Agent Test...")
    agent = ScraperAgent(agent_id=1, headless=True) # Headless=True for stability
    
    try:
        await agent.start()
        print("Agent started. Navigating...")
        
        # Test Search: Cafe in Central Park
        await agent.search_area("Cafe", 40.7812, -73.9665)
        
        print("Navigation successful. Taking screenshot...")
        await agent.page.screenshot(path="backend/test_screenshot.png")
        print("Screenshot saved.")
        
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        await agent.stop()
        print("Agent stopped.")

if __name__ == "__main__":
    asyncio.run(main())
