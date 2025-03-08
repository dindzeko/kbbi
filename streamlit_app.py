import streamlit as st
import docx
from io import BytesIO
from koreksi import Koreksi
import re

# ===== Konfigurasi =====
st.set_page_config(
    page_title="Pemeriksa Typo Laporan",
    page_icon="🔍",
    layout="centered"
)

# ===== Fungsi Utama =====
def check_typos(text):
    koreksi = Koreksi()
    words = re.findall(r'\b[\w-]+\b', text)
    typos = []
    
    for word in words:
        processed = word.lower().strip()
        if not processed:
            continue
        if koreksi.periksa(processed):
            typos.append({
                "Kata Asli": word,
                "Koreksi": koreksi.koreksi(processed),
                "Kepercayaan": "95%"  # Dummy value
            })
    return typos

# ===== Antarmuka =====
st.title("🔍 Pemeriksa Typo Laporan")
st.sidebar.header("📝 Pengaturan")

uploaded_file = st.sidebar.file_uploader(
    "Upload file Word (.docx)",
    type=["docx"],
    help="Pastikan dokumen berisi teks biasa tanpa tabel/gambar"
)

if st.sidebar.button("Periksa Typo", disabled=(uploaded_file is None)):
    with st.spinner("Memproses..."):
        try:
            # Baca file
            doc = docx.Document(BytesIO(uploaded_file.getvalue()))
            full_text = " ".join([para.text for para in doc.paragraphs])
            
            # Periksa typo
            typos = check_typos(full_text)
            
            # Tampilkan hasil
            st.subheader("📝 Hasil Pemeriksaan")
            if typos:
                st.warning(f"⚠️ {len(typos)} kata perlu diperiksa ulang:")
                st.table(typos)
            else:
                st.success("✅ Tidak ada typo yang terdeteksi!")
        
        except Exception as e:
            st.error(f"❌ Terjadi kesalahan: {str(e)}")

# ===== Footer =====
st.caption("Dibuat dengan ❤️ oleh [Nama Anda]")
