FROM python:3.12.4-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY ./requirements.txt /app/requirements.txt

RUN apt-get update \
    && apt-get install gcc curl -y \
    && apt-get clean

RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code to the container
COPY . /app/

# Start the FastAPI application
CMD ["python", "-m", "src.main"]