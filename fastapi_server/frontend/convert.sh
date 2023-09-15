# Run by netlify to remap all urls to the correct domain
sed -i "s|{{ server_url }}|$BACKEND_SERVER_URL|g" index.html
sed -i "s|{{ server_url }}|$BACKEND_SERVER_URL|g" chat/index.html
sed -i "s|{{ server_url }}|$BACKEND_SERVER_URL|g" todo/index.html
sed -i "s|{{ server_url }}|$BACKEND_SERVER_URL|g" login/index.html
sed -i "s|{{ server_url }}|$BACKEND_SERVER_URL|g" logout/index.html
