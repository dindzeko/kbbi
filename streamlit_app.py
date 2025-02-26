import streamlit as st
from docx import Document
import re
import requests

# Judul aplikasi
st.title("📝 Aplikasi Pemeriksaan Kata Berdasarkan KBBI")
st.write("Upload dokumen Word (.docx) untuk memeriksa kata-kata yang tidak sesuai KBBI.")

def preprocess_text(text):
    """
    Membersihkan teks dari tanda baca dan mengubah ke huruf kecil.
    """
    # Hapus tanda baca dan angka
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\d+', '', text)
    # Ubah ke huruf kecil
    text = text.lower()
    return text

def check_word_with_api(word):
    """
    Memeriksa validitas kata menggunakan API KBBI.
    """
    url = f"https://services.x-labs.my.id/kbbi/search?word={word}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Jika kata ditemukan, hasilnya akan berisi array dengan data
            return len(data) > 0
        return False
    except Exception:
        return False

def check_spelling_with_api(text):
    """
    Memeriksa kata-kata dalam teks menggunakan API KBBI.
    """
    words = preprocess_text(text).split()
    misspelled_words = []
    for word in words:
        if not check_word_with_api(word):
            misspelled_words.append(word)
    return misspelled_words

# Upload file
uploaded_file = st.file_uploader("Upload File Word (.docx)", type=["docx"])

if uploaded_file:
    try:
        # Baca dokumen Word
        doc = Document(uploaded_file)
        
        # Ekstrak teks dari semua paragraf
        full_text = ""
        for para in doc.paragraphs:
            full_text += para.text + " "
        
        # Preprocessing teks
        cleaned_text = preprocess_text(full_text)
        
        # Periksa ejaan menggunakan API KBBI
        with st.spinner("Memeriksa kata-kata..."):
            misspelled_words = check_spelling_with_api(cleaned_text)
        
        # Output hasil
        if misspelled_words:
            st.warning("Kata-kata yang tidak sesuai KBBI:")
            st.write(", ".join(set(misspelled_words)))  # Gunakan set untuk menghindari duplikat
        else:
            st.success("Tidak ada kata yang tidak sesuai KBBI.")
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")
