# Requirements:
# pip install poetry --no-cache-dir
# poetry install --no-dev
# cd ../$FRONTEND_FOLDER
# npm install --omit=dev
set -e
BACKEND_FOLDER=fastapi_server
FRONTEND_FOLDER=svelte_frontend

# Start backend
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 2>/dev/null >&2 &
BACKEND_PROCESS_ID=$!

# Start frontend
cd ../$FRONTEND_FOLDER
npm run dev >/dev/null &

# Wait for servers to start
sleep 1

# Run integration test
cd ../$BACKEND_FOLDER
poetry run pytest --browser chromium test_integration

# Kill process ids to clear up ports
killall node
kill -9 $BACKEND_PROCESS_ID
