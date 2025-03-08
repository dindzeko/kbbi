import streamlit as st
from docx import Document
import re
from supabase import create_client
from difflib import get_close_matches
import os

# Konfigurasi Supabase (gunakan environment variables dari server Anda)
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')

# Inisialisasi client Supabase
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Pastikan environment variables SUPABASE_URL dan SUPABASE_ANON_KEY telah diset")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Judul aplikasi
st.title("📝 Aplikasi Pemeriksaan Kata Berdasarkan KBBI")
st.write("Upload dokumen Word (.docx) untuk memeriksa kata-kata yang tidak sesuai KBBI.")

@st.cache_data(ttl=3600)  # Cache data selama 1 jam
def load_kbbi_words():
    """Ambil semua kata dari tabel kbbifull di Supabase"""
    response = supabase.table('kbbifull').select('kata').execute()
    if response.error:
        st.error(f"Terjadi kesalahan: {response.error.message}")
        return set()
    return {row['kata'].lower() for row in response.data}

# Load kata-kata KBBI sekali saja
VALID_WORDS = load_kbbi_words()

def preprocess_text(text):
    """Membersihkan teks dari tanda baca dan mengubah ke huruf kecil."""
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\d+', '', text)
    return text.lower()

def check_word(word):
    """Periksa apakah kata ada di KBBI"""
    return word in VALID_WORDS

def suggest_word(word):
    """Berikan rekomendasi kata terdekat"""
    matches = get_close_matches(word, VALID_WORDS, n=1, cutoff=0.6)
    return matches[0] if matches else "Tidak ada rekomendasi"

def check_spelling(text):
    """Periksa semua kata dalam teks"""
    words = preprocess_text(text).split()
    misspelled = []
    suggestions = {}
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    total = len(words)
    
    for i, word in enumerate(words):
        if not check_word(word):
            misspelled.append(word)
            suggestions[word] = suggest_word(word)
        
        # Update progress
        progress = (i + 1) / total
        progress_bar.progress(progress)
        status_text.text(f"Memeriksa kata: {i+1}/{total} ({progress:.2%})")
    
    return misspelled, suggestions

# Upload file
uploaded_file = st.file_uploader("Upload File Word (.docx)", type=["docx"])
if uploaded_file:
    try:
        # Ekstrak teks dari dokumen Word
        doc = Document(uploaded_file)
        full_text = " ".join([para.text for para in doc.paragraphs])
        
        # Pemeriksaan ejaan
        with st.spinner("Memeriksa kata-kata..."):
            misspelled_words, suggestions = check_spelling(full_text)
        
        # Tampilkan hasil
        if misspelled_words:
            unique_misspelled = list(set(misspelled_words))
            table_data = {
                "Kata Tidak Sesuai": unique_misspelled,
                "Rekomendasi": [suggestions[word] for word in unique_misspelled]
            }
            
            st.warning(f"Kata tidak sesuai ditemukan: {len(unique_misspelled)}")
            st.table(table_data)
            
            # Tombol download hasil
            result = "\n".join([
                f"{word} -> {suggestions[word]}" 
                for word in unique_misspelled
            ])
            st.download_button(
                "📥 Download Hasil",
                data=result,
                file_name="hasil_pemeriksaan.txt",
                mime="text/plain"
            )
        else:
            st.success("Tidak ada kata yang tidak sesuai KBBI!")
    
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")
