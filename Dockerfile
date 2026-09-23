FROM mcr.microsoft.com/playwright:v1.58.0-noble

WORKDIR /app

# Copy package files first for better layer caching
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy the rest of the project
COPY . .

# Default command — can be overridden
CMD ["npx", "playwright", "test"]