# Use official Node image
FROM node:20

# Set working directory
WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy the rest of the app
COPY . .

# Expose port 3000
EXPOSE 3000

# Start the app
# CMD ["npm", "run", "start"]

CMD ["npx", "vite", "--host", "0.0.0.0", "--port", "3000"]
