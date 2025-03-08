import streamlit as st
from docx import Document
import re
from supabase import create_client
from difflib import get_close_matches
import os

# ====================================================================================
# KONFIGURASI SUPABASE
# ====================================================================================
SUPABASE_URL = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY") or st.secrets.get("SUPABASE_ANON_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Konfigurasi Supabase tidak ditemukan!")
    st.stop()

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Gagal terhubung ke Supabase: {str(e)}")
    st.stop()

# ====================================================================================
# FUNGSI UTAMA
# ====================================================================================
@st.cache_data(ttl=3600)
def load_kbbi():
    """Muat semua kata KBBI dari Supabase dengan pagination"""
    try:
        all_words = []
        page = 1
        while True:
            # Ambil data per 1000 baris
            res = supabase.table('kbbifull').select('kata').range((page-1)*1000, page*1000-1).execute()
            if not res.data:
                break
            # Proses data
            words = [row['kata'].strip().lower() for row in res.data]
            all_words.extend(words)
            page += 1
        return set(all_words)
    except Exception as e:
        st.error(f"Gagal memuat data KBBI: {str(e)}")
        return set()

KBBI_WORDS = load_kbbi()

def preprocess(text):
    """Bersihkan teks: lowercase, hapus tanda baca & angka"""
    text = re.sub(r'[^\w\s]', '', text.lower())
    return re.sub(r'\d+', '', text)

def check_spelling(text):
    """Periksa ejaan dan beri rekomendasi"""
    words = preprocess(text).split()
    misspelled = []
    suggestions = {}
    
    progress = st.progress(0)
    status = st.empty()
    total = len(words)
    
    for i, word in enumerate(words):
        clean_word = word.strip()
        if clean_word and clean_word not in KBBI_WORDS:
            misspelled.append(clean_word)
            # Cari rekomendasi dengan algoritma Levenshtein
            matches = get_close_matches(clean_word, KBBI_WORDS, n=3, cutoff=0.7)
            suggestions[clean_word] = ", ".join(matches) if matches else "Tidak ada rekomendasi"
        
        progress.progress((i+1)/total)
        status.text(f"Memproses: {i+1}/{total} kata")
    
    return misspelled, suggestions

# ====================================================================================
# ANTARMUKA STREAMLIT
# ====================================================================================
st.title("🔍 Pemeriksa Ejaan KBBI")
st.markdown("Upload file Word (.docx) untuk mengecek kesesuaian kata dengan KBBI")

uploaded_file = st.file_uploader("Upload Dokumen Word", type=["docx"])

if uploaded_file:
    try:
        doc = Document(uploaded_file)
        full_text = "\n".join([para.text for para in doc.paragraphs])
        
        with st.spinner("Memproses dokumen..."):
            misspelled, saran = check_spelling(full_text)
        
        if misspelled:
            unique_misspelled = list(set(misspelled))
            st.warning(f"⚠️ Ditemukan {len(unique_misspelled)} kata tidak sesuai KBBI")
            
            # Tampilkan hasil dalam format tabel
            data = []
            for kata in unique_misspelled:
                data.append({
                    "Kata": kata,
                    "Rekomendasi": saran.get(kata, "Tidak ada")
                })
            
            st.dataframe(data, use_container_width=True)
            
            # Tombol download
            hasil = "\n".join([f"{row['Kata']} -> {row['Rekomendasi']}" for row in data])
            st.download_button(
                "📥 Download Hasil",
                hasil,
                "hasil_pemeriksaan.txt",
                "text/plain"
            )
        else:
            st.success("✅ Semua kata sesuai dengan KBBI!")
    
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")
