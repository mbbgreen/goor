FROM ubuntu:latest

# 1. نصب Python، pip و ابزار venv
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv bash libgl1 libglib2.0-0 libsm6 libxext6 && \
    rm -rf /var/lib/apt/lists/*

# 2. ایجاد virtual environment و ارتقاء pip
WORKDIR /app
COPY requirements.txt /app/
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/python -m pip install --upgrade pip setuptools wheel

# 3. نصب بسته‌ها در محیط مجازی
RUN . /opt/venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

# 4. کپی باقی پروژه
COPY . /app

# 5. تنظیم PATH برای استفاده از venv به‌صورت پیش‌فرض
ENV PATH="/opt/venv/bin:$PATH"

# 6. اجرای برنامه
CMD ["python", "main.py"]
