FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm install

# Copy application source code
COPY . .

# Expose Next.js default port
EXPOSE 3000

# Disable telemetry
ENV NEXT_TELEMETRY_DISABLED 1

# Start the Next.js development server
# (Using dev server so changes made to your mounted /src volumes instantly reload)
CMD ["npm", "run", "dev"]
