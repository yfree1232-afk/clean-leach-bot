import urllib.request
import urllib.parse
import json
import ssl
import base64
import re
import time
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

class AppxClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE
        
        self.token = None
        self.user_id = None
        
        # Statistics
        self.total_videos = 0
        self.total_pdfs = 0

    def login(self, email, password):
        attempts = [
            {
                "eps": ["/post/userLogin"],
                "data": f"email={urllib.parse.quote(email)}&password={urllib.parse.quote(password)}&device_type=WEB".encode('utf-8'),
                "ctype": "application/x-www-form-urlencoded"
            },
            {
                "eps": ["/api/v2/users/login", "/api/users/login", "/v3/users/login", "/v2/users/login", "/users/login", "/get/loginWithEmail"],
                "data": json.dumps({"email": email, "password": password, "device_type": "WEB"}).encode('utf-8'),
                "ctype": "application/json"
            }
        ]
        
        for attempt in attempts:
            for ep in attempt["eps"]:
                url = self.base_url + ep
                versions = ['2'] if attempt["ctype"] == "application/x-www-form-urlencoded" else ['3', '2']
                for v in versions:
                    headers = {
                        'User-Agent': 'Mozilla/5.0',
                        'client-service': 'Appx',
                        'auth-key': 'appxapi',
                        'appx-version': v,
                        'device_type': 'WEB',
                        'Content-Type': attempt["ctype"]
                    }
                    try:
                        req = urllib.request.Request(url, data=attempt["data"], headers=headers, method='POST')
                        with urllib.request.urlopen(req, context=self.ctx, timeout=10) as res:
                            resp_json = json.loads(res.read().decode('utf-8'))
                            status_val = str(resp_json.get('status'))
                            if status_val in ["200", "1"] or resp_json.get('success'):
                                data = resp_json.get('data', resp_json)
                                self.token = data.get('token') or data.get('jwt')
                                self.user_id = data.get('userid') or data.get('id')
                                return {"success": True, "data": data}
                    except Exception:
                        pass
        return {"success": False, "error": "Login failed."}

    def fetch_courses(self):
        if not self.token or not self.user_id:
            return {"success": False, "error": "Not logged in"}
            
        courses_endpoints = ["/get/mycoursev2", "/get/mycourses"]
        for v in ['3', '2']:
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'appx-version': v,
                'client-service': 'Appx',
                'auth-key': 'appxapi',
                'device_type': 'WEB',
                'Authorization': self.token,
                'token': self.token,
                'User-ID': str(self.user_id)
            }
            for ep in courses_endpoints:
                url = f"{self.base_url}{ep}?userid={self.user_id}"
                try:
                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req, context=self.ctx, timeout=10) as res:
                        resp_json = json.loads(res.read().decode('utf-8'))
                        status_val = str(resp_json.get('status'))
                        if status_val in ["200", "1"] or resp_json.get('success'):
                            return {"success": True, "courses": resp_json.get('data', [])}
                except Exception:
                    pass
        return {"success": False, "error": "Failed to fetch courses"}

    def decrypt_val(self, encrypted_str, key_str="638udh3829162018", iv_str="fedcba9876543210"):
        try:
            parts = encrypted_str.split(':')
            ciphertext_b64 = parts[0]
            iv_bytes = base64.b64decode(parts[1]) if len(parts) > 1 else iv_str.encode('utf-8')
            ciphertext_bytes = base64.b64decode(ciphertext_b64)
            cipher = AES.new(key_str.encode('utf-8'), AES.MODE_CBC, iv=iv_bytes)
            return unpad(cipher.decrypt(ciphertext_bytes), AES.block_size).decode('utf-8')
        except Exception:
            return ""

    def extract_links(self, course_id):
        self.total_videos = 0
        self.total_pdfs = 0
        all_links = []
        
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'appx-version': '2',
            'client-service': 'Appx',
            'auth-key': 'appxapi',
            'device_type': 'WEB',
            'Authorization': self.token,
            'token': self.token,
            'User-ID': str(self.user_id)
        }

        def fetch_video_details(video_id):
            url = f"{self.base_url}/get/fetchVideoDetailsById?course_id={course_id}&video_id={video_id}&ytflag=1&folder_wise_course=1&userid={self.user_id}"
            found_links = []
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, context=self.ctx, timeout=10) as res:
                    data = json.loads(res.read().decode('utf-8')).get('data', {})
                    
                    pdf_link = data.get('pdf_link')
                    if pdf_link:
                        if not pdf_link.startswith('http') and ':' in pdf_link:
                            pdf_link = self.decrypt_val(pdf_link)
                        if pdf_link:
                            self.total_pdfs += 1
                            found_links.append(f"PDF: {pdf_link}")
                            
                    pdf_link2 = data.get('pdf_link2')
                    if pdf_link2 and pdf_link2 != data.get('pdf_link'):
                        if not pdf_link2.startswith('http') and ':' in pdf_link2:
                            pdf_link2 = self.decrypt_val(pdf_link2)
                        if pdf_link2:
                            self.total_pdfs += 1
                            found_links.append(f"PDF: {pdf_link2}")
                            
                    encrypted_links = data.get('encrypted_links', [])
                    for link_obj in encrypted_links:
                        dec_link = self.decrypt_val(link_obj.get('path', ''))
                        if dec_link:
                            self.total_videos += 1
                            found_links.append(f"Video [{link_obj.get('quality', 'Unknown')}]: {dec_link}")
                            break # Only one quality
                            
                    if not encrypted_links and data.get('file_link'):
                        self.total_videos += 1
                        found_links.append(f"Video: {data['file_link']}")
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    time.sleep(3)
                    return fetch_video_details(video_id)
            except Exception:
                pass
            return found_links

        def fetch_folder(parent_id, path_prefix=""):
            url = f"{self.base_url}/get/folder_contentsv2?course_id={course_id}&parent_id={parent_id}&folder_wise_course=1&userid={self.user_id}"
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, context=self.ctx, timeout=10) as res:
                    items = json.loads(res.read().decode('utf-8')).get('data', [])
                    for item in items:
                        title = item.get('Title', item.get('title', 'Unknown'))
                        item_type = item.get('resource_type', item.get('type'))
                        item_id = item.get('id')
                        
                        is_folder = str(item.get('is_folder')) == "1" or str(item_type) in ["2", "0"] or str(item.get('material_type')).upper() == "FOLDER"
                        if is_folder:
                            fetch_folder(item_id, path_prefix + title + " > ")
                        else:
                            links = fetch_video_details(item_id)
                            if links:
                                for l in links:
                                    all_links.append(f"{path_prefix}{title}\n↳ {l}\n")
                            elif item.get('file_link') or item.get('pdf_link'):
                                link = item.get('file_link') or item.get('pdf_link')
                                if 'pdf' in str(link).lower():
                                    self.total_pdfs += 1
                                else:
                                    self.total_videos += 1
                                all_links.append(f"{path_prefix}{title}\n↳ {link}\n")
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    time.sleep(3)
                    fetch_folder(parent_id, path_prefix)
            except Exception:
                pass

        fetch_folder("-1")
        return all_links
