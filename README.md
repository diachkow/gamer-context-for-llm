# Gamer Context for LLM

This application allows users to create a context that can later be shared with LLM on your Steam game library.

## Running locally

1. Install [`concurrently`](https://www.npmjs.com/package/concurrently) node package globally to run development server easier:
```shell
npm install -g concurrently
```
2. Install [`tailwindcss`](https://tailwindcss.com/) CLI:
```shell
npm install -g @tailwindcss/cli
```
3. Install project dependencies with `uv`. Make sure that tool is [installed](https://docs.astral.sh/uv/getting-started/installation/):
```shell
uv sync
```
4. Then, run `uvicorn` server for backend [Starlette](https://www.starlette.io/) application and [`tailwindcss`](https://tailwindcss.com/) local server:
```shell
npx concurrently \
    "uv run uvicorn --host 0.0.0.0 --port 8000 src.app:app --reload --reload-dir=src/" \
    "npx tailwindcss -i src/static/input.css -o src/static/output.css --watch"
```
