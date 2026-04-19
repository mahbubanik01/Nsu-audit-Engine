# NSU Audit Engine - Comprehensive Demo (Windows PowerShell)

$host.UI.RawUI.WindowTitle = "NSU Graduation Audit Engine - Demo"

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "          NSU GRADUATION AUDIT ENGINE - DEMO                    " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This demo will run all three levels of audit analysis."
Write-Host ""

# Set UTF8 encoding for Python output
$env:PYTHONUTF8=1

# Level 1 Demo
Write-Host "----------------------------------------------------------------" -ForegroundColor Yellow
Write-Host "LEVEL 1: CREDIT TALLY ENGINE" -ForegroundColor Yellow
Write-Host "----------------------------------------------------------------" -ForegroundColor Yellow
Write-Host ""
python src/main.py -l 1 -t data/test_cases/test_L1.csv
Write-Host ""
Read-Host "Press Enter to continue to Level 2..."
Write-Host ""

# Level 2 Demo
Write-Host "----------------------------------------------------------------" -ForegroundColor Yellow
Write-Host "LEVEL 2: GPA CALCULATOR AND WAIVER HANDLER" -ForegroundColor Yellow
Write-Host "----------------------------------------------------------------" -ForegroundColor Yellow
Write-Host ""
python src/main.py -l 2 -t data/test_cases/test_L2.csv --waive ENG102,BUS112 --no-interactive
Write-Host ""
Read-Host "Press Enter to continue to Level 3..."
Write-Host ""

# Level 3 Demo
Write-Host "----------------------------------------------------------------" -ForegroundColor Yellow
Write-Host "LEVEL 3: COMPLETE GRADUATION AUDIT" -ForegroundColor Yellow
Write-Host "----------------------------------------------------------------" -ForegroundColor Yellow
Write-Host ""
python src/main.py -l 3 -t data/test_cases/test_L3_retakes.csv --program-type BBA --id 2014567890 --name "Ahmed Rahman" --no-interactive
Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "                      DEMO COMPLETE!                            " -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Try the system with your own transcript:"
Write-Host "  python src/main.py -l 3 -t your_transcript.csv --program-type BBA"
Write-Host ""
