import os

port = os.getenv("PORT", "8000")
bind = f"0.0.0.0:{port}"
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"
keepalive = 120
timeout = 600
accesslog = "-"
errorlog = "-"
loglevel = "info"
