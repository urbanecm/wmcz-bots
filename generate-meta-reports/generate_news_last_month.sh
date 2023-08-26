#!/bin/bash

source ~/venv/bin/activate
python3 ~/wmczbot/generate-meta-reports/generate_news.py $(date +%Y-%m -d 'last month')
