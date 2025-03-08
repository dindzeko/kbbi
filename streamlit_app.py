import streamlit as st
import docx
from koreksi import Koreksi
import re
from io import BytesIO

# Judul aplikasi
st.set_page_config(page_title="Pemeriksa Typo Laporan", page_icon="🔍")
st.title("🔍 Aplikasi Pemeriksa Typo Laporan Bahasa Indonesia")

# Sidebar untuk upload file
st.sidebar.header("Pengaturan")
uploaded_file = st.sidebar.file_uploader("Upload file Word (.docx)", type=["docx"])
check_button = st.sidebar.button("Periksa Typo", disabled=(uploaded_file is None))

# Fungsi utama pemeriksaan typo
def check_typos_in_docx(file_bytes):
    # Membaca dokumen Word dari bytes
    doc = docx.Document(BytesIO(file_bytes))
    full_text = [para.text for para in doc.paragraphs]
    text = ' '.join(full_text)

    # Inisialisasi pemeriksa ejaan
    koreksi = Koreksi()
    typos = []

    # Ekstrak kata-kata dari teks
    words = re.findall(r'\b[\w-]+\b', text)

    for original_word in words:
        processed_word = original_word.lower().strip()
        if not processed_word:
            continue

        # Periksa typo
        if koreksi.periksa(processed_word):
            correction = koreksi.koreksi(processed_word)
            typos.append({
                "Kata Asli": original_word,
                "Koreksi": correction
            })

    return typos

# Tampilan utama
if check_button:
    with st.spinner("Memproses dokumen..."):
        # Konversi file upload ke bytes
        file_bytes = uploaded_file.getvalue()
        
        # Jalankan pemeriksaan typo
        typos = check_typos_in_docx(file_bytes)
        
        # Tampilkan hasil
        st.subheader("Hasil Pemeriksaan")
        if typos:
            st.warning(f"Ditemukan {len(typos)} kata yang mungkin typo:")
            st.table(typos)
        else:
            st.success("Tidak ditemukan typo dalam dokumen!")

# Catatan penting
st.sidebar.markdown("""
**Catatan:**  
1. Pastikan laporan menggunakan bahasa Indonesia baku  
2. Kosakata teknis/asing mungkin tidak terdeteksi  
3. Gunakan file .docx tanpa tabel/gambar kompleks  
""")

# Info penggunaan
with st.expander("Cara Menggunakan"):
    st.write("""
    1. Upload file Word (.docx) melalui sidebar
    2. Klik tombol "Periksa Typo"
    3. Tunggu hingga proses selesai
    4. Lihat hasil pemeriksaan di layar utama
    """)
