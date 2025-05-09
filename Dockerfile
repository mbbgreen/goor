FROM python:3.10-slim

# نصب libGL برای opencv
RUN apt-get update && apt-get install -y libgl1 && rm -rf /var/lib/apt/lists/*

# نصب پکیج‌ها از requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی کردن کد
COPY . /app
WORKDIR /app

# اجرای بات
CMD ["python", "bot.py"]
