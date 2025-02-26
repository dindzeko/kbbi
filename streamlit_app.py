import streamlit as st
from docx import Document
import re
import requests
from collections import defaultdict

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

def check_word_with_api(word, cache):
    """
    Memeriksa validitas kata menggunakan API KBBI dengan caching.
    """
    if word in cache:
        return cache[word]
    url = f"https://services.x-labs.my.id/kbbi/search?word={word}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Jika kata ditemukan, hasilnya akan berisi array dengan data
            is_valid = len(data) > 0
            cache[word] = is_valid
            return is_valid
        cache[word] = False
        return False
    except Exception:
        cache[word] = False
        return False

def suggest_word_with_api(word, cache):
    """
    Memberikan rekomendasi kata yang sesuai KBBI berdasarkan input dengan caching.
    """
    if word in cache:
        return cache[word]
    url = f"https://services.x-labs.my.id/kbbi/suggest?word={word}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Ambil saran kata pertama jika ada
            suggestion = data[0] if data else "Tidak ada rekomendasi"
            cache[word] = suggestion
            return suggestion
        cache[word] = "Tidak ada rekomendasi"
        return "Tidak ada rekomendasi"
    except Exception:
        cache[word] = "Tidak ada rekomendasi"
        return "Tidak ada rekomendasi"

def check_spelling_with_api(text):
    """
    Memeriksa kata-kata dalam teks menggunakan API KBBI dengan progress bar.
    """
    words = preprocess_text(text).split()
    total_words = len(words)
    misspelled_words = []
    suggestions = {}
    cache = {}  # Cache untuk menyimpan hasil pengecekan dan rekomendasi
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, word in enumerate(words):
        if not check_word_with_api(word, cache):
            misspelled_words.append(word)
            suggestions[word] = suggest_word_with_api(word, cache)
        
        # Update progress bar
        progress = (i + 1) / total_words
        progress_bar.progress(progress)
        status_text.text(f"Memeriksa kata: {i + 1}/{total_words} ({progress * 100:.2f}%)")
    
    return misspelled_words, suggestions

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
            misspelled_words, suggestions = check_spelling_with_api(cleaned_text)
        
        # Output hasil
        if misspelled_words:
            st.warning("Kata-kata yang tidak sesuai KBBI:")
            # Tampilkan dalam bentuk tabel
            table_data = {
                "Kata Tidak Sesuai": list(set(misspelled_words)),
                "Rekomendasi Kata": [suggestions[word] for word in set(misspelled_words)]
            }
            st.table(table_data)
            
            # Tombol download hasil pemeriksaan
            result_text = "Hasil Pemeriksaan Kata:\n\n"
            for word in set(misspelled_words):
                result_text += f"Kata Tidak Sesuai: {word} -> Rekomendasi: {suggestions[word]}\n"
            st.download_button(
                label="📥 Download Hasil Pemeriksaan",
                data=result_text,
                file_name="hasil_pemeriksaan_kata.txt",
                mime="text/plain"
            )
        else:
            st.success("Tidak ada kata yang tidak sesuai KBBI.")
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")
