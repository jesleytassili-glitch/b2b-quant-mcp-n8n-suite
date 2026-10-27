FROM python:3.11-slim
WORKDIR /app
COPY mcp_server.py pyproject.toml README.md glama.json ./
ENTRYPOINT ["python", "mcp_server.py"]
