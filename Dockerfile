FROM ubuntu:latest

# نصب پایتون و bash و سایر وابستگی‌ها
RUN apt-get update && \
    apt-get install -y python3-opencv libgl1 libglib2.0-0 bash

# کپی فایل پایتون به کانتینر (اگر فایل داری)
COPY . /app
WORKDIR /app

# اجرای فایل پایتون یا هر اسکریپت دیگری
CMD ["python3", "main.py"]
