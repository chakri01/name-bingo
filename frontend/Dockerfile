FROM node:20-alpine

WORKDIR /build

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

EXPOSE $PORT

# Use npm run to execute the preview script
CMD ["npm", "run", "preview"]