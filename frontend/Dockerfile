# frontend/Dockerfile 수정
FROM node:16

WORKDIR /app

# package.json만 복사하도록 변경
COPY package.json ./
RUN npm install

# 코드 복사 (개발 환경에서는 볼륨 마운트로 오버라이드)
COPY . .

# 개발 서버 실행
CMD ["npm", "start"]