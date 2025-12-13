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

# Serve DIST using Vite Preview (production mode)
#CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "${PORT}"]
CMD ["npm", "run", "start"]