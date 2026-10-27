#!/bin/bash
# Azure App Service Linux Startup Script
echo "Starting StockQuote AI Backend..."
gunicorn -c gunicorn_conf.py main:app
