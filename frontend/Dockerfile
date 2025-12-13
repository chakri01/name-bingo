FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Build production bundle
RUN npm run build

# Railway sets PORT automatically
ENV PORT=5173

EXPOSE 5173

# run vite preview in production mode
CMD ["sh", "-c", "vite preview --host 0.0.0.0 --port ${PORT}"]