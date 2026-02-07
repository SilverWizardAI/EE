#!/bin/bash
#
# Launch CCM V3 - Iteration 1
#

cd "$(dirname "$0")"

echo "🖥️  Starting CCM V3 - Iteration 1 (KISS)"
echo ""
echo "Prerequisites:"
echo "  - PyQt6 installed"
echo "  - aiohttp installed"
echo "  - EE shared libraries available"
echo ""

python3 ccm_v3.py
