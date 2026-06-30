# Stage 1: build the React app into static files
FROM node:20-slim AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: serve those static files with a tiny production server
# (Vite's dev server isn't meant for this — 'serve' is a minimal,
# purpose-built static file server)
FROM node:20-slim
WORKDIR /app
RUN npm install -g serve
COPY --from=build /app/dist ./dist
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
