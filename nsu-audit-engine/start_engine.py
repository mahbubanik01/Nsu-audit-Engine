import subprocess
import time
import os
import sys
import re

def start_engine():
    print("\n" + "="*50)
    print("      NSU AUDIT ENGINE - ONE-CLICK LAUNCHER")
    print("="*50 + "\n")

    # 1. Kill any existing processes on port 8000
    print("[1/3] Clearing port 8000...")
    if sys.platform == "win32":
        os.system("powershell -Command \"Get-Process -Id (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue\"")
    
    time.sleep(1)

    # 2. Start the FastAPI Backend
    print("[2/3] Starting Backend API...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    print("      ✓ API running at http://localhost:8000")

    # 3. Start the Cloudflare Tunnel
    print("[3/3] Starting Cloudflare Tunnel...")
    # Using the existing start_tunnel script logic to get the URL
    tunnel_script = os.path.join(os.path.dirname(__file__), "start_tunnel.py")
    
    try:
        # Run start_tunnel.py and capture its output
        result = subprocess.run([sys.executable, tunnel_script], capture_output=True, text=True)
        
        # Extract the URL using regex
        match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", result.stdout)
        if match:
            url = match.group(0)
            print("\n" + "!"*50)
            print("  ENGINE IS LIVE!")
            print(f"  URL: {url}")
            print("!"*50)
            print("\nKeep this window open. Closing it will shut down the engine.")
            print("Press Ctrl+C to stop.")
            
            # Keep the main process alive while the backend runs
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n[*] Shutting down engine...")
                backend_proc.terminate()
        else:
            print("\n[!] Error: Could not retrieve Tunnel URL.")
            print(result.stdout)
            backend_proc.terminate()

    except Exception as e:
        print(f"\n[!] Failed to start tunnel: {e}")
        backend_proc.terminate()

if __name__ == "__main__":
    start_engine()
