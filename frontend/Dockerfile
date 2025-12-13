# --- Build Stage ---
FROM node:20-alpine AS builder

WORKDIR /app

# Copy ONLY the frontend package.json
COPY ./frontend/package*.json ./

RUN npm install

# Copy the rest of the frontend source
COPY ./frontend .

RUN npm run build

# --- Run Stage ---
FROM node:20-alpine

WORKDIR /app
RUN npm install -g serve

COPY --from=builder /app/dist ./dist

ENV PORT=5173
EXPOSE 5173

CMD ["serve", "-s", "dist", "-l", "5173"]
