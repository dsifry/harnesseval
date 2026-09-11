#!/bin/bash
cd "$(dirname "$0")/.."
exec python3 tools/campaign_dashboard.py
