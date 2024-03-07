# Use the official Python image as base
FROM python:3.8-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install required dependencies
RUN pip install --no-cache-dir pyrogram pymongo

# Expose the port the bot runs on
EXPOSE 8080

# Run the bot
CMD ["python", "bot.py"]
