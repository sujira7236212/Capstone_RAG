"""python -m service: the feedback service on 127.0.0.1 only (see service/app.py)."""
import logging
import os

import uvicorn

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
uvicorn.run("service.app:app", host="127.0.0.1", port=int(os.environ.get("FEEDBACK_PORT") or 8100),
            access_log=False)
