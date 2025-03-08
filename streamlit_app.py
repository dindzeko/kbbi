import streamlit as st
from docx import Document
import re
from supabase import create_client
from difflib import get_close_matches
import os

# ====================================================================================
# KONFIGURASI DAN KEAMANAN
# ====================================================================================
st.set_page_config(
    page_title="Pemeriksa KBBI",
    page_icon=":book:",
    layout="wide"
)

# Ambil konfigurasi dari secrets (Streamlit Cloud) atau environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY") or st.secrets.get("SUPABASE_ANON_KEY", "")

# Validasi konfigurasi
if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Konfigurasi Supabase tidak ditemukan! Pastikan SUPABASE_URL dan SUPABASE_ANON_KEY sudah diset.")
    st.stop()

# Inisialisasi client Supabase dengan error handling
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Tes koneksi awal
    test_response = supabase.table('kbbifull').select('kata').limit(1).execute()
    
    # Penanganan error untuk versi supabase terbaru
    if hasattr(test_response, 'error') and test_response.error:
        st.error(f"Error Supabase: {test_response.error.message}")
        st.stop()
    if len(test_response.data) == 0:
        st.warning("Tabel kbbifull kosong. Pastikan data KBBI sudah diunggah ke Supabase.")
        
except Exception as e:
    st.error(f"Koneksi ke Supabase gagal: {str(e)}")
    st.info(
        """
        Solusi:
        1. Pastikan URL dan API key benar
        2. Cek koneksi internet
        3. Pastikan tabel kbbifull ada di Supabase
        4. Aktifkan public read access di Supabase
        """
    )
    st.stop()

# ====================================================================================
# FUNGSI UTAMA
# ====================================================================================
@st.cache_data(ttl=3600, show_spinner="Memuat data KBBI...")
def load_kbbi_words():
    """Ambil semua kata KBBI dari Supabase"""
    try:
        response = supabase.table('kbbifull').select('kata').execute()
        
        # Penanganan error untuk versi supabase terbaru
        if hasattr(response, 'error') and response.error:
            st.error(f"Error mengambil data: {response.error.message}")
            return set()
            
        return {row['kata'].lower() for row in response.data}
    except Exception as e:
        st.error(f"Gagal mengambil data: {str(e)}")
        return set()

VALID_WORDS = load_kbbi_words()

def preprocess_text(text):
    """Bersihkan teks dari karakter tidak penting"""
    text = re.sub(r'[^\w\s]', '', text)  # Hapus tanda baca
    text = re.sub(r'\d+', '', text)      # Hapus angka
    return text.lower()

def check_word(word):
    """Cek keberadaan kata di KBBI"""
    return word in VALID_WORDS

def suggest_word(word):
    """Berikan rekomendasi kata terdekat"""
    matches = get_close_matches(word, VALID_WORDS, n=3, cutoff=0.6)
    return ", ".join(matches) if matches else "Tidak ada rekomendasi"

def check_spelling(text):
    """Pemeriksaan ejaan dengan progress bar"""
    words = preprocess_text(text).split()
    total_words = len(words)
    
    misspelled = []
    suggestions = {}
    progress = st.progress(0)
    status = st.empty()
    
    for i, word in enumerate(words):
        if not check_word(word):
            misspelled.append(word)
            suggestions[word] = suggest_word(word)
        progress.progress((i+1)/total_words)
        status.text(f"Memproses: {i+1}/{total_words} kata")
    
    return misspelled, suggestions

# ====================================================================================
# ANTARMUKA STREAMLIT
# ====================================================================================
st.title("📚 Pemeriksa Kata Berdasarkan KBBI")
st.markdown("""
    Upload dokumen Word (.docx) untuk memeriksa kata-kata yang tidak sesuai KBBI.
    Aplikasi ini akan:
    - Mengecek setiap kata dalam dokumen
    - Memberikan rekomendasi kata terdekat
    - Menyimpan hasil pemeriksaan
""")

uploaded_file = st.file_uploader("Upload File Word", type=["docx"])

if uploaded_file:
    try:
        # Ekstrak teks dari dokumen
        doc = Document(uploaded_file)
        full_text = "\n".join([para.text for para in doc.paragraphs])
        
        # Proses pemeriksaan
        with st.spinner("Memproses dokumen..."):
            misspelled, suggestions = check_spelling(full_text)
        
        # Tampilkan hasil
        if misspelled:
            unique_words = list(set(misspelled))
            st.warning(f"⚠️ Ditemukan {len(unique_words)} kata tidak sesuai KBBI")
            
            # Format hasil dalam tabel
            result_df = []
            for word in unique_words:
                result_df.append({
                    "Kata": word,
                    "Rekomendasi": suggestions[word]
                })
            
            st.dataframe(result_df, use_container_width=True)
            
            # Tombol download hasil
            result_text = "\n".join([f"{row['Kata']} -> {row['Rekomendasi']}" for row in result_df])
            st.download_button(
                label="📥 Download Hasil",
                data=result_text,
                file_name="hasil_pemeriksaan.txt",
                mime="text/plain"
            )
        else:
            st.success("✅ Dokumen sudah sesuai KBBI! Tidak ada kata yang perlu diperbaiki.")
    
    except Exception as e:
        st.error(f"❌ Terjadi kesalahan: {str(e)}")

# ====================================================================================
# INFORMASI TAMBAHAN
# ====================================================================================
with st.expander("ℹ️ Panduan Penggunaan"):
    st.write("""
    1. Pastikan file dalam format .docx
    2. Dokumen akan diproses secara keseluruhan
    3. Kata-kata yang tidak ditemukan di KBBI akan ditampilkan
    4. Rekomendasi kata berdasarkan kesamaan fonetik
    """)
