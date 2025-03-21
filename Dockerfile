FROM python:3.9-slim

WORKDIR /app

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create a volume for SQLite database file
VOLUME /app/data

# Expose port for API
EXPOSE 8000

# Initialize the database and seed with sample data
RUN python seed_database.py

# Run the API server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"] 