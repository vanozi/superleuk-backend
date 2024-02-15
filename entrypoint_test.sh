#!/bin/bash

# Start Uvicorn in the background
uvicorn app.main:app --host 0.0.0.0 --port 8004 &

# Wait for the server to be up and running
while ! 2>/dev/null </dev/tcp/localhost/8004; do
    sleep 0.1 # wait for 1/10 of the second before checking again
done

# Run Aerich commands
aerich init -t app.db.TORTOISE_ORM
aerich init-db
aerich migrate
aerich upgrade

# insert testdata in the database
python ./db/python_scripts/setup_roles.py

# Keep the script running to keep the container alive
wait
