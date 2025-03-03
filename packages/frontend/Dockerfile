# Use Node.js as the base image
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Switch to root user for installation steps
USER root

# Copy package.json and package-lock.json first
COPY package.json package-lock.json* ./

# Install dependencies (using ci for more reliable builds)
RUN npm ci

# Copy the application code (excluding node_modules)
COPY . .
# The .dockerignore file should contain node_modules

# Build the SvelteKit app with adapter-static
RUN npm run build

# Set proper ownership of all files
RUN chown -R node:node /app

# Expose the preview port (default is 4173)
EXPOSE 4173

# Switch to non-root user for runtime
USER node

# Start the preview server
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0"]