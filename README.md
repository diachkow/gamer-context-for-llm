# Gamer Context for LLM

This application allows users to create a context that can later be shared with LLM on your Steam game library.

## Running locally

Install [`concurrently`](https://www.npmjs.com/package/concurrently) node package globally to run development server easier:

```shell
npm install -g concurrently
```

Install project dependencies with `uv`. Make sure that tool is [installed](https://docs.astral.sh/uv/getting-started/installation/):

```shell
uv sync
```

Then, run `uvicorn` server for backend [Starlette](https://www.starlette.io/) application and [`tailwindcss`](https://tailwindcss.com/) local server:

```shell
npx concurrently \
    "uv run uvicorn --host 0.0.0.0 --port 8000 src.app:app --reload --reload-dir=src/" \
    "bin/tailwindcss -i src/static/input.css -o src/static/output.css --watch"
```
