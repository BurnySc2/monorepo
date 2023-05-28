# Install python / backend
cd burny_common
poetry install
cd ../discord_bot
poetry install
cd ../fastapi_server
poetry install
cd ../python_examples
poetry install
# Install frontend
cd ../bored_gems
npm install
cd ../replay_comparer
npm install
cd ../supabase_stream_scripts
npm install
cd ../svelte_frontend
npm install
