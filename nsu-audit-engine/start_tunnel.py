import os
import sys
import time
import urllib.request
import subprocess
import re
import uuid

session_id = uuid.uuid4().hex[:8]
CLOUDFLARED_URL = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
EXE_NAME = f"cloudflared_{session_id}.exe"
LOG_FILE = f"tunnel_{session_id}.log"
URL_FILE = "tunnel_url.txt"

def main():
    print(f"[*] Downloading {EXE_NAME}...")
    if not os.path.exists(EXE_NAME):
        try:
            urllib.request.urlretrieve(CLOUDFLARED_URL, EXE_NAME)
        except Exception as e:
            print(f"[!] Failed to download: {e}")
            return
            
    print(f"[*] Starting Cloudflare tunnel to localhost:8000...")
    
    # Kill any existing instances to avoid conflicts
    os.system(f"taskkill /F /IM {EXE_NAME} >nul 2>&1")
    time.sleep(1)
    
    # Start the process and redirect stderr to a file
    with open(LOG_FILE, "w") as f:
        proc = subprocess.Popen(
            [EXE_NAME, "tunnel", "--url", "http://localhost:8000"],
            stdout=f,
            stderr=subprocess.STDOUT
        )
        
    print(f"[*] Waiting for tunnel URL...")
    
    url = None
    for _ in range(30): # Wait up to 30 seconds
        time.sleep(1)
        if not os.path.exists(LOG_FILE):
            continue
            
        with open(LOG_FILE, "r") as f:
            content = f.read()
            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", content)
            if match:
                url = match.group(0)
                break
                
    if url:
        print(f"\n[SUCCESS] Tunnel is running!")
        print(f"[URL] {url}")
        with open(URL_FILE, "w") as f:
            f.write(url)
    else:
        print(f"\n[!] Failed to get URL. Check {LOG_FILE}")
        
if __name__ == "__main__":
    main()
