#!/usr/bin/env python3
"""
Build script for Tanaor Creative Arena dashboard.
Reads dashboard-data.json and injects it into the HTML template.
Run this after updating dashboard-data.json to regenerate docs/index.html.
"""
import json
import os

DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(DIR, 'dashboard-data.json')
TEMPLATE_PATH = os.path.join(DIR, 'docs', 'index.template.html')
OUTPUT_PATH = os.path.join(DIR, 'docs', 'index.html')

with open(DATA_PATH) as f:
    data = json.load(f)

with open(TEMPLATE_PATH) as f:
    html = f.read()

html = html.replace('__DASHBOARD_DATA__', json.dumps(data))

with open(OUTPUT_PATH, 'w') as f:
    f.write(html)

print(f"Dashboard built: {len(data['ads'])} ads, {len(html):,} bytes")
print(f"Output: {OUTPUT_PATH}")
