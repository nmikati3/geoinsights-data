# Use Python 3.12 slim image as base
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=True
ENV PYTHONPATH=/geoinsights_data

WORKDIR /geoinsights_data

COPY requirements.txt .

RUN groupadd -r geoinsights_data && \
    useradd -r -g geoinsights_data geoinsights_data && \
    # Install build dependencies for packages that need compilation (e.g., hdbscan)
    apt-get update && \
    apt-get upgrade -y --no-install-recommends && \
    apt-get install -y --no-install-recommends build-essential gcc g++ libgomp1 && \
    # Upgrade system pip to fix CVE-2025-8869
    pip install --upgrade pip && \
    # Create a virtual environment (uses ensurepip)
    python -m venv ./venv && \
    # Now safe to remove vulnerable bundled pip wheels
    rm -rf /usr/local/lib/python3.12/ensurepip/_bundled && \
    # Ensure venv uses the latest pip
    ./venv/bin/pip install --upgrade pip setuptools wheel && \
    ./venv/bin/pip install --no-cache-dir -r requirements.txt && \
    # Clean up build dependencies to reduce image size
    apt-get purge -y build-essential gcc g++ && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --chown=geoinsights_data:geoinsights_data . .

USER geoinsights_data

CMD ["/geoinsights_data/venv/bin/python", "geoinsights_data/join_datasets/join.py"]
