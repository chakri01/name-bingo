FROM node:20-alpine AS builder

WORKDIR /build
RUN ls -la
RUN pwd

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM node:20-alpine

WORKDIR /app
RUN npm install -g serve

COPY --from=builder /build/dist ./dist

EXPOSE $PORT

CMD sh -c "serve -s dist -l $PORT"