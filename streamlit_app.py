import streamlit as st
from docx import Document
import re
from supabase import create_client, Client
from difflib import get_close_matches
import os

# Konfigurasi Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Cek koneksi sebelum inisialisasi
if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Konfigurasi Supabase tidak lengkap! Pastikan environment variables SUPABASE_URL dan SUPABASE_ANON_KEY telah diset.")
    st.stop()

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    # Tes koneksi
    response = supabase.table('kbbifull').select('*', count='exact').execute()
    if response.count == 0:
        st.warning("Tabel kbbifull kosong! Pastikan data KBBI sudah diunggah ke Supabase.")
except Exception as e:
    st.error(f"Gagal terhubung ke Supabase: {str(e)}")
    st.info("Pastikan:")
    st.info("1. URL dan API key Supabase benar")
    st.info("2. Tabel kbbifull sudah ada di Supabase")
    st.info("3. Akses read untuk role anon sudah diaktifkan")
    st.stop()

# Judul aplikasi
st.title("📝 Aplikasi Pemeriksaan Kata Berdasarkan KBBI")
st.write("Upload dokumen Word (.docx) untuk memeriksa kata-kata yang tidak sesuai KBBI.")

@st.cache_data(ttl=3600)
def load_kbbi_words():
    try:
        response = supabase.table('kbbifull').select('kata').execute()
        if response.error:
            st.error(f"Error saat mengambil data KBBI: {response.error.message}")
            return set()
        return {row['kata'].lower() for row in response.data}
    except Exception as e:
        st.error(f"Koneksi ke Supabase gagal: {str(e)}")
        return set()

# Load kata-kata KBBI
VALID_WORDS = load_kbbi_words()

if not VALID_WORDS:
    st.warning("Tidak dapat memuat data KBBI. Periksa koneksi dan konfigurasi Supabase.")

# Sisanya kode tetap sama seperti sebelumnya...
