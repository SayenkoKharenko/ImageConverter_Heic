FROM python:3.12-slim

WORKDIR /app

RUN mkdir -p /app/output /app/upl /app/downl

# Install necessary packages
RUN apt-get update && apt-get install -y \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
COPY app.py ./

RUN pip3 install --no-cache-dir -r requirements.txt

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

EXPOSE 5000

CMD ["flask", "run"]
