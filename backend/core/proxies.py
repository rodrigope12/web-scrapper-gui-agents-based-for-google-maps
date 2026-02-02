import logging
import random
import os
import requests
from typing import Optional, List

logger = logging.getLogger(__name__)

class ProxyManager:
    def __init__(self, proxies: Optional[List[str]] = None):
        self.proxies = proxies or []
        self._load_from_env()
        self.current_index = 0

    def _load_from_env(self):
        # Load PROXY_LIST from env if not provided
        if not self.proxies:
            if env_proxies:
                self.proxies = [p.strip() for p in env_proxies.split(",") if p.strip()]
        
        # Load from API URL if provided
        proxy_url = os.getenv("PROXY_API_URL")
        if proxy_url:
            try:
                logger.info(f"Fetching proxies from {proxy_url}...")
                resp = requests.get(proxy_url, timeout=10)
                if resp.status_code == 200:
                    # Assumes one proxy per line or similar text format
                    lines = resp.text.strip().split('\n')
                    api_proxies = [l.strip() for l in lines if l.strip()]
                    self.proxies.extend(api_proxies)
                    logger.info(f"Fetched {len(api_proxies)} proxies from API.")
            except Exception as e:
                logger.error(f"Failed to fetch proxies from API: {e}")

        if not self.proxies:
            logger.warning("No proxies configured. Agent will run direct (High Risk).")

    def get_next_proxy(self) -> Optional[str]:
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_index]
        # Rotate
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy

    def validate_proxy(self, proxy: str) -> bool:
        """
        Simple validation check.
        """
        try:
            # Check IP
            response = requests.get("https://api.ipify.org?format=json", proxies={"http": proxy, "https": proxy}, timeout=5)
            if response.status_code == 200:
                return True
        except Exception as e:
            logger.debug(f"Proxy {proxy} failed validation: {e}")
            return False
        return False
