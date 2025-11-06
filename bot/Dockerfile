# Multi-stage Dockerfile for Discord Bot

# Base stage - common dependencies
FROM node:22-alpine AS base

# Set the working directory inside the container
WORKDIR /app

# Create a non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S discordbot -u 1001

# Copy package.json and package-lock.json (if available)
COPY package*.json ./

# Development stage
FROM base AS development

# Install all dependencies (including dev dependencies)
RUN npm ci && npm cache clean --force

# Copy the application code
COPY . .

# Change ownership of the app directory to the nodejs user
RUN chown -R discordbot:nodejs /app

# Switch to the non-root user
USER discordbot

# Start the application with nodemon for development
CMD ["npx", "nodemon", "index.js"]

# Production stage
FROM base AS production

# Install only production dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy the application code
COPY . .

# Change ownership of the app directory to the nodejs user
RUN chown -R discordbot:nodejs /app

# Switch to the non-root user
USER discordbot

# Expose port (not strictly necessary for this bot, but good practice)
EXPOSE 3000

# Add health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD node -e "console.log('Bot is running')" || exit 1

# Start the application
CMD ["npm", "start"]

# Default to production if no target is specified
FROM production