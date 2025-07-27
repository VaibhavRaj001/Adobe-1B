# Use a specific, slim, and platform-compliant base image
FROM --platform=linux/amd64 python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file first
COPY requirements.txt .

# Install CPU-only torch first
RUN pip install --no-cache-dir torch==2.0.1+cpu -f https://download.pytorch.org/whl/torch_stable.html

# Then install the rest
RUN pip install --no-cache-dir -r requirements.txt

# Copy local model (must be saved beforehand)
COPY ./models/all-MiniLM-L6-v2 ./models/all-MiniLM-L6-v2

# Copy application code
COPY . .

# Set entrypoint
CMD ["python", "app.py"]
