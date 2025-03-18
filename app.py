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

def install_dependencies():
    repo_url = "https://github.com/zyddnys/manga-image-translator.git"
    
    if not os.path.exists(TRANSLATOR_PATH):
        with st.spinner("Mengunduh translator..."):
            subprocess.run(["git", "clone", repo_url, TRANSLATOR_PATH], check=True)
            st.success("✅ Translator berhasil diunduh!")

    os.chdir(TRANSLATOR_PATH)
    subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)
    st.success("✅ Instalasi dependencies selesai!")

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
