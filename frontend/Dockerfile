FROM node:20-alpine

# Use /build to match your previous working setup
WORKDIR /build

# Copy package files
COPY package*.json ./

# Install dependencies (including vite)
RUN npm install

# Copy source code
COPY . .

# Build production bundle (creates /build/dist)
RUN npm run build

# Expose Railway's port
EXPOSE $PORT

# Run vite preview (automatically serves from /build/dist)
CMD ["sh", "-c", "vite preview --host 0.0.0.0 --port $PORT"]