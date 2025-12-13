# --- Build Stage ---
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# --- Run Stage ---
FROM node:20-alpine

WORKDIR /app
RUN npm install -g serve

COPY --from=builder /app/dist ./dist

ENV PORT=5173

EXPOSE 5173

CMD ["serve", "-s", "dist", "-l", "5173"]
