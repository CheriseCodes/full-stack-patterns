#!/bin/bash
if [ "$APP_TYPE" = "frontend" ]; then
  cd fastapi-nextjs-low-cost-cloud/frontend
  npm install
  npm run build
  npm start
elif [ "$APP_TYPE" = "backend" ]; then
  cd fastapi-nextjs-low-cost-cloud/backend
  pip install -r requirements.txt
  uvicorn main:app --host 0.0.0.0 --port $PORT
fi