# Langkah 1: Tentukan dasar Python
FROM python:3.9-slim

# Langkah 2: Buat direktori kerja
WORKDIR /app

# Langkah 3: Salin file daftar library
COPY requirements.txt .

# Langkah 4: WAJIB INSTALL library
RUN pip install --no-cache-dir -r requirements.txt

# Langkah 5: Salin semua sisa file kode
COPY . .
