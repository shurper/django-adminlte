FROM python:3.10

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install PostgreSQL client
RUN apt-get update && apt-get install -y postgresql-client

# Create log directory
RUN mkdir /logs

COPY requirements.txt .
# install python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY wait_for_db.sh /wait_for_db.sh
RUN chmod +x /wait_for_db.sh

# Указываем стандартный порт
EXPOSE 8000
