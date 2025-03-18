import streamlit as st
import os
import requests
import shutil
import subprocess
from bs4 import BeautifulSoup

# Direktori Penyimpanan yang Diperbolehkan oleh Streamlit Cloud
BASE_PATH = "/tmp"
DOWNLOAD_PATH = os.path.join(BASE_PATH, "Manga_Downloads")
TRANSLATOR_PATH = os.path.join(BASE_PATH, "manga-image-translator")

def check_directories():
    """Pastikan direktori ada sebelum menjalankan proses"""
    if not os.path.exists(DOWNLOAD_PATH):
        os.makedirs(DOWNLOAD_PATH)
    if not os.path.exists(TRANSLATOR_PATH):
        st.error(f"❌ Folder `{TRANSLATOR_PATH}` tidak ditemukan! Jalankan instalasi terlebih dahulu.")
        return False
    return True

def check_directories():
    """Pastikan direktori ada sebelum menjalankan proses"""
    if not os.path.exists(DOWNLOAD_PATH):
        os.makedirs(DOWNLOAD_PATH)
    if not os.path.exists(TRANSLATOR_PATH):
        st.error(f"❌ Folder `{TRANSLATOR_PATH}` tidak ditemukan! Jalankan instalasi terlebih dahulu.")
        return False
    return True

def install_dependencies():
    """Mengunduh repository manga-image-translator dan menginstal dependencies"""
    repo_url = "https://github.com/zyddnys/manga-image-translator.git"
    
    if not os.path.exists(TRANSLATOR_PATH):
        with st.spinner("Mengunduh manga-image-translator..."):
            result = subprocess.run(["git", "clone", repo_url, TRANSLATOR_PATH], capture_output=True, text=True)
            if result.returncode != 0:
                st.error(f"❌ Gagal clone repository:\n{result.stderr}")
                return
    
    os.chdir(TRANSLATOR_PATH)
    with st.spinner("Menginstal dependencies..."):
        result = subprocess.run(["pip", "install", "-r", "requirements.txt"], capture_output=True, text=True)
        if result.returncode != 0:
            st.error(f"❌ Gagal install dependencies:\n{result.stderr}")
            return
    
    st.success("✅ Instalasi selesai!")
    
def run_translator(save_folder):
    """Menjalankan manga translator dan menangani error"""
    if not check_directories():
        return
    
    if not os.path.exists(save_folder):
        st.error(f"❌ Folder `{save_folder}` tidak ditemukan!")
        return

    os.chdir(TRANSLATOR_PATH)
    
    with st.spinner(f"🔠 Menerjemahkan manga di `{save_folder}`..."):
        result = subprocess.run(
            ["python3", "-m", "manga_translator", "local", "-v", "-i", save_folder],
            capture_output=True, text=True
        )
    
        if result.returncode != 0:
            st.error(f"❌ Gagal menjalankan translator:\n{result.stderr}")
            return
    
    st.success("✅ Terjemahan selesai!")

def download_image(img_url, save_path):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(img_url, headers=headers, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        return True
    return False

def scrape_manga(base_url, total_pages):
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)
    
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(base_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    title = soup.find("h1", class_="title")
    title_text = "Manga" if not title else " ".join([span.text for span in title.find_all("span")])
    folder_name = title_text.replace(" ", "_")
    save_folder = os.path.join(DOWNLOAD_PATH, folder_name)
    os.makedirs(save_folder, exist_ok=True)
    
    st.write(f"📂 Folder penyimpanan: `{save_folder}`")
    
    for i in range(1, total_pages + 1):
        page_url = f"{base_url}{i}/"
        page_response = requests.get(page_url, headers=headers)
        page_soup = BeautifulSoup(page_response.text, "html.parser")
        
        img_section = page_soup.find("section", id="image-container")
        if img_section:
            img_tag = img_section.find("img")
            if img_tag and 'src' in img_tag.attrs:
                img_url = img_tag['src']
                img_filename = os.path.join(save_folder, f"page_{i}.webp")
                if download_image(img_url, img_filename):
                    st.write(f"✅ Halaman {i} berhasil diunduh.")
                else:
                    st.write(f"❌ Gagal mengunduh halaman {i}.")
    
    st.success(f"🔠 Menjalankan Translator untuk: `{save_folder}`")
    
    os.chdir(TRANSLATOR_PATH)
    subprocess.run(["python", "-m", "manga_translator", "local", "-v", "-i", save_folder], check=True)
    
    translated_folder = f"{save_folder}-translated"
    if os.path.exists(translated_folder) and os.listdir(translated_folder):
        zip_filename = f"{translated_folder}.zip"
        shutil.make_archive(translated_folder, 'zip', translated_folder)
        st.success(f"✅ Proses selesai! File ZIP tersimpan di: `{zip_filename}`")
        st.download_button(label="Unduh Hasil Translate", data=open(zip_filename, "rb").read(), file_name=os.path.basename(zip_filename))
    else:
        st.error(f"❌ Gagal menemukan folder hasil translate di: `{translated_folder}`")

st.title("📖 Manga Scraper & Translator")
if st.button("Install Dependencies"):
    install_dependencies()

base_url = st.text_input("Masukkan URL Manga:")
total_pages = st.number_input("Masukkan jumlah halaman:", min_value=1, step=1)
if st.button("Mulai Scraping"):
    with st.spinner("Sedang memproses..."):
        scrape_manga(base_url, total_pages)
