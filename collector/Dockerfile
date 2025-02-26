# collector/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 코드 복사
COPY . .

# 출력 디렉토리 생성
RUN mkdir -p output

# 기본 명령 (수집 실행)
CMD ["python", "main.py"]
