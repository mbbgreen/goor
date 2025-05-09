FROM python:3.10-slim

# نصب پیش‌نیازهای سیستمی (در صورت نیاز)
RUN apt-get update && \
    apt-get install -y curl libgl1 libglib2.0-0 libsm6 libxext6 && \
    rm -rf /var/lib/apt/lists/*

# کپی و نصب بسته‌ها
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# کپی کد و راه‌اندازی
COPY . /app
CMD ["python", "main.py"]
