#!/bin/bash
# NSU Audit Engine - Comprehensive Demo
# This script demonstrates all three levels of the audit system

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          NSU GRADUATION AUDIT ENGINE - DEMO                    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "This demo will run all three levels of audit analysis."
echo ""

# Level 1 Demo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "LEVEL 1: CREDIT TALLY ENGINE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
python3 src/main.py -l 1 -t data/test_cases/test_L1.csv
echo ""
read -p "Press Enter to continue to Level 2..."
echo ""

# Level 2 Demo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "LEVEL 2: GPA CALCULATOR & WAIVER HANDLER"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
python3 src/main.py -l 2 -t data/test_cases/test_L2.csv --waive ENG102,BUS112 --no-interactive
echo ""
read -p "Press Enter to continue to Level 3..."
echo ""

# Level 3 Demo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "LEVEL 3: COMPLETE GRADUATION AUDIT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
python3 src/main.py -l 3 -t data/test_cases/test_L3_retakes.csv --program-type BBA --id 2014567890 --name "Ahmed Rahman" --no-interactive
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                      DEMO COMPLETE!                            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Try the system with your own transcript:"
echo "  python3 src/main.py -l 3 -t your_transcript.csv --program-type BBA"
echo ""
