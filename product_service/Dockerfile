FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY db.py .
COPY models.py .
COPY middleware.py .
COPY events.py .
EXPOSE 5001
CMD ["python", "app.py"]
