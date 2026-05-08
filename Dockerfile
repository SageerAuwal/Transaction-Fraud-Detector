# Use Python 3.10
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create data directory for SQLite
RUN mkdir -p data && chmod 777 data

# Expose the port FastAPI runs on
EXPOSE 7860

# Generate data and train the AI model (Ensures model exists on startup)
RUN python generate_data.py && python train.py

# Run the application
# Note: Hugging Face expects the app to run on port 7860
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
