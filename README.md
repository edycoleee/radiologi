# Menyiapkan virtual environment Python dan menginstal Flask

Panduan singkat untuk membuat virtual environment, mengaktifkannya (macOS zsh),
dan menginstal `flask` serta `flask-restx`.

**Prasyarat**: Python 3.8+ terpasang. Periksa dengan:

```bash
python3 --version
```

1) Buat virtual environment di direktori proyek:

```bash
python3 -m venv .venv
```

2) Aktifkan virtual environment (macOS / zsh):

```bash
source .venv/bin/activate
```

3) Perbarui `pip` dan install paket yang diperlukan:

```bash
pip install --upgrade pip
pip install flask flask-restx
```

4) Verifikasi instalasi:

```bash
python -c "import flask, flask_restx; print('Flask', flask.__version__, 'Flask-RESTX', flask_restx.__version__)"
```

5) (Opsional) Simpan dependensi ke `requirements.txt`:

```bash
pip freeze > requirements.txt
```

6) Untuk keluar/menonaktifkan virtual environment:

```bash
deactivate
```

Jika anda ingin alternatif pengelola dependensi seperti `poetry` atau `pipenv`, beri tahu saya dan saya
akan tambahkan instruksi opsional untuk salah satu dari keduanya.

**Environment file (.env)**

A `.env` file is included for convenience with these variables (don't commit secrets in public repos):

```
AUTH_URL=https://api-satusehat.kemkes.go.id/oauth2/v1
BASE_URL=https://api-satusehat.kemkes.go.id/fhir-r4/v1
ORG_ID=100025702
CLIENT_ID=Gzn7YjXv0tQrNIlzgFliVAiBBkLLgVLEYsuXqmNVnwfapAxD
CLIENT_SECRET=fbPy8SDIkcrx1V7OaH1mHfx0xebHwBJBL4Fw8gW0Gi6MjIFrt9vWgW7NOIVNibGt
```

Instruksi singkat untuk menjalankan:

```bash
# Buat & aktifkan virtualenv (jika belum):
python3 -m venv .venv
 # Windows: python -m venv .venv
source .venv/bin/activate
 # Windows: .venv\Scripts\activate

# Pasang dependensi:
pip install --upgrade pip
pip install -r requirements.txt

# Jalankan server:
python app.py

# Swagger UI: http://127.0.0.1:5000/api/docs
```

Catatan: `.env` dimuat otomatis oleh `app.py` (menggunakan `python-dotenv`). Untuk keamanan, pertimbangkan menyimpan `CLIENT_SECRET` di vault/secret manager saat deploy.


=============================


