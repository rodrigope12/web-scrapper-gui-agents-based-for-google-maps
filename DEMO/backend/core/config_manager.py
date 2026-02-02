import json
import os
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self, config_file="secrets.json"):
        # Store secrets in the same directory as the app or a robust user data dir
        # For simplicity in this project structure, we keep it in root or data dir
        self.config_path = os.path.join(os.getcwd(), "data", config_file)
        self.config = self._load_config()
        self._ensure_structure()

    def _load_config(self) -> Dict:
        if not os.path.exists(self.config_path):
            return self._default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self._default_config()

    def _default_config(self):
        return {
            "two_captcha_key": "",
            "proxies": [],
            "saved_queries": [
                {"id": str(uuid.uuid4()), "term": "Restaurants", "created_at": datetime.utcnow().isoformat()},
                {"id": str(uuid.uuid4()), "term": "Real Estate", "created_at": datetime.utcnow().isoformat()},
            ],
            "extraction_profiles": [
                {
                    "id": "p_basic",
                    "name": "Basic Info",
                    "is_default": False,
                    "fields": ["name", "address", "phone", "rating", "category"]
                },
                {
                    "id": "p_full",
                    "name": "Full Details",
                    "is_default": True,
                    "fields": ["name", "address", "phone", "rating", "reviews", "website", "category", "opening_hours", "images"]
                }
            ],
            "performance": {
                "max_concurrency": 2,
                "request_delay": 2.0,
                "random_delay": True
            },
            "is_configured": False
        }

    def _ensure_structure(self):
        """Migrate old config structure if necessary"""
        modified = False
        
        # Migrate string queries to objects
        new_queries = []
        if "saved_queries" in self.config:
            for q in self.config["saved_queries"]:
                if isinstance(q, str):
                    new_queries.append({
                        "id": str(uuid.uuid4()),
                        "term": q,
                        "created_at": datetime.utcnow().isoformat()
                    })
                    modified = True
                else:
                    new_queries.append(q)
            self.config["saved_queries"] = new_queries

        # Ensure profiles exist
        if "extraction_profiles" not in self.config:
            self.config["extraction_profiles"] = self._default_config()["extraction_profiles"]
            modified = True

        # Ensure performance settings exist
        if "performance" not in self.config:
             self.config["performance"] = self._default_config()["performance"]
             modified = True

        if modified:
            self._save_to_file()

    # --- Saved Queries Management ---
    def get_saved_queries(self) -> List[Dict]:
        return self.config.get("saved_queries", [])

    def add_saved_query(self, term: str) -> Dict:
        # Check duplicates
        for q in self.config.get("saved_queries", []):
            if q["term"].lower() == term.lower():
                return q
        
        new_query = {
            "id": str(uuid.uuid4()),
            "term": term,
            "created_at": datetime.utcnow().isoformat()
        }
        self.config.setdefault("saved_queries", []).append(new_query)
        self._save_to_file()
        return new_query

    def update_saved_query(self, query_id: str, new_term: str):
        for q in self.config.get("saved_queries", []):
            if q["id"] == query_id:
                q["term"] = new_term
                self._save_to_file()
                return True
        return False

    def remove_saved_query(self, query_id: str):
        original_len = len(self.config.get("saved_queries", []))
        self.config["saved_queries"] = [q for q in self.config["saved_queries"] if q["id"] != query_id]
        if len(self.config["saved_queries"]) < original_len:
            self._save_to_file()

    # --- Profiles Management ---
    def get_profiles(self) -> List[Dict]:
        return self.config.get("extraction_profiles", [])

    def add_profile(self, name: str, fields: List[str]) -> Dict:
        new_profile = {
            "id": str(uuid.uuid4()),
            "name": name,
            "is_default": False,
            "fields": fields
        }
        self.config.setdefault("extraction_profiles", []).append(new_profile)
        self._save_to_file()
        return new_profile

    def update_profile(self, profile_id: str, updates: Dict):
        for p in self.config.get("extraction_profiles", []):
            if p["id"] == profile_id:
                p.update(updates)
                self._save_to_file()
                return True
        return False

    def remove_profile(self, profile_id: str):
        # Prevent removing default profiles if we wanted to enforce that, but for now allow it unless it's the last one
        self.config["extraction_profiles"] = [p for p in self.config["extraction_profiles"] if p["id"] != profile_id]
        self._save_to_file()

    def set_default_profile(self, profile_id: str):
        for p in self.config.get("extraction_profiles", []):
            p["is_default"] = (p["id"] == profile_id)
        self._save_to_file()
    
    def get_default_profile(self) -> Dict:
        for p in self.config.get("extraction_profiles", []):
            if p.get("is_default"):
                return p
        # Fallback
        if self.config.get("extraction_profiles"):
            return self.config["extraction_profiles"][0]
        return {}

    # --- Performance & System ---
    def get_performance_config(self) -> Dict:
        return self.config.get("performance", {})

    def update_performance_config(self, concurrency: int, delay: float, random_delay: bool):
        self.config["performance"] = {
            "max_concurrency": concurrency,
            "request_delay": delay,
            "random_delay": random_delay
        }
        self._save_to_file()

    def _save_to_file(self):
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def save_config(self, two_captcha_key: str, proxies: List[str]):
        self.config["two_captcha_key"] = two_captcha_key
        # Clean proxies
        cleaned_proxies = [p.strip() for p in proxies if p.strip()]
        self.config["proxies"] = cleaned_proxies
        
        # Determine if configured
        if two_captcha_key or cleaned_proxies: # Allow partial config
            self.config["is_configured"] = True
        else:
            self.config["is_configured"] = False

        self._save_to_file()

    def get_proxies(self) -> List[str]:
        return self.config.get("proxies", [])

    def get_captcha_key(self) -> str:
        return self.config.get("two_captcha_key", "")

    def is_configured(self) -> bool:
        return self.config.get("is_configured", False)
