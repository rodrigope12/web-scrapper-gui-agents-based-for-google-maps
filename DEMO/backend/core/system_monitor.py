import psutil
import logging

logger = logging.getLogger(__name__)

class SystemMonitor:
    def __init__(self, high_cpu_threshold=90, high_ram_threshold=90):
        self.high_cpu_threshold = high_cpu_threshold
        self.high_ram_threshold = high_ram_threshold

    def get_health(self):
        """
        Returns a dictionary with current system health stats.
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            ram = psutil.virtual_memory()
            ram_percent = ram.percent
            
            return {
                "cpu_percent": cpu_percent,
                "ram_percent": ram_percent,
                "ram_available_gb": round(ram.available / (1024**3), 2),
                "ram_total_gb": round(ram.total / (1024**3), 2)
            }
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            return {"cpu_percent": 0, "ram_percent": 0, "error": str(e)}

    def should_throttle(self):
        """
        Returns True if the system is under heavy load.
        """
        health = self.get_health()
        
        is_high_cpu = health["cpu_percent"] > self.high_cpu_threshold
        is_high_ram = health["ram_percent"] > self.high_ram_threshold
        
        if is_high_cpu:
            logger.warning(f"High CPU usage detected: {health['cpu_percent']}%")
        if is_high_ram:
            logger.warning(f"High RAM usage detected: {health['ram_percent']}%")
            
        return is_high_cpu or is_high_ram
