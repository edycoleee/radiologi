# Gunakan image python yang ramping
FROM python:3.10-slim

# Instal dependencies sistem (DCMTK untuk dcmodify & storescu)
RUN apt-get update && apt-get install -y \
    dcmtk \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Buat folder log dan temporary
RUN mkdir -p /app/logs /tmp/dicom_gateway_tmp

# Copy requirements terlebih dahulu (optimasi cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh kode aplikasi
COPY . .

# Expose port Flask
EXPOSE 5000

# Jalankan aplikasi
CMD ["python", "app.py"]