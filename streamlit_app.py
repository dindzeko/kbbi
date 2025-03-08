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
            res = supabase.table('kbbifull').select('kata').range((page-1)*1000, page*1000-1).execute()
            if not res.data:
                break
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

def check_word(word):
    """Cek validasi kata dengan analisis imbuhan lengkap"""
    if word in KBBI_WORDS:
        return True
    
    # Pola imbuhan lengkap
    prefixes = ['ber', 'di', 'ter', 'me', 'pe', 'ke', 'se']
    suffixes = ['kan', 'an', 'i', 'nya']
    infixes = ['el', 'em', 'er', 'in']
    circumfixes = [
        ('ber', 'an'), ('ke', 'an'), ('pe', 'an'), 
        ('se', 'nya'), ('di', 'kan'), ('me', 'kan')
    ]
    
    # Cek semua kemungkinan imbuhan
    possible_roots = []
    
    # 1. Cek awalan (prefix)
    for pre in prefixes:
        if word.startswith(pre):
            possible_roots.append(word[len(pre):])
    
    # 2. Cek akhiran (suffix)
    for suf in suffixes:
        if word.endswith(suf):
            possible_roots.append(word[:-len(suf)])
    
    # 3. Cek sisipan (infix)
    for inf in infixes:
        if len(word) > 4:
            pattern = re.compile(f"^{inf}")
            possible_roots.append(pattern.sub('', word))
    
    # 4. Cek apitan (circumfix)
    for (pre, suf) in circumfixes:
        if word.startswith(pre) and word.endswith(suf):
            root = word[len(pre):-len(suf)]
            if root:
                possible_roots.append(root)
    
    # 5. Cek kombinasi awalan + akhiran
    for pre in prefixes:
        for suf in suffixes:
            if word.startswith(pre) and word.endswith(suf):
                root = word[len(pre):-len(suf)]
                if root:
                    possible_roots.append(root)
    
    # 6. Cek pola khusus (peN-, per-, pem-, pen-, dll)
    if word.startswith('pe'):
        possible_roots.append(word[2:])  # pe- → ''
        if len(word) > 3:
            possible_roots.append(word[3:])  # pem-, pen-, etc
    
    # Cek semua kemungkinan akar kata
    for root in possible_roots:
        if root in KBBI_WORDS:
            return True
    
    return False

def suggest_word(word):
    """Berikan rekomendasi dengan analisis imbuhan"""
    if word in KBBI_WORDS:
        return "Kata sudah sesuai KBBI"
    
    # Cari rekomendasi langsung
    matches = get_close_matches(word, KBBI_WORDS, n=3, cutoff=0.7)
    
    # Jika tidak ada, analisis imbuhan
    if not matches:
        possible_roots = []
        for pre in ['ber', 'di', 'ter', 'me', 'pe', 'ke', 'se']:
            if word.startswith(pre):
                possible_roots.append(word[len(pre):])
        
        for root in possible_roots:
            matches += get_close_matches(root, KBBI_WORDS, n=3, cutoff=0.7)
    
    return ", ".join(matches) if matches else "Tidak ada rekomendasi"

def check_spelling(text):
    """Periksa ejaan dengan analisis imbuhan"""
    words = preprocess(text).split()
    misspelled = []
    suggestions = {}
    
    progress = st.progress(0)
    status = st.empty()
    total = len(words)
    
    for i, word in enumerate(words):
        clean_word = word.strip()
        if clean_word and not check_word(clean_word):
            misspelled.append(clean_word)
            suggestions[clean_word] = suggest_word(clean_word)
        
        progress.progress((i+1)/total)
        status.text(f"Memproses: {i+1}/{total} kata")
    
    return misspelled, suggestions

# ====================================================================================
# ANTARMUKA STREAMLIT
# ====================================================================================
st.title("🔍 Pemeriksa Ejaan KBBI dengan Analisis Imbuhan Lengkap")
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
