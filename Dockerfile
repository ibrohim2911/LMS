# Python'ning yengil rasmiy versiyasidan foydalanamiz
FROM python:3.10-slim-buster

# Konteyner ichida ishchi papkani ko'rsatamiz
WORKDIR /app

# Python optimizatsiyasi uchun muhit o'zgaruvchilari
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Kerakli kutubxonalarni o'rnatish
# Eslatma: loyihangizda requirements.txt fayli bo'lishi shart
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Loyihaning barcha fayllarini konteynerga ko'chiramiz
COPY . /app/

# Odatiy holatda Django serverni ishga tushirish
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
