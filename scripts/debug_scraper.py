import logging
from backend.scraper.agent import ScraperAgent

logging.basicConfig(level=logging.INFO)

def debug():
    # Headless False to see what happens
    agent = ScraperAgent(headless=False) # Headed to test stability
    try:
        # Search for something very popular
        results = agent.search_area(40.7128, -74.0060, "Starbucks")
        print(f"DEBUG: Found {len(results)} results")
        for r in results[:3]:
            print(r)
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
    finally:
        agent.close()

if __name__ == "__main__":
    debug()
