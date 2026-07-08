# Use Python 3.11 full image
FROM python:3.11

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Run the application (seed data first)
CMD sh -c "python seed_data.py && flask run --host=0.0.0.0"
