FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Build will use VITE_API_URL from Railway env vars
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# --- Run Stage ---
FROM node:20-alpine

WORKDIR /app

# Install serve globally
RUN npm install -g serve

# Copy built files
COPY --from=builder /app/dist ./dist

# Railway provides PORT automatically
EXPOSE $PORT

# Serve on Railway's PORT
CMD sh -c "serve -s dist -l $PORT"