import json
from curl_cffi import requests

class ClassplusClient:
    def __init__(self, org_code):
        self.org_code = org_code
        self.base_url = "https://api.classplusapp.com"
        self.session = requests.Session(impersonate="chrome110")
        self.token = None
        self.user_id = None
        
        self.headers = {
            "api-version": "18",
            "User-Agent": "Mobile-Android",
            "Content-Type": "application/json",
            "x-access-token": ""
        }

    def generate_otp(self, mobile, country_ext="91"):
        url = f"{self.base_url}/v2/otp/generate"
        payload = {
            "orgCode": self.org_code,
            "mobile": mobile,
            "countryExt": country_ext
        }
        try:
            res = self.session.post(url, json=payload, headers=self.headers)
            return res.json()
        except Exception as e:
            return {"success": False, "message": str(e)}

    def verify_otp(self, mobile, otp, country_ext="91"):
        url = f"{self.base_url}/v2/users/verify"
        payload = {
            "orgCode": self.org_code,
            "mobile": mobile,
            "otp": otp,
            "countryExt": country_ext
        }
        try:
            res = self.session.post(url, json=payload, headers=self.headers)
            resp_json = res.json()
            if resp_json.get("status") == "success" or resp_json.get("data"):
                data = resp_json.get("data", {})
                self.token = data.get("token")
                self.user_id = data.get("user", {}).get("id")
                self.headers["x-access-token"] = self.token
                return {"success": True, "data": data}
            return {"success": False, "error": resp_json.get("message", "Invalid OTP")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def fetch_courses(self):
        if not self.token:
            return {"success": False, "error": "Not authenticated"}
            
        url = f"{self.base_url}/v2/users/me"
        try:
            res = self.session.get(url, headers=self.headers)
            resp = res.json()
            # Usually the user profile contains enrolled courses or we hit /v2/courses
            return {"success": True, "data": resp}
        except Exception as e:
            return {"success": False, "error": str(e)}
