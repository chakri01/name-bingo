FROM node:20-alpine

WORKDIR /build

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

EXPOSE $PORT

CMD ["npm", "run", "preview"]