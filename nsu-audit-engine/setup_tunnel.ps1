# Cloudflare Tunnel Setup for NSU Audit Engine
# This script helps expose your local OCR server (port 8000) to the internet so Vercel can reach it.

Write-Host "--- NSU Audit: Cloudflare Tunnel Helper ---" -ForegroundColor Cyan

# 1. Check if cloudflared is installed
if (!(Get-Command cloudflared -ErrorAction SilentlyContinue)) {
    Write-Host "[!] cloudflared not found. Downloading..." -ForegroundColor Yellow
    # Download latest windows version (approx 30MB)
    Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile "cloudflared.exe"
    $executable = ".\cloudflared.exe"
} else {
    $executable = "cloudflared"
}

Write-Host "[*] Starting Quick Tunnel to localhost:8000..." -ForegroundColor Green
Write-Host "[*] COPY THE URL SHOWN BELOW AND PASTE IT INTO VERCEL ENV 'VITE_API_BASE_URL'" -ForegroundColor Yellow

# Start the tunnel and keep it running
& $executable tunnel --url http://localhost:8000
