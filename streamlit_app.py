import streamlit as st
import docx
from koreksi import Koreksi
import re
from io import BytesIO

# Konfigurasi halaman
st.set_page_config(
    page_title="Pemeriksa Typo Laporan",
    page_icon="🔍",
    layout="centered"
)

# Judul aplikasi
st.title("🔍 Pemeriksa Typo Laporan Bahasa Indonesia")

# Sidebar
with st.sidebar:
    st.header("📝 Pengaturan")
    uploaded_file = st.file_uploader(
        "Upload file Word (.docx)",
        type=["docx"],
        help="Hanya menerima file .docx tanpa tabel/gambar kompleks"
    )
    check_button = st.button(
        "Periksa Typo",
        disabled=(uploaded_file is None),
        type="primary"
    )

# Fungsi pemeriksaan typo
def check_typos_in_docx(file_bytes):
    doc = docx.Document(BytesIO(file_bytes))
    full_text = ' '.join([para.text for para in doc.paragraphs])
    
    koreksi = Koreksi()
    typos = []

    # Ekstrak kata-kata dengan regex
    words = re.findall(r'\b[\w-]+\b', full_text)
    
    for original_word in words:
        processed_word = original_word.lower().strip()
        if not processed_word:
            continue
            
        if koreksi.periksa(processed_word):
            correction = koreksi.koreksi(processed_word)
            typos.append({
                "Kata Asli": original_word,
                "Koreksi": correction
            })
    
    return typos

# Logika utama
if check_button:
    with st.spinner("Memproses dokumen..."):
        try:
            # Konversi file ke bytes
            file_bytes = uploaded_file.getvalue()
            
            # Jalankan pemeriksaan
            typos = check_typos_in_docx(file_bytes)
            
            # Tampilkan hasil
            st.subheader("📝 Hasil Pemeriksaan")
            if typos:
                st.warning(f"Ditemukan {len(typos)} kata yang mungkin typo:")
                st.table(typos)
            else:
                st.success("✅ Tidak ditemukan typo dalam dokumen!")
        
        except Exception as e:
            st.error(f"Terjadi kesalahan: {str(e)}")

# Informasi tambahan
with st.expander("ℹ️ Informasi Penting"):
    st.markdown("""
    - Pastikan laporan menggunakan bahasa Indonesia baku
    - Kosakata teknis/asing mungkin tidak terdeteksi
    - Format dokumen harus .docx tanpa elemen kompleks
    """)

# Footer
st.caption("Dibuat dengan ❤️ menggunakan Streamlit")
