FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

# Install pip requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Set timezone
ENV TZ="America/Edmonton"

# Start the bot
CMD ["python", "main.py"]
