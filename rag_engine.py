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
    
    def increment_query_count(self, query_text: str = ""):
        """Track query for analytics"""
        self.metadata["total_queries"] = self.metadata.get("total_queries", 0) + 1
        self.metadata["last_query_at"] = datetime.now().isoformat()
        
        # Track query history (keep last 500 queries)
        if "query_history" not in self.metadata:
            self.metadata["query_history"] = []
        
        self.metadata["query_history"].append({
            "query": query_text,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 500 queries to avoid large files
        if len(self.metadata["query_history"]) > 500:
            self.metadata["query_history"] = self.metadata["query_history"][-500:]
        
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
        """
        Membuat vector store dengan Pasal-aware chunking.
        Setiap Pasal/artikel dijaga agar tetap utuh dalam 1 chunk.
        """
        try:
            # Preprocess text
            text = self._preprocess_text(text)
            
            # v2.0: Pasal-aware semantic chunking
            chunks = self._pasal_aware_chunking(text, filename)
            
            # Process chunks with rich metadata
            processed_chunks = []
            for chunk_data in chunks:
                chunk = chunk_data['content']
                chunk = re.sub(r'\s+', ' ', chunk).strip()
                
                if len(chunk) > 30:
                    # Build source info with pasal reference
                    source_info = f"[Sumber: {filename}"
                    if chunk_data.get('pasal'):
                        source_info += f", {chunk_data['pasal']}"
                    if chunk_data.get('bab'):
                        source_info += f", {chunk_data['bab']}"
                    source_info += "]"
                    
                    processed_chunks.append(f"{source_info}\n{chunk}")
            
            print(f"  → Created {len(processed_chunks)} chunks from {filename}")
            
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
    
    def _pasal_aware_chunking(self, text, filename):
        """
        v2.0: Chunking yang menjaga setiap Pasal tetap utuh.
        Untuk dokumen peraturan, setiap Pasal menjadi 1 chunk.
        Untuk dokumen lain, gunakan semantic chunking.
        """
        chunks = []
        
        # Detect if this is a regulatory document
        is_regulation = 'peraturan' in filename.lower() or 'rektor' in filename.lower()
        is_calendar = 'kalender' in filename.lower()
        
        if is_regulation:
            # Split by Pasal
            pasal_pattern = r'(Pasal\s+\d+.*?)(?=Pasal\s+\d+|BAB\s+[IVXLCDM]+|$)'
            pasal_matches = re.findall(pasal_pattern, text, re.DOTALL | re.IGNORECASE)
            
            # Also extract BAB headers
            bab_pattern = r'(BAB\s+[IVXLCDM]+[^\n]*)'
            current_bab = ""
            
            for match in re.finditer(bab_pattern, text, re.IGNORECASE):
                current_bab = match.group(1).strip()
            
            for pasal_text in pasal_matches:
                pasal_text = pasal_text.strip()
                if len(pasal_text) > 50:
                    # Extract pasal number
                    pasal_match = re.search(r'Pasal\s+(\d+)', pasal_text, re.IGNORECASE)
                    pasal_num = f"Pasal {pasal_match.group(1)}" if pasal_match else ""
                    
                    # If pasal is too long, split by ayat
                    if len(pasal_text) > 1500:
                        ayat_chunks = self._split_pasal_by_ayat(pasal_text, pasal_num)
                        chunks.extend(ayat_chunks)
                    else:
                        chunks.append({
                            'content': pasal_text,
                            'pasal': pasal_num,
                            'bab': current_bab,
                            'type': 'pasal'
                        })
            
            # If no pasals found, fallback to regular chunking
            if not chunks:
                chunks = self._fallback_chunking(text)
        
        elif is_calendar:
            # For calendar, chunk by table/section
            chunks = self._calendar_chunking(text)
        
        else:
            # Regular semantic chunking for other documents
            chunks = self._fallback_chunking(text)
        
        return chunks
    
    def _split_pasal_by_ayat(self, pasal_text, pasal_num):
        """Split a long Pasal into individual ayat chunks"""
        chunks = []
        
        # Pattern for ayat: (1), (2), etc.
        ayat_pattern = r'(\(\d+\)[^(]*?)(?=\(\d+\)|$)'
        ayat_matches = re.findall(ayat_pattern, pasal_text, re.DOTALL)
        
        if ayat_matches and len(ayat_matches) > 1:
            # Add header (everything before first ayat)
            header_match = re.match(r'(Pasal\s+\d+[^\(]*)', pasal_text)
            header = header_match.group(1).strip() if header_match else ""
            
            for ayat_text in ayat_matches:
                ayat_text = ayat_text.strip()
                if len(ayat_text) > 30:
                    # Extract ayat number
                    ayat_match = re.search(r'\((\d+)\)', ayat_text)
                    ayat_num = f"Ayat {ayat_match.group(1)}" if ayat_match else ""
                    
                    chunks.append({
                        'content': f"{header}\n{ayat_text}" if header else ayat_text,
                        'pasal': f"{pasal_num} {ayat_num}".strip(),
                        'bab': '',
                        'type': 'ayat'
                    })
        else:
            # Can't split by ayat, keep as one chunk
            chunks.append({
                'content': pasal_text,
                'pasal': pasal_num,
                'bab': '',
                'type': 'pasal'
            })
        
        return chunks
    
    def _calendar_chunking(self, text):
        """Special chunking for calendar documents - by event/row"""
        chunks = []
        
        # Split by lines and group related content
        lines = text.split('\n')
        current_chunk = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk)
                    if len(chunk_text) > 30:
                        chunks.append({
                            'content': chunk_text,
                            'pasal': '',
                            'bab': 'Kalender Akademik',
                            'type': 'calendar'
                        })
                    current_chunk = []
            else:
                current_chunk.append(line)
                # If chunk is getting long, save it
                if len('\n'.join(current_chunk)) > 500:
                    chunk_text = '\n'.join(current_chunk)
                    chunks.append({
                        'content': chunk_text,
                        'pasal': '',
                        'bab': 'Kalender Akademik',
                        'type': 'calendar'
                    })
                    current_chunk = []
        
        # Don't forget the last chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            if len(chunk_text) > 30:
                chunks.append({
                    'content': chunk_text,
                    'pasal': '',
                    'bab': 'Kalender Akademik',
                    'type': 'calendar'
                })
        
        return chunks if chunks else self._fallback_chunking(text)
    
    def _fallback_chunking(self, text):
        """Fallback chunking using RecursiveCharacterTextSplitter"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=150,
            length_function=len,
            separators=["Pasal ", "\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " "]
        )
        raw_chunks = text_splitter.split_text(text)
        
        chunks = []
        for chunk in raw_chunks:
            if len(chunk) > 30:
                pasal_refs = self._extract_pasal_refs(chunk)
                chunks.append({
                    'content': chunk,
                    'pasal': pasal_refs,
                    'bab': '',
                    'type': 'general'
                })
        
        return chunks

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
        """
        v2.0: Enhanced RAG query dengan:
        - Multi-strategy retrieval
        - Relevance re-ranking
        - Anti-hallucination prompting
        """
        self.refresh_vectorstore()
        
        if not self.vectorstore:
            yield {"response": "Knowledge base belum tersedia. Silakan upload dokumen di halaman Admin, atau letakkan file PDF di folder 'data/'."}
            return
         
        self.increment_query_count(question)
        
        # Apply synonym mapping early for better retrieval
        question_expanded = self._apply_synonym_mapping(question)
        
        # ========================================
        # STAGE 1: Multi-Strategy Retrieval
        # ========================================
        all_docs = []
        seen = set()
        
        # Strategy 1: Direct semantic search (highest priority)
        docs1 = self.vectorstore.similarity_search_with_score(question_expanded, k=30)
        for doc, score in docs1:
            content_hash = hash(doc.page_content[:100])
            if content_hash not in seen:
                all_docs.append((doc, score, "semantic"))
                seen.add(content_hash)
        
        # Strategy 2: Keyword-focused search
        keywords = self._extract_keywords(question)
        if keywords:
            keyword_query = " ".join(keywords)
            docs2 = self.vectorstore.similarity_search_with_score(keyword_query, k=15)
            for doc, score in docs2:
                content_hash = hash(doc.page_content[:100])
                if content_hash not in seen:
                    # Slightly penalize to prefer semantic
                    all_docs.append((doc, score * 1.05, "keyword"))
                    seen.add(content_hash)
        
        # Strategy 3: Entity/number search (for specific queries)
        entities = self._extract_entities(question)
        for entity in entities[:5]:
            docs3 = self.vectorstore.similarity_search_with_score(entity, k=5)
            for doc, score in docs3:
                content_hash = hash(doc.page_content[:100])
                if content_hash not in seen:
                    all_docs.append((doc, score * 0.95, "entity"))
                    seen.add(content_hash)
        
        # Strategy 4: Regulatory term boost
        regulatory_terms = self._get_regulatory_terms(question)
        for term in regulatory_terms[:3]:
            docs4 = self.vectorstore.similarity_search_with_score(term, k=5)
            for doc, score in docs4:
                content_hash = hash(doc.page_content[:100])
                if content_hash not in seen:
                    all_docs.append((doc, score * 0.9, "regulatory"))
                    seen.add(content_hash)
        
        # ========================================
        # STAGE 2: Relevance Re-ranking
        # ========================================
        reranked_docs = self._rerank_documents(question, all_docs)
        relevant_docs = reranked_docs[:12]  # Top 12 most relevant
        
        # ========================================
        # STAGE 3: Build Context
        # ========================================
        context_parts = []
        for i, (doc, score, strategy, relevance) in enumerate(relevant_docs, 1):
            # Include relevance indicator for debugging
            context_parts.append(f"=== BAGIAN {i} (relevansi: {relevance:.0%}) ===\n{doc.page_content}")
        context = "\n\n".join(context_parts)
        
        # Limit context size but keep complete chunks
        if len(context) > 10000:
            context = context[:10000]
        
        # Citations for UI
        citations = []
        for doc, _, _, _ in relevant_docs[:3]:
            citation = doc.page_content[:60].replace('[Sumber:', '').replace(']', '')
            citations.append(citation + "...")
        yield {"citations": citations}
        
        # ========================================
        # STAGE 4: Enhanced Anti-Hallucination Prompt
        # ========================================
        system_prompt = """Anda adalah Asisten Akademik AKASIA v2.0 untuk Universitas Halu Oleo.

TUGAS UTAMA:
Cari dan berikan jawaban dari REFERENSI yang diberikan. Dokumen berisi Peraturan Rektor dan Kalender Akademik UHO.

CARA MENJAWAB:
1. CARI dengan teliti di semua bagian REFERENSI
2. Jika menemukan informasi yang relevan, berikan jawaban dengan jelas
3. Sertakan nomor Pasal atau sumber dokumen
4. Jawab dalam 1-3 kalimat ringkas

PEMETAAN ISTILAH (gunakan untuk pencarian):
- S1 = Program Sarjana
- D3 = Diploma III / Vokasi
- SKS = Satuan Kredit Semester
- IPS = Indeks Prestasi Semester
- IPK = Indeks Prestasi Kumulatif

FORMAT JAWABAN:
"[Jawaban lengkap]. [Sumber: Pasal XX / Kalender Akademik]"

JIKA TIDAK DITEMUKAN:
"Maaf, informasi mengenai [topik] tidak ditemukan dalam dokumen. Silakan hubungi Bagian Akademik UHO."

PENTING: Jangan mengarang informasi. Hanya jawab berdasarkan REFERENSI."""

        prompt = f"""REFERENSI AKADEMIK UHO:
{context}

---
PERTANYAAN: {question}

Instruksi: Cari jawaban di REFERENSI di atas. Jika ditemukan, jawab SINGKAT dengan sumber. Jika tidak ditemukan, katakan tidak tersedia."""

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
    
    def _rerank_documents(self, question, docs):
        """
        v2.0: Re-rank documents based on relevance signals
        Uses keyword overlap and position weighting
        """
        question_lower = question.lower()
        question_words = set(re.findall(r'\b\w+\b', question_lower))
        
        # Remove stopwords
        stopwords = {'apa', 'berapa', 'kapan', 'dimana', 'bagaimana', 'siapa', 
                     'yang', 'dan', 'atau', 'untuk', 'dengan', 'ke', 'di', 'dari',
                     'adalah', 'ini', 'itu', 'ada', 'tidak', 'bisa', 'dapat'}
        question_words = question_words - stopwords
        
        reranked = []
        for doc, score, strategy in docs:
            content_lower = doc.page_content.lower()
            content_words = set(re.findall(r'\b\w+\b', content_lower))
            
            # Calculate relevance score
            overlap = len(question_words & content_words)
            overlap_ratio = overlap / max(len(question_words), 1)
            
            # Bonus for exact phrase match
            phrase_bonus = 0.2 if question_lower[:20] in content_lower else 0
            
            # Bonus for Pasal reference in question matching content
            pasal_match = re.search(r'pasal\s*(\d+)', question_lower)
            pasal_bonus = 0.3 if pasal_match and f"pasal {pasal_match.group(1)}" in content_lower else 0
            
            # Calculate final relevance (lower is better for FAISS scores)
            relevance = overlap_ratio + phrase_bonus + pasal_bonus
            adjusted_score = score * (1 - relevance * 0.3)  # Boost relevant docs
            
            reranked.append((doc, adjusted_score, strategy, relevance))
        
        # Sort by adjusted score (lower is better)
        reranked.sort(key=lambda x: x[1])
        return reranked

    def _apply_synonym_mapping(self, question):
        """
        v2.0: Expand abbreviations dan istilah untuk retrieval lebih baik.
        Menambahkan variasi kata kunci untuk meningkatkan kemungkinan match.
        """
        # Direct replacements
        mappings = {
            r'\bS1\b': 'S1 sarjana program sarjana',
            r'\bS2\b': 'S2 magister program magister pascasarjana',
            r'\bS3\b': 'S3 doktor program doktor',
            r'\bD3\b': 'D3 diploma tiga vokasi',
            r'\bD4\b': 'D4 diploma empat sarjana terapan',
            r'\bKRS\b': 'KRS kartu rencana studi',
            r'\bKHS\b': 'KHS kartu hasil studi',
            r'\bUKT\b': 'UKT uang kuliah tunggal',
            r'\bIPK\b': 'IPK indeks prestasi kumulatif',
            r'\bIPS\b': 'IPS indeks prestasi semester',
            r'\bSKS\b': 'SKS satuan kredit semester',
            r'\bUTS\b': 'UTS ujian tengah semester',
            r'\bUAS\b': 'UAS ujian akhir semester',
            r'\bKKN\b': 'KKN kuliah kerja nyata',
            r'\bTA\b': 'tugas akhir skripsi',
            r'\bDO\b': 'drop out dikeluarkan',
            r'\bcuti\b': 'cuti akademik izin tidak aktif',
            r'\bwisuda\b': 'wisuda kelulusan yudisium',
            r'\blulus\b': 'lulus kelulusan yudisium predikat',
        }
        result = question
        for pattern, replacement in mappings.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        # Add key terms based on question type
        q_lower = question.lower()
        additions = []
        
        if 'masa studi' in q_lower or 'berapa lama' in q_lower:
            additions.append('beban studi tahun akademik sks')
        if 'syarat' in q_lower or 'ketentuan' in q_lower:
            additions.append('pasal peraturan')
        if 'nilai' in q_lower or 'ipk' in q_lower:
            additions.append('indeks prestasi huruf mutu')
        if 'jadwal' in q_lower or 'kapan' in q_lower:
            additions.append('tanggal kalender akademik')
            
        if additions:
            result = result + ' ' + ' '.join(additions)
        
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
