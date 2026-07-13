# Python 3.13 slim 이미지 사용 (3.14가 없는 경우)
FROM python:3.13-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치 (pyproj를 위한 PROJ 라이브러리 필요)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    libproj-dev \
    proj-data \
    proj-bin && \
    rm -rf /var/lib/apt/lists/*

# uv 패키지 매니저 설치
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# 프로젝트 파일 복사
COPY pyproject.toml .
COPY src/ ./src/
COPY main.py .

# 의존성 설치
RUN /root/.local/bin/uv venv && \
    /root/.local/bin/uv pip install -e .

# 환경변수 기본값 설정 (플랫폼에서 override 가능)
ENV MCP_TRANSPORT=streamable-http
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000

# MCP 서버 포트 노출
EXPOSE 8000

# uvicorn을 직접 사용하여 Starlette 앱 실행 (MCP + /health)
CMD [".venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]