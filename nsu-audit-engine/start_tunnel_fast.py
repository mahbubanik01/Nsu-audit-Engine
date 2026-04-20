import os
import sys
import time
import subprocess
import re
import uuid

session_id = uuid.uuid4().hex[:8]
EXE_NAME = "cloudflared_new.exe"
LOG_FILE = f"tunnel_{session_id}.log"
URL_FILE = "tunnel_url.txt"

def main():
    if not os.path.exists(EXE_NAME):
        print(f"[!] {EXE_NAME} not found. Please ensure it exists in this directory.")
        return
            
    print(f"[*] Starting Cloudflare tunnel to localhost:8000...")
    
    # Start the process and redirect stderr to a file
    with open(LOG_FILE, "w") as f:
        proc = subprocess.Popen(
            [EXE_NAME, "tunnel", "--url", "http://localhost:8000"],
            stdout=f,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
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
