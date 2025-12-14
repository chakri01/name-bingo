FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:20-alpine

WORKDIR /app

RUN npm install -g serve@14.2.1

COPY --from=build /app/dist ./dist

# Explicitly bind to 0.0.0.0 and use PORT
CMD sh -c "serve dist -l 0.0.0.0:${PORT:-3000} -n"
