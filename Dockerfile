FROM node:18-alpine

# Cài đặt thư mục làm việc
WORKDIR /app

# Copy file package.json và cài đặt dependencies
COPY package*.json ./
RUN npm install

# Copy toàn bộ source code vào container
COPY . .

# Expose port cho Dashboard
EXPOSE 8000

# Chạy server Node.js
CMD ["npm", "start"]
