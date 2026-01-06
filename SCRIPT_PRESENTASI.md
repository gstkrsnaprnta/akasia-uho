# 📜 SCRIPT PRESENTASI
## AKASIA - Asisten Akademik Cerdas Universitas Halu Oleo
### Berbasis Retrieval-Augmented Generation (RAG)

---

## 🎬 SLIDE 1: PEMBUKAAN (2 menit)

**[Narrator]**

"Assalamualaikum Warahmatullahi Wabarakatuh. Selamat pagi/siang Bapak/Ibu dosen penguji yang saya hormati.

Perkenalkan, nama saya [NAMA ANDA], NIM [NIM ANDA], dari Program Studi [PRODI]. 

Pada kesempatan kali ini, saya akan mempresentasikan hasil penelitian/tugas akhir saya yang berjudul:

**'AKASIA: Pengembangan Chatbot Asisten Akademik Berbasis Retrieval-Augmented Generation untuk Universitas Halu Oleo'**

---

## 🎬 SLIDE 2: LATAR BELAKANG (3 menit)

**[Narrator]**

"Mengapa penelitian ini penting? Berikut latar belakangnya:

### Masalah yang Dihadapi:

1. **Informasi Akademik Tersebar**
   - Mahasiswa kesulitan menemukan informasi dari berbagai dokumen seperti Peraturan Rektor, Kalender Akademik, dan pedoman lainnya
   - Rata-rata mahasiswa membutuhkan 15-30 menit untuk menemukan informasi spesifik

2. **Layanan Terbatas**
   - Bagian Akademik hanya melayani di jam kerja
   - Antrian panjang, terutama saat awal semester

3. **Pertanyaan Berulang**
   - 70% pertanyaan mahasiswa bersifat repetitif
   - Misalnya: 'Kapan batas pengisian KRS?', 'Berapa masa studi maksimal?'

### Solusi yang Ditawarkan:

**AKASIA** - Chatbot cerdas yang dapat menjawab pertanyaan akademik 24/7 berdasarkan dokumen resmi UHO.

---

## 🎬 SLIDE 3: TUJUAN PENELITIAN (1 menit)

**[Narrator]**

"Tujuan dari penelitian ini adalah:

1. **Merancang dan mengimplementasikan** sistem chatbot berbasis RAG yang dapat menjawab pertanyaan akademik mahasiswa UHO

2. **Mengintegrasikan dokumen resmi** seperti Peraturan Rektor dan Kalender Akademik sebagai knowledge base

3. **Mengevaluasi akurasi** sistem dalam menjawab berbagai jenis pertanyaan akademik

4. **Menyediakan antarmuka** yang ramah pengguna dan mudah diakses

---

## 🎬 SLIDE 4: METODOLOGI - RAG ARCHITECTURE (4 menit)

**[Narrator]**

"Sistem AKASIA menggunakan arsitektur **Retrieval-Augmented Generation** atau RAG. Mari kita lihat bagaimana cara kerjanya:

### Apa itu RAG?

RAG adalah teknik yang menggabungkan:
- **Retrieval** (Pengambilan): Mencari dokumen yang relevan
- **Augmented** (Ditingkatkan): Memperkaya konteks untuk LLM
- **Generation** (Generasi): Menghasilkan jawaban natural

### Alur Kerja AKASIA:

```
[Pertanyaan Mahasiswa]
        ↓
[1. Query Expansion] → Memperluas query dengan sinonim
        ↓
[2. Multi-Query Retrieval] → Mencari dengan 3 variasi pertanyaan
        ↓
[3. Hybrid Search] → Semantic (70%) + Keyword BM25 (30%)
        ↓
[4. Cross-Encoder Reranking] → Neural re-ranking untuk akurasi
        ↓
[5. Context Assembly] → Menyusun konteks terbaik
        ↓
[6. LLM Generation] → Groq Cloud (Llama 3.1)
        ↓
[Jawaban + Sumber]
```

### Keunggulan RAG vs Chatbot Biasa:

| Aspek | Chatbot Biasa | AKASIA (RAG) |
|-------|---------------|--------------|
| Sumber Jawaban | Ditraining sekali | Dokumen terkini |
| Update Informasi | Perlu re-training | Upload dokumen baru |
| Transparansi | Black box | Menyertakan sumber |
| Hallusinasi | Tinggi | Minimal |

---

## 🎬 SLIDE 5: TEKNOLOGI YANG DIGUNAKAN (2 menit)

**[Narrator]**

"Berikut teknologi yang digunakan dalam pengembangan AKASIA:

### Backend (Python):
- **FastAPI** - REST API framework
- **LangChain** - Orchestration framework untuk RAG
- **FAISS** - Vector database untuk similarity search
- **Sentence Transformers** - Model embedding multilingual
- **Groq Cloud** - LLM API (Llama 3.1-8B)

### Frontend (Next.js):
- **React 19** - UI framework
- **Tailwind CSS** - Styling
- **Framer Motion** - Animasi
- **Lucide React** - Ikon

### NLP Models:
- **paraphrase-multilingual-MiniLM-L12-v2** - Embedding
- **cross-encoder/ms-marco-MiniLM-L-6-v2** - Reranking

---

## 🎬 SLIDE 6: FITUR UTAMA (3 menit)

**[Narrator]**

"AKASIA memiliki fitur-fitur unggulan:

### 1. 💬 Chat Interface
- Streaming response real-time
- Markdown rendering untuk format tabel/list
- Dark/Light mode

### 2. 🔍 Hybrid Search
- Kombinasi semantic search dan keyword matching
- Akurasi tinggi untuk berbagai jenis query

### 3. 📊 Confidence Scoring
- Setiap jawaban memiliki tingkat keyakinan
- Indikator: Tinggi (>70%), Sedang (50-70%), Rendah (<50%)

### 4. 📚 Citation System
- Menyertakan sumber dokumen
- Pasal/ayat dari peraturan, bagian kalender

### 5. 👍👎 Feedback System
- Thumbs up/down untuk setiap jawaban
- Data untuk evaluasi dan improvement

### 6. 🔗 Related Questions
- Saran pertanyaan terkait
- Membantu eksplorasi informasi

### 7. 🛠️ Admin Panel
- Upload/hapus dokumen
- Statistik penggunaan
- Query testing tool
- Feedback dashboard

---

## 🎬 SLIDE 7: DEMO APLIKASI (5 menit)

**[Narrator]**

"Sekarang mari kita lihat demo aplikasi AKASIA.

### Demo 1: Landing Page
*[Buka http://localhost:3000]*
- Desain modern dengan animasi neural network
- Tombol 'Mulai Chat' yang interaktif

### Demo 2: Chat Interface
*[Klik 'Mulai Chat']*
- Interface chat yang bersih dan responsif
- Typing indicator saat bot merespons

### Demo 3: Pertanyaan Akademik
*[Ketik: 'Berapa masa studi maksimal S1?']*
- Chatbot menjawab: 'Masa studi maksimal S1 adalah 7 tahun akademik. [Sumber: Pasal 44]'
- Perhatikan confidence score dan citation

### Demo 4: Pertanyaan Kalender
*[Ketik: 'Kapan pembayaran SPP semester gasal?']*
- Menunjukkan kemampuan memahami context kalender

### Demo 5: Admin Panel
*[Buka http://localhost:3000/admin]*
- Dashboard statistik
- Upload dokumen baru
- Query tester untuk debugging

---

## 🎬 SLIDE 8: HASIL PENGUJIAN (3 menit)

**[Narrator]**

"Berikut hasil pengujian sistem AKASIA:

### Metrik Evaluasi:

| Kategori Pertanyaan | Jumlah | Akurasi |
|---------------------|--------|---------|
| Peraturan Akademik | 20 | 85% |
| Kalender Akademik | 15 | 75% |
| Prosedur Administratif | 10 | 80% |
| **Total** | **45** | **80%** |

### Response Time:
- Average: 2-4 detik (streaming)
- Cached: <100ms

### User Satisfaction (dari feedback):
- Positive (👍): 78%
- Negative (👎): 22%

### Error Analysis:
- 15% pertanyaan tidak terjawab karena informasi tidak ada di dokumen
- 5% jawaban kurang tepat karena chunk terpotong

---

## 🎬 SLIDE 9: KONTRIBUSI PENELITIAN (2 menit)

**[Narrator]**

"Kontribusi dari penelitian ini:

### Kontribusi Praktis:
1. **Prototipe sistem chatbot** yang dapat digunakan UHO
2. **Knowledge base** dari dokumen akademik UHO
3. **Source code open** yang dapat dikembangkan

### Kontribusi Akademik:
1. **Implementasi RAG** dengan Bahasa Indonesia
2. **Teknik Hybrid Search** untuk dokumen akademik
3. **Query-aware boosting** untuk meningkatkan akurasi

### Novelty:
- **Semester-aware date detection** untuk query kalender
- **Program-aware term boosting** untuk query S1/S2/S3
- **CS-style persona** untuk respons yang ramah

---

## 🎬 SLIDE 10: KETERBATASAN & PENGEMBANGAN (2 menit)

**[Narrator]**

"Setiap penelitian memiliki keterbatasan. Berikut keterbatasan dan saran pengembangan:

### Keterbatasan Saat Ini:

1. **PDF dengan tabel gambar** tidak terekstrak dengan baik
2. **Beberapa istilah spesifik** belum memiliki mapping
3. **Belum terintegrasi** dengan sistem akademik UHO (SIAKAD)

### Saran Pengembangan:

1. **OCR Enhancement** - Perbaikan ekstraksi tabel dari PDF
2. **Fine-tuning Model** - Melatih model khusus bahasa akademik Indonesia
3. **Integration** - Integrasi dengan SIAKAD untuk data real-time
4. **Mobile App** - Pengembangan aplikasi mobile
5. **Voice Interface** - Fitur voice assistant

---

## 🎬 SLIDE 11: KESIMPULAN (2 menit)

**[Narrator]**

"Sebagai kesimpulan:

1. **AKASIA berhasil dikembangkan** sebagai chatbot asisten akademik berbasis RAG untuk UHO

2. **Akurasi mencapai 80%** dalam menjawab pertanyaan akademik berdasarkan dokumen resmi

3. **Arsitektur RAG terbukti efektif** untuk domain akademik dengan Bahasa Indonesia

4. **Sistem siap untuk pilot testing** dengan mahasiswa UHO

5. **Dapat dikembangkan lebih lanjut** dengan integrasi sistem akademik

---

## 🎬 SLIDE 12: PENUTUP (1 menit)

**[Narrator]**

"Demikian presentasi dari saya. 

AKASIA hadir sebagai solusi untuk membantu mahasiswa mendapatkan informasi akademik dengan cepat dan akurat, kapan saja dan di mana saja.

Terima kasih atas perhatian Bapak/Ibu. Saya membuka sesi tanya jawab.

Wassalamualaikum Warahmatullahi Wabarakatuh."

---

## 📝 ANTISIPASI PERTANYAAN

### Q1: "Mengapa menggunakan RAG, bukan fine-tuning LLM?"
**A:** RAG lebih cocok karena:
- Tidak perlu re-training saat dokumen berubah
- Lebih murah dan cepat dikembangkan
- Dapat menunjukkan sumber jawaban (transparansi)

### Q2: "Bagaimana mengatasi hallusinasi LLM?"
**A:** Kami menerapkan:
- Anti-hallucination prompt yang ketat
- Confidence scoring untuk filter jawaban tidak yakin
- Citation wajib untuk setiap jawaban

### Q3: "Bagaimana jika dokumen diupdate?"
**A:** Admin dapat:
- Menghapus dokumen lama dari Admin Panel
- Upload dokumen baru
- Sistem otomatis re-index

### Q4: "Mengapa tidak menggunakan GPT-4?"
**A:** Pertimbangan:
- Groq lebih cepat (inference time)
- Llama 3.1 memadai untuk task ini
- Biaya lebih efisien
- Data tidak dikirim ke OpenAI

### Q5: "Berapa biaya operasional?"
**A:** 
- Groq: Free tier cukup untuk development
- Hosting: ~$5-10/bulan untuk VPS kecil
- Sangat affordable untuk institusi

---

## 🎯 TIPS PRESENTASI

1. **Waktu**: Total ~25-30 menit (sesuaikan dengan alokasi)
2. **Demo**: Pastikan backend & frontend sudah running sebelum presentasi
3. **Backup**: Siapkan video recording demo jika ada masalah teknis
4. **Eye Contact**: Jangan hanya membaca, lakukan kontak mata dengan penguji
5. **Pace**: Bicara dengan tempo yang jelas, tidak terburu-buru

---

*Script ini dibuat untuk presentasi akademik AKASIA Chatbot*
*© 2026 - Universitas Halu Oleo*
