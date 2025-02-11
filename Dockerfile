FROM python:3.13.2-slim-bullseye AS BUILDER

# Add NodeSource repository and install Node.js 20
RUN apt-get update \
    && apt-get install -y ca-certificates curl gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

ENV UV_VERSION=0.5.29
ENV UV_COMPILE_BYTECODE=1
ENV UV_INSTALL_DIR="/usr/local/uv/"

# Download the latest installer
ADD https://astral.sh/uv/${UV_VERSION}/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh ./uv-installer.sh && rm ./uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="$PATH:$UV_INSTALL_DIR"

ARG RELEASE="unspecified-release"
ENV PYTHONPATH=/var/www/gamer-context

WORKDIR /var/www/gamer-context/

# Install project dependencies (Python)
COPY pyproject.toml uv.lock ./
RUN uv sync

# Copy the rest of the application
COPY . .

# Install node dependencies and build
RUN npm install
RUN npm run build

# ==========================
FROM python:3.13.2-slim-bullseye AS FINAL

ENV UV_INSTALL_DIR="/usr/local/uv/"
ENV PATH="$PATH:$UV_INSTALL_DIR"
ENV PYTHONPATH=/var/www/gamer-context

WORKDIR /var/www/gamer-context/

# Copy uv executables from builder
COPY --from=BUILDER ${UV_INSTALL_DIR} ${UV_INSTALL_DIR}

# Copy only necessary files from the builder
COPY --from=BUILDER /var/www/gamer-context/pyproject.toml /var/www/gamer-context/uv.lock ./
COPY --from=BUILDER /var/www/gamer-context/.venv ./.venv
COPY --from=BUILDER /var/www/gamer-context/src ./src

EXPOSE 8000

# Run application in production mode
CMD ["uv", "run", "uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
