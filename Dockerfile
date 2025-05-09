FROM ubuntu:latest

# نصب Python و pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip bash libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# کپی کردن requirements.txt و نصب پکیج‌ها
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# کپی سایر فایل‌ها
COPY . /app

WORKDIR /app

# اجرای فایل پایتون
CMD ["python3", "main.py"]
