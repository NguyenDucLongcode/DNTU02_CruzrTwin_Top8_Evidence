FROM python:3.10-slim

# Cài đặt thư mục làm việc
WORKDIR /app

# Copy file requirements và cài đặt
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Cài đặt Docker CLI để gọi lệnh restart simulator
RUN apt-get update && apt-get install -y docker.io && rm -rf /var/lib/apt/lists/*

# Copy toàn bộ source code
COPY . .

# Expose port cho Dashboard Backend (Flask)
EXPOSE 5000

# Chạy server
CMD ["python", "src/fiware/webhook_receiver.py"]
