import asyncio
import random

async def human_sleep(min_seconds: float = 1.0, max_seconds: float = 3.0):
    """
    Sleeps for a random amount of time to simulate human behavior.
    """
    delay = random.uniform(min_seconds, max_seconds)
    await asyncio.sleep(delay)

def get_random_offset():
    """Returns a small random pixel offset for mouse clicks."""
    return random.randint(-5, 5)
