# fastapi-svelte-typescript-template

# Requirement

-   Python 3.7 or newer
-   Node.js 12+

# Installation

Install node and python 3.7+

```
pip install poetry --user
poetry install
npm install
```

# Start frontend

```
npm run dev
```

Then to go http://localhost:3000 to preview the page

# Deploy

Create the front end and host it somewhere (e.g. github pages)

```
npm run build
```

# Functionality

## Requests

[x] Communicate between front and backend

[x] Accept file download (sent via backend)

[ ] Accept file upload

[ ] User register

[ ] User login

[ ] Use cookies to store login? https://sanic.readthedocs.io/en/latest/sanic/cookies.html

# Tests

Run python backend tests via

```
poetry run pytest test_backend --benchmark-skip
```

and Javascript unit tests via

```
npm run test
```

[x] How to test a webserver?
Run frontend tests via

```
poetry run pytest test_frontend --benchmark-skip --headless
```

You can benchmark tests with

```
poetry run pytest test_frontend --benchmark-only
```

# Upgrade packages to latest major version

```
npx npm-check-updates -u
```

Or run

```
npm run update
```

to update versions, reinstall node_modules from scratch

# Autoformatting

```
npm run format
```
