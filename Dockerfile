FROM ubuntu:latest

# 1. نصب Python3 و pip و bash و سایر وابستگی‌های سیستمی
RUN apt-get update && \
    apt-get install -y python3 python3-pip bash libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# 2. کپی فایل requirements.txt و نصب بسته‌های پایتون
WORKDIR /app
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt

# 3. کپی باقی فایل‌های پروژه
COPY . /app

# 4. پیش‌فرض اجرای اسکریپت
CMD ["python3", "main.py"]
