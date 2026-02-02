import requests
import time
import logging

logger = logging.getLogger(__name__)

class CaptchaSolver:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url_in = "https://2captcha.com/in.php"
        self.base_url_res = "https://2captcha.com/res.php"

    def solve_recaptcha_v2(self, site_key: str, url: str) -> str:
        """
        Solves Google ReCaptcha V2.
        """
        if not self.api_key:
            raise ValueError("No 2Captcha API Key configured.")

        # 1. Submit Request
        payload = {
            'key': self.api_key,
            'method': 'userrecaptcha',
            'googlekey': site_key,
            'pageurl': url,
            'json': 1
        }
        
        try:
            logger.info(f"Submitting CAPTCHA for solution...")
            resp = requests.post(self.base_url_in, data=payload)
            data = resp.json()
            
            if data.get('status') != 1:
                logger.error(f"2Captcha Submit Error: {data}")
                return None
                
            request_id = data.get('request')
            logger.info(f"Captcha submitted. ID: {request_id}")
            
            # 2. Poll for Result
            for i in range(20):
                time.sleep(5)
                resp = requests.get(f"{self.base_url_res}?key={self.api_key}&action=get&id={request_id}&json=1")
                res_data = resp.json()
                
                if res_data.get('status') == 1:
                    logger.info("Captcha Solved!")
                    return res_data.get('request') # The token
                
                if res_data.get('request') != 'CAPCHA_NOT_READY':
                    logger.warning(f"Captcha Poll Error: {res_data.get('request')}")
                    return None
                    
            logger.error("Captcha solution timed out.")
            return None
            
        except Exception as e:
            logger.error(f"Captcha Exception: {e}")
            return None
