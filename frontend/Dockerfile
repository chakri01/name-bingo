FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

# Build production files
RUN npm run build

# Railway provides PORT automatically
ENV PORT=5173

EXPOSE 5173

# Use Vite preview for production
CMD ["sh", "-c", "npm run start -- --host 0.0.0.0 --port ${PORT}"]
