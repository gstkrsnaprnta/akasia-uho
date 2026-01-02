"""
============================================
AKASIA v1.0 - RAG Engine
============================================
Retrieval-Augmented Generation Engine

File ini berisi mesin utama chatbot yang melakukan:
- Ekstraksi teks dari PDF (termasuk OCR untuk PDF scan)
- Chunking dan indexing dokumen ke FAISS vector database
- Multi-strategy retrieval (semantik, keyword, regulatory)
- Query processing dan streaming response ke LLM

Komponen Utama:
- RAGEngine: Kelas utama untuk semua operasi RAG
- _extract_pdf_text: Ekstraksi teks dengan fallback OCR
- create_vectorstore: Membuat/update index FAISS
- query_stream: Menjawab pertanyaan dengan streaming

Model yang digunakan:
- Embedding: paraphrase-multilingual-MiniLM-L12-v2
- LLM: Groq Llama 3.1 8B Instant
============================================
"""

import os
import json
import time
import re
from datetime import datetime
from groq import Groq
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()

# Konfigurasi path untuk penyimpanan data
FAISS_INDEX_PATH = "./faiss_index"      # Folder untuk index vektor FAISS
METADATA_FILE = "./documents_metadata.json"  # File metadata dokumen
DATA_FOLDER = "./data"                   # Folder dokumen PDF untuk auto-load

class RAGEngine:
    def __init__(self):
        self.embeddings = self._get_embeddings()
        self.vectorstore = self.load_existing_vectorstore()
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.llm_model = "llama-3.1-8b-instant"
        self.fallback_model = "llama-3.2-3b-preview"
        self.metadata = self.load_metadata()
        
        # Auto-load documents from data folder on startup
        self._auto_load_documents()
    
    def _get_embeddings(self):
        """Get embeddings model - use multilingual for Indonesian"""
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={'device': 'cpu'}
        )
    
    def _auto_load_documents(self):
        """Auto-load PDFs from data folder if not already indexed"""
        if not os.path.exists(DATA_FOLDER):
            os.makedirs(DATA_FOLDER, exist_ok=True)
            return
            
        pdf_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.pdf')]
        if not pdf_files:
            return
            
        print(f"Checking {len(pdf_files)} documents in {DATA_FOLDER} for auto-loading...")
        
        # Get list of already indexed files
        indexed_files = [d.get("filename") for d in self.metadata.get("documents", [])]
        
        files_to_load = []
        for pdf_file in pdf_files:
            if pdf_file not in indexed_files:
                files_to_load.append(pdf_file)
            else:
                print(f"  • Already indexed: {pdf_file}")
                
        if not files_to_load:
            print("All documents are up to date.")
            return
            
        print(f"Found {len(files_to_load)} new documents to index...")
        
        for pdf_file in files_to_load:
            try:
                print(f"  → Indexing: {pdf_file}...")
                pdf_path = os.path.join(DATA_FOLDER, pdf_file)
                text = self._extract_pdf_text(pdf_path)
                if text:
                    self.create_vectorstore(text, pdf_file, os.path.getsize(pdf_path))
                    print(f"  ✓ Successfully loaded: {pdf_file}")
            except Exception as e:
                print(f"  ✗ Failed to load {pdf_file}: {e}")
    
    def _extract_pdf_text(self, pdf_path):
        """Extract text from PDF with special handling for calendar tables and scanned documents"""
        filename = os.path.basename(pdf_path).lower()
        is_calendar = 'kalender' in filename or 'akademik' in filename
        
        text = ""
        
        # For calendar documents, try to extract tables as markdown
        if is_calendar:
            text = self._extract_tables_as_markdown(pdf_path)
            if text and len(text.strip()) > 200:
                return text
        
        # Standard text extraction
        # Method 1: Try pypdf
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except Exception:
            pass
        
        # Method 2: Try PyMuPDF if pypdf failed or returned little text
        if len(text.strip()) < 100:
            try:
                import fitz
                doc = fitz.open(pdf_path)
                text = ""
                for page in doc:
                    text += page.get_text() + "\n"
                doc.close()
            except Exception:
                pass
        
        # Method 3: OCR for scanned documents if still not enough text
        if len(text.strip()) < 100:
            print(f"Using OCR for scanned PDF: {pdf_path}")
            text = self._extract_with_ocr(pdf_path)
        
        return text.strip()
    
    def _extract_with_ocr(self, pdf_path):
        """Extract text from scanned PDF using OCR"""
        try:
            from pdf2image import convert_from_path
            import pytesseract
            
            # Convert PDF pages to images
            print("Converting PDF to images for OCR...")
            images = convert_from_path(pdf_path, dpi=200)
            
            all_text = []
            for i, image in enumerate(images):
                print(f"  OCR processing page {i+1}/{len(images)}...")
                # Run OCR with Indonesian language support
                page_text = pytesseract.image_to_string(image, lang='ind+eng')
                if page_text.strip():
                    all_text.append(f"=== Halaman {i+1} ===\n{page_text}")
            
            return "\n\n".join(all_text)
        except Exception as e:
            print(f"OCR extraction failed: {e}")
            return ""
    
    def _extract_tables_as_markdown(self, pdf_path):
        """Extract tables from PDF and convert to markdown format"""
        try:
            import fitz
            doc = fitz.open(pdf_path)
            all_text = []
            
            for page_num, page in enumerate(doc):
                # Get all text first
                page_text = page.get_text()
                all_text.append(f"=== Halaman {page_num + 1} ===\n{page_text}")
                
                # Try to find and extract tables
                try:
                    tables = page.find_tables()
                    for table in tables:
                        if table.row_count > 1:
                            # Convert table to markdown
                            md_table = "\n| " + " | ".join([str(cell) if cell else "" for cell in table.extract()[0]]) + " |\n"
                            md_table += "|" + "|".join(["---"] * len(table.extract()[0])) + "|\n"
                            for row in table.extract()[1:]:
                                md_table += "| " + " | ".join([str(cell) if cell else "" for cell in row]) + " |\n"
                            all_text.append(f"\n=== TABEL Halaman {page_num + 1} ===\n{md_table}")
                except Exception:
                    pass
            
            doc.close()
            return "\n\n".join(all_text)
        except Exception as e:
            print(f"Table extraction failed: {e}")
            return ""
    
    def load_metadata(self):
        try:
            if os.path.exists(METADATA_FILE):
                with open(METADATA_FILE, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {"documents": [], "total_queries": 0, "last_query_at": None}
    
    def save_metadata(self):
        try:
            with open(METADATA_FILE, 'w') as f:
                json.dump(self.metadata, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving metadata: {e}")
    
    def add_document_metadata(self, filename: str, size_bytes: int, chunks_count: int):
        import uuid
        # Check if already exists
        for doc in self.metadata["documents"]:
            if doc["filename"] == filename:
                return doc["id"]
        
        doc_meta = {
            "id": str(uuid.uuid4()),
            "filename": filename,
            "size_bytes": size_bytes,
            "uploaded_at": datetime.now().isoformat(),
            "status": "indexed",
            "chunks_count": chunks_count
        }
        self.metadata["documents"].append(doc_meta)
        self.save_metadata()
        return doc_meta["id"]
    
    def get_documents(self):
        return self.metadata.get("documents", [])
    
    def delete_document(self, doc_id: str):
        self.metadata["documents"] = [d for d in self.metadata["documents"] if d["id"] != doc_id]
        self.save_metadata()
        return True
    
    def get_stats(self):
        docs = self.metadata.get("documents", [])
        total_size = sum(d.get("size_bytes", 0) for d in docs)
        return {
            "total_documents": len(docs),
            "total_queries": self.metadata.get("total_queries", 0),
            "total_size_bytes": total_size,
            "last_query_at": self.metadata.get("last_query_at")
        }
    
    def increment_query_count(self):
        self.metadata["total_queries"] = self.metadata.get("total_queries", 0) + 1
        self.metadata["last_query_at"] = datetime.now().isoformat()
        self.save_metadata()

    def load_existing_vectorstore(self):
        try:
            if os.path.exists(FAISS_INDEX_PATH) and os.path.isdir(FAISS_INDEX_PATH):
                return FAISS.load_local(
                    folder_path=FAISS_INDEX_PATH,
                    embeddings=self.embeddings,
                    allow_dangerous_deserialization=True
                )
        except Exception:
            pass
        return None
    
    def refresh_vectorstore(self):
        self.vectorstore = self.load_existing_vectorstore()
        return self.vectorstore is not None

    def create_vectorstore(self, text, filename="unknown", file_size=0):
        try:
            # Preprocess text
            text = self._preprocess_text(text)
            
            # Smaller chunks for more precise retrieval
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,  # Smaller chunks for precise retrieval
                chunk_overlap=100,  # Sufficient overlap
                length_function=len,
                separators=["Pasal ", "\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " "]
            )
            chunks = text_splitter.split_text(text)
            
            # Process chunks with metadata
            processed_chunks = []
            for i, chunk in enumerate(chunks):
                chunk = re.sub(r'\s+', ' ', chunk).strip()
                if len(chunk) > 50:
                    # Extract pasal/section references
                    pasal_refs = self._extract_pasal_refs(chunk)
                    source_info = f"[Sumber: {filename}"
                    if pasal_refs:
                        source_info += f", {pasal_refs}"
                    source_info += "]"
                    
                    processed_chunks.append(f"{source_info}\n{chunk}")
            
            if self.vectorstore:
                self.vectorstore.add_texts(texts=processed_chunks)
            else:
                self.vectorstore = FAISS.from_texts(texts=processed_chunks, embedding=self.embeddings)
            
            self.vectorstore.save_local(FAISS_INDEX_PATH)
            self.add_document_metadata(filename, file_size, len(processed_chunks))
            
            return True
        except Exception as e:
            print(f"Error creating vectorstore: {e}")
            return False

    def _preprocess_text(self, text):
        """Clean and normalize text while preserving structure"""
        # Normalize whitespace but keep paragraph breaks
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = re.sub(r'[ \t]+', ' ', line).strip()
            if line:
                cleaned_lines.append(line)
        return '\n'.join(cleaned_lines)
    
    def _extract_pasal_refs(self, text):
        """Extract Pasal/Ayat references from text"""
        patterns = [
            r'Pasal\s+\d+(?:\s+ayat\s+\([^)]+\))?',
            r'BAB\s+[IVXLCDM]+',
            r'Bagian\s+(?:Ke)?[a-zA-Z]+',
        ]
        refs = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            refs.extend(matches[:2])
        return ', '.join(refs[:2]) if refs else ""

    def _call_llm(self, messages, stream=False, max_retries=2):
        models = [self.llm_model, self.fallback_model]
        for model in models:
            for attempt in range(max_retries):
                try:
                    return self.client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=0.1,
                        max_tokens=1500,
                        top_p=0.95,
                        stream=stream
                    )
                except Exception as e:
                    if "rate_limit" in str(e).lower() or "429" in str(e):
                        if attempt < max_retries - 1:
                            time.sleep(1)
                            continue
                        break
                    raise e
        raise Exception("Semua model sedang sibuk. Coba lagi.")

    def query_stream(self, question):
        """Generator that yields response chunks for streaming"""
        self.refresh_vectorstore()
        
        if not self.vectorstore:
            yield {"response": "Knowledge base belum tersedia. Silakan upload dokumen di halaman Admin, atau letakkan file PDF di folder 'data/'."}
            return
         
        self.increment_query_count()
        
        # Multi-strategy retrieval
        all_docs = []
        seen = set()
        
        # Strategy 1: Direct semantic search
        docs1 = self.vectorstore.similarity_search_with_score(question, k=25)
        for doc, score in docs1:
            content_hash = hash(doc.page_content[:100])
            if content_hash not in seen:
                all_docs.append((doc, score, "semantic"))
                seen.add(content_hash)
        
        # Strategy 2: Keyword-based search
        keywords = self._extract_keywords(question)
        if keywords:
            keyword_query = " ".join(keywords)
            docs2 = self.vectorstore.similarity_search_with_score(keyword_query, k=15)
            for doc, score in docs2:
                content_hash = hash(doc.page_content[:100])
                if content_hash not in seen:
                    all_docs.append((doc, score * 1.1, "keyword"))
                    seen.add(content_hash)
        
        # Strategy 3: Entity/number search
        entities = self._extract_entities(question)
        for entity in entities[:5]:
            docs3 = self.vectorstore.similarity_search_with_score(entity, k=5)
            for doc, score in docs3:
                content_hash = hash(doc.page_content[:100])
                if content_hash not in seen:
                    all_docs.append((doc, score * 0.9, "entity"))
                    seen.add(content_hash)
        
        # Strategy 4: Explicit regulatory term search
        regulatory_terms = self._get_regulatory_terms(question)
        for term in regulatory_terms:
            docs4 = self.vectorstore.similarity_search_with_score(term, k=5)
            for doc, score in docs4:
                content_hash = hash(doc.page_content[:100])
                if content_hash not in seen:
                    all_docs.append((doc, score * 0.85, "regulatory"))
                    seen.add(content_hash)
        
        # Sort by score and take best results
        all_docs.sort(key=lambda x: x[1])
        relevant_docs = all_docs[:15]  # More docs for better coverage
        
        # Build rich context with source attribution
        context_parts = []
        for i, (doc, score, strategy) in enumerate(relevant_docs, 1):
            context_parts.append(f"=== DOKUMEN BAGIAN {i} ===\n{doc.page_content}")
        context = "\n\n".join(context_parts)
        
        # Limit context size
        if len(context) > 8000:
            context = context[:8000]
        
        # Citations for UI
        citations = []
        for doc, _, _ in relevant_docs[:3]:
            citation = doc.page_content[:60].replace('[Sumber:', '').replace(']', '')
            citations.append(citation + "...")
        yield {"citations": citations}
        
        # Apply synonym mapping to question
        question_expanded = self._apply_synonym_mapping(question)
        
        # Comprehensive system prompt from user specification
        system_prompt = """Anda adalah Customer Service Akademik UHO yang ramah dan profesional.

ATURAN UTAMA:
- Jawaban PASTI ada di REFERENSI yang diberikan. CARI DENGAN TELITI!
- Jika ada data tanggal, angka, atau info spesifik di REFERENSI, GUNAKAN itu sebagai jawaban.
- JANGAN bilang "tidak ada" jika belum benar-benar mencari di semua bagian REFERENSI.

GAYA JAWABAN:
- SINGKAT dan TO THE POINT (1-3 kalimat saja)
- Langsung berikan jawaban dalam teks biasa (TANPA format markdown seperti ** atau *)
- Ramah seperti customer service
- Akhiri dengan sumber [Sumber: ...]

CONTOH JAWABAN YANG BENAR:
✅ "Wisuda periode April-Juli 2025 dilaksanakan tanggal 5-6 Agustus 2025. [Sumber: Kalender Akademik 2025/2026]"
✅ "Masa studi maksimal S1 adalah 7 tahun akademik. [Sumber: Peraturan Rektor 2019, Pasal 44]"

PEMETAAN ISTILAH:
- S1 = Program Sarjana
- D3 = Diploma/Vokasi
- IPS = Indeks Prestasi Semester

HANYA jika benar-benar TIDAK ADA di referensi:
"Mohon maaf, saya belum memiliki informasi tersebut. Silakan hubungi Bagian Akademik atau kunjungi https://uho.ac.id"

BAHASA: Indonesia, sopan, profesional."""

        prompt = f"""REFERENSI (jawaban ada di sini, cari dengan teliti):
{context}

PERTANYAAN: {question_expanded}

PENTING: Cari jawabannya di REFERENSI di atas. Jawab SINGKAT (1-3 kalimat) dengan sumber."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        try:
            stream = self._call_llm(messages, stream=True)
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {"response": chunk.choices[0].delta.content}
        except Exception as e:
            yield {"response": f"Error: {str(e)}"}

    def _apply_synonym_mapping(self, question):
        """Expand common abbreviations for better retrieval"""
        mappings = {
            r'\bS1\b': 'S1 (Program Sarjana)',
            r'\bS2\b': 'S2 (Program Magister)',
            r'\bS3\b': 'S3 (Program Doktor)',
            r'\bD3\b': 'D3 (Program Diploma/Vokasi)',
            r'\bD4\b': 'D4 (Program Diploma Empat/Sarjana Terapan)',
            r'\bKRS\b': 'KRS (Kartu Rencana Studi)',
            r'\bUKT\b': 'UKT (Uang Kuliah Tunggal)',
            r'\bSPP\b': 'SPP (Sumbangan Pembinaan Pendidikan)',
            r'\bIPK\b': 'IPK (Indeks Prestasi Kumulatif)',
            r'\bIPS\b': 'IPS (Indeks Prestasi Semester)',
            r'\bSKS\b': 'SKS (Satuan Kredit Semester)',
        }
        result = question
        for pattern, replacement in mappings.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result

    def _extract_keywords(self, text):
        """Extract meaningful keywords"""
        stopwords = {'apa', 'adalah', 'yang', 'dan', 'di', 'ke', 'dari', 'untuk', 'dengan',
                     'pada', 'ini', 'itu', 'atau', 'juga', 'saya', 'kamu', 'dia', 'mereka',
                     'bagaimana', 'kapan', 'dimana', 'siapa', 'mengapa', 'berapa', 'apakah',
                     'bisa', 'dapat', 'akan', 'sudah', 'belum', 'tidak', 'ada', 'harus',
                     'mau', 'ingin', 'tolong', 'mohon', 'coba', 'jelaskan', 'sebutkan',
                     'jika', 'bila', 'ketika', 'saat', 'agar', 'supaya', 'sehingga'}
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        return [w for w in words if w not in stopwords and len(w) > 2]

    def _extract_entities(self, text):
        """Extract important entities like numbers, dates, proper nouns"""
        entities = []
        
        # Numbers with context
        nums = re.findall(r'\d+(?:[.,]\d+)?(?:\s*(?:tahun|semester|sks|persen|%|bulan|minggu|hari))?', text, re.IGNORECASE)
        entities.extend(nums)
        
        # Dates
        dates = re.findall(r'\d{1,2}\s+(?:Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s+\d{4}', text, re.IGNORECASE)
        entities.extend(dates)
        
        # Academic terms
        terms = re.findall(r'(?:IPK|IPS|SKS|KRS|UKT|SPP|S1|S2|S3|D3|D4)\b', text, re.IGNORECASE)
        entities.extend(terms)
        
        # Proper nouns (capitalized words)
        caps = re.findall(r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b', text)
        entities.extend(caps[:3])
        
        return list(set(entities))[:10]

    def _get_regulatory_terms(self, question):
        """Generate specific regulatory search terms based on question"""
        terms = []
        q = question.lower()
        
        # === KALENDER AKADEMIK ===
        if any(w in q for w in ['kapan', 'jadwal', 'tanggal', 'periode', 'semester']):
            terms.append("jadwal pembayaran UKT SPP registrasi")
            terms.append("pengisian KRS online SIAKAD")
            terms.append("masa perkuliahan praktikum")
        
        if any(w in q for w in ['ukt', 'spp', 'pembayaran', 'registrasi']):
            terms.append("pembayaran UKT SPP semester gasal genap")
            terms.append("batas akhir registrasi ulang")
        
        if any(w in q for w in ['uts', 'uas', 'ujian tengah', 'ujian akhir']):
            terms.append("ujian tengah semester UTS")
            terms.append("ujian akhir semester UAS")
        
        if any(w in q for w in ['wisuda', 'yudisium', 'dies natalis']):
            terms.append("pelaksanaan wisuda periode")
            terms.append("dies natalis upacara akademik")
        
        if any(w in q for w in ['kkn', 'kuliah kerja nyata', 'magang']):
            terms.append("KKN Kuliah Kerja Nyata batch")
            terms.append("magang praktik kerja lapangan")
        
        if any(w in q for w in ['snbp', 'snbt', 'utbk', 'smmuho', 'seleksi']):
            terms.append("SNBP SNBT UTBK seleksi masuk")
            terms.append("SMMUHO pendaftaran ujian")
        
        # === MASA STUDI & BEBAN SKS ===
        if any(w in q for w in ['masa studi', 'lama studi', 'beban studi', 'beban']):
            terms.append("beban studi program ditempuh paling lama tahun")
            terms.append("Pasal 44 sarjana 144 sks 7 tahun")
            terms.append("Pasal 43 diploma 108 sks 5 tahun")
        
        if any(w in q for w in ['d3', 'diploma']):
            terms.append("Pasal 43 diploma 3 108 sks 5 tahun")
        
        if any(w in q for w in ['s1', 'sarjana']):
            terms.append("Pasal 44 sarjana 144 sks 7 tahun akademik")
        
        if any(w in q for w in ['s2', 'magister']):
            terms.append("Pasal 46 magister 36 sks 4 tahun")
        
        if any(w in q for w in ['s3', 'doktor']):
            terms.append("Pasal 47 doktor 42 sks 7 tahun disertasi")
        
        if any(w in q for w in ['ips', 'sks', 'diprogramkan', 'diprogram', 'ambil']):
            terms.append("IPS Jumlah sks maksimal diprogramkan")
            terms.append("3,01 4,00 24 sks 2,75 22 sks 2,51 20 sks")
        
        if any(w in q for w in ['1 sks', 'bobot sks', 'nilai sks']):
            terms.append("1 sks tatap muka praktikum per minggu")
        
        # === PENILAIAN & RUMUS ===
        if any(w in q for w in ['nilai', 'huruf', 'rentang', 'konversi']):
            terms.append("nilai huruf A B C D E konversi angka")
            terms.append("rentang nilai 81 100 66 80 56 65")
        
        if any(w in q for w in ['rumus', 'nilai akhir', 'na', 'komponen']):
            terms.append("rumus nilai akhir NA tugas UTS UAS")
            terms.append("komponen penilaian praktikum")
        
        if any(w in q for w in ['kehadiran', 'hadir', 'absen', 'persentase']):
            terms.append("kehadiran minimal 75 persen ujian")
            terms.append("syarat mengikuti ujian mahasiswa")
        
        # === KELULUSAN & PREDIKAT ===
        if any(w in q for w in ['lulus', 'kelulusan', 'syarat lulus']):
            terms.append("syarat kelulusan IPK minimal")
            terms.append("dinyatakan lulus program")
        
        if any(w in q for w in ['predikat', 'cum laude', 'pujian', 'memuaskan']):
            terms.append("predikat kelulusan cum laude dengan pujian")
            terms.append("sangat memuaskan memuaskan IPK")
        
        if any(w in q for w in ['wisudawan', 'terbaik']):
            terms.append("wisudawan terbaik IPK tertinggi masa studi")
        
        # === ADMINISTRASI & CUTI ===
        if any(w in q for w in ['cuti', 'akademik', 'berhenti sementara']):
            terms.append("Pasal 96 cuti akademik syarat")
            terms.append("maksimum cuti semester berturutan")
        
        if any(w in q for w in ['pindah', 'alih program', 'transfer']):
            terms.append("pindah kuliah antar program studi")
            terms.append("syarat IPK pindah semester")
        
        if any(w in q for w in ['daftar ulang', 'registrasi', 'non aktif']):
            terms.append("registrasi ulang status mahasiswa")
            terms.append("non aktif dua semester berturut")
        
        if any(w in q for w in ['ktm', 'kartu tanda mahasiswa']):
            terms.append("Pasal 109 KTM hilang surat keterangan")
        
        # === SKRIPSI, TESIS, DISERTASI ===
        if any(w in q for w in ['skripsi', 'tugas akhir', 'ta']):
            terms.append("skripsi tugas akhir syarat")
            terms.append("masa penulisan skripsi maksimal")
        
        if any(w in q for w in ['tesis']):
            terms.append("tesis magister S2 syarat")
        
        if any(w in q for w in ['disertasi']):
            terms.append("disertasi doktor S3 promotor")
        
        if any(w in q for w in ['toefl', 'bahasa inggris']):
            terms.append("TOEFL skor minimal ujian akhir")
        
        if any(w in q for w in ['publikasi', 'jurnal']):
            terms.append("publikasi jurnal syarat kelulusan")
        
        if any(w in q for w in ['pembimbing', 'promotor', 'dosen']):
            terms.append("pembimbing utama skripsi promotor")
            terms.append("syarat jabatan fungsional")
        
        # === EVALUASI & DROP OUT ===
        if any(w in q for w in ['evaluasi', 'do', 'drop out', 'gagal studi']):
            terms.append("evaluasi program mahasiswa DO")
            terms.append("gagal studi dikeluarkan")
        
        if any(w in q for w in ['perpanjangan', 'masa studi']):
            terms.append("perpanjangan masa studi syarat")
        
        if any(w in q for w in ['skorsing']):
            terms.append("masa skorsing dihitung")
        
        # === ETIKA & SANKSI ===
        if any(w in q for w in ['plagiat', 'sanksi', 'pelanggaran']):
            terms.append("sanksi plagiat pelanggaran")
            terms.append("teguran skorsing dikeluarkan")
        
        if any(w in q for w in ['larangan', 'dilarang', 'tidak boleh']):
            terms.append("larangan mahasiswa kampus")
        
        if any(w in q for w in ['demonstrasi', 'demo', 'unjuk rasa']):
            terms.append("demonstrasi radius izin tertulis")
        
        if any(w in q for w in ['narkoba', 'obat terlarang']):
            terms.append("narkoba sanksi berat dikeluarkan")
        
        if any(w in q for w in ['pemalsuan', 'palsu', 'tanda tangan']):
            terms.append("memalsukan tanda tangan sanksi")
        
        if any(w in q for w in ['skpi', 'surat keterangan']):
            terms.append("SKPI Surat Keterangan Pendamping Ijazah")
        
        if any(w in q for w in ['gelar', 'dicabut']):
            terms.append("gelar akademik dicabut tidak sah")
        
        if any(w in q for w in ['dosen pa', 'pembimbing akademik']):
            terms.append("dosen pembimbing akademik PA kewajiban")
        
        return terms
