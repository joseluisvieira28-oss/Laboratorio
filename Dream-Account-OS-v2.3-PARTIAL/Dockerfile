FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY scripts ./scripts
RUN pip install --no-cache-dir .
RUN mkdir -p /var/data
EXPOSE 8080
CMD ["python", "/app/scripts/runtime_entrypoint.py"]
