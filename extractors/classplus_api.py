import json
from curl_cffi import requests

class ClassplusClient:
    def __init__(self, org_code):
        self.base_url = "https://api.classplusapp.com"
        self.org_code = org_code
        self.total_videos = 0
        self.total_pdfs = 0
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
            
        url = f"{self.base_url}/v2/courses"
        try:
            res = self.session.get(url, headers=self.headers)
            try:
                resp = res.json()
                return {"success": True, "data": resp}
            except:
                return {"success": False, "error": f"API returned non-JSON: {res.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def extract_links(self, course_id):
        links = []
        
        def traverse(folder_id, path):
            url = f"{self.base_url}/v2/course/content/get?courseId={course_id}"
            if folder_id:
                url += f"&folderId={folder_id}"
                
            try:
                res = self.session.get(url, headers=self.headers).json()
                items = res.get("data", {}).get("courseContent", [])
                
                for item in items:
                    c_type = item.get("contentType")
                    name = item.get("name", "Unknown").replace(":", "-").strip()
                    
                    if c_type == 1: # Folder
                        traverse(item["id"], path + f"{name}/")
                    else: # File/Video
                        file_url = item.get("url")
                        if file_url:
                            links.append(f"{name}: {file_url}")
                            if c_type == 2:
                                self.total_videos += 1
                            elif c_type == 3:
                                self.total_pdfs += 1
                        else:
                            # Some files might not have url directly, maybe 'key' or something else.
                            # Classplus usually provides it directly in 'url'
                            pass
            except Exception as e:
                print(f"Error traversing folder {folder_id}: {e}")

        traverse(None, "")
        return links
