# SC2 Replay Comparer

It uses [Zephyrus sc2 replay plarser](https://github.com/ZephyrBlu/zephyrus-sc2-parser) to get the data from replays, then displays them in [highcharts](https://www.highcharts.com/).

# Live version

[Develop branch](https://replaycomparer.netlify.app)

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

# Update packages

```
npm run update
```

to update versions, reinstall node_modules from scratch

# Autoformatting

```
npm run format
```
