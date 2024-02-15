#!/bin/bash

# Run Aerich commands
aerich init -t app.db.TORTOISE_ORM
aerich init-db
aerich migrate
aerich upgrade

# insert testdata in the database
python ./db/python_scripts/setup_roles.py

# install debugpy and start uvicorn in debug mode
pip install debugpy
python -m debugpy --wait-for-client --listen 0.0.0.0:5678 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8004
