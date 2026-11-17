FROM node:20-alpine
WORKDIR /app
COPY frontend/package.json ./
RUN npm install
COPY frontend/ .
ARG NEXT_PUBLIC_API=http://localhost:8000
ENV NEXT_PUBLIC_API=$NEXT_PUBLIC_API
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
