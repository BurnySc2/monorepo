# A todo app using nim webserver and htmx frontend


Project is for now `on hold` because nim's debugging tools are lacking. Errors in threads are not reflected by prologue. Dict/map only supports a single type at a time.

# Nim installation
```sh
nimble install mustache
nimble install prologue
```

Run with
```sh
nim c -r main.nim
```

# Frontend
Run with
```sh
npx servor --browse --reload frontend
```
