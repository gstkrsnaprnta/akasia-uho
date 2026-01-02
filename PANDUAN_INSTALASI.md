# 📚 PANDUAN INSTALASI AKASIA v2.0

Panduan lengkap untuk menjalankan aplikasi Chatbot AKASIA setelah mengekstrak file ZIP.

---

## 📋 Prasyarat

Sebelum menjalankan AKASIA, pastikan komputer Anda sudah terinstall:

| Software | Versi Minimum | Link Download |
|----------|---------------|---------------|
| **Python** | 3.10+ | [python.org/downloads](https://www.python.org/downloads/) |
| **Node.js** | 18+ | [nodejs.org](https://nodejs.org/) |

### Cara Cek Versi

Buka Terminal (Mac/Linux) atau Command Prompt (Windows), lalu ketik:

```bash
python3 --version   # Harus 3.10 atau lebih tinggi
node --version      # Harus 18 atau lebih tinggi
```

---

## 🚀 Langkah Instalasi

### Langkah 1: Ekstrak File ZIP

```bash
unzip chatbot_uho_v2.0_YYYYMMDD.zip
cd chatbot_uho
```

> 💡 Ganti `YYYYMMDD` dengan tanggal file ZIP Anda

---

### Langkah 2: Setup Otomatis

#### Mac / Linux:
```bash
chmod +x setup.sh
./setup.sh
```

#### Windows (Manual):
```bash
# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
venv\Scripts\activate

# Install dependensi Python
pip install -r requirements.txt

# Salin file environment
copy .env.example .env
```

---

### Langkah 3: Jalankan Backend

Buka **Terminal 1** dan jalankan:

#### Mac / Linux:
```bash
source venv/bin/activate
python api.py
```

#### Windows:
```bash
venv\Scripts\activate
python api.py
```

✅ **Sukses jika muncul:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### Langkah 4: Jalankan Frontend

Buka **Terminal 2 (baru)** dan jalankan:

```bash
cd rag-app
npm install
npm run dev
```

✅ **Sukses jika muncul:**
```
  ▲ Next.js 15.x.x
  - Local:        http://localhost:3000
```

---

## 🌐 Akses Aplikasi

Buka browser dan akses:

| URL | Halaman | Fungsi |
|-----|---------|--------|
| http://localhost:3000 | 🏠 Landing Page | Halaman utama/pembuka |
| http://localhost:3000/chat | 💬 Chat | Tanya jawab dengan AI |
| http://localhost:3000/admin | 📊 Admin | Upload dokumen, lihat statistik |

---

## 📄 Menambah Dokumen PDF

### Cara 1: Letakkan di Folder `data/`

1. Salin file PDF ke folder `data/`
2. Restart backend (Ctrl+C lalu jalankan ulang `python api.py`)
3. Dokumen otomatis ter-index

### Cara 2: Via Admin Panel

1. Buka http://localhost:3000/admin
2. Scroll ke bagian "Knowledge Base Manager"
3. Drag & drop file PDF atau klik untuk upload
4. Tunggu proses indexing selesai

---

## ⚠️ Troubleshooting

### ❌ Port 8000 sudah digunakan

**Mac/Linux:**
```bash
lsof -ti :8000 | xargs kill -9
```

**Windows:**
```bash
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F
```

---

### ❌ npm: command not found

Node.js belum terinstall. Download dari [nodejs.org](https://nodejs.org/)

---

### ❌ pip: command not found

Python belum terinstall dengan benar. Download dari [python.org](https://python.org)

---

### ❌ ModuleNotFoundError

Virtual environment belum aktif. Aktifkan dulu:
```bash
# Mac/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

---

### ❌ Frontend tidak bisa connect ke backend

1. Pastikan backend berjalan di Terminal 1
2. Cek apakah muncul error di Terminal 1
3. Pastikan URL backend: `http://localhost:8000`

---

## 🔑 Konfigurasi API Key

File `.env` sudah berisi API key demo. Jika ingin menggunakan API key sendiri:

1. Buka [console.groq.com](https://console.groq.com)
2. Buat akun dan generate API key
3. Edit file `.env`:
   ```
   GROQ_API_KEY=gsk_your_api_key_here
   ```

---

## 📞 Bantuan

Jika mengalami kendala, hubungi:
- **Developer**: Gusti Krisna Pranata
- **GitHub**: [github.com/gstkrsnaprnta/akasia-uho](https://github.com/gstkrsnaprnta/akasia-uho)

---

**AKASIA v2.0** - Asisten Akademik Berbasis AI untuk Universitas Halu Oleo 🎓
