FROM python:3.14.7-slim-trixie

RUN mkdir -p /app/cfg

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python3"]
CMD ["-u", "app.py"]
