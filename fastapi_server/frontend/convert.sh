# Run by netlify to remap all urls to the correct domain
sed "s|{{ server_url }}|$BACKEND_SERVER_URL|g" index.html > index.html
sed "s|{{ server_url }}|$BACKEND_SERVER_URL|g" chat/index.html > chat/index.html
sed "s|{{ server_url }}|$BACKEND_SERVER_URL|g" todo/index.html > todo/index.html
