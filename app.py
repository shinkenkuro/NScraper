import streamlit as st
import os
import requests
import zipfile
import shutil
import git
from bs4 import BeautifulSoup

def install_dependencies():
    repo_url = "https://github.com/zyddnys/manga-image-translator.git"
    clone_dir = "./manga-image-translator"
    
    if not os.path.exists(clone_dir):
        with st.spinner("Mengunduh translator..."):
            git.Repo.clone_from(repo_url, clone_dir)
            st.success("✅ Translator berhasil diunduh!")
    
    os.chdir(clone_dir)
    os.system("pip install -r requirements.txt")
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
    download_path = "./Manga_Downloads"
    os.makedirs(download_path, exist_ok=True)
    
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(base_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    title = soup.find("h1", class_="title")
    title_text = "Manga" if not title else " ".join([span.text for span in title.find_all("span")])
    folder_name = title_text.replace(" ", "_")
    save_folder = os.path.join(download_path, folder_name)
    os.makedirs(save_folder, exist_ok=True)
    
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
                    st.image(img_filename, caption=f"Page {i}")

    path_file = "./manga_path.txt"
    with open(path_file, "w") as f:
        f.write(save_folder)
    
    st.success(f"🔠 Menjalankan Translator untuk: {save_folder}")
    os.system(f"python -m manga_translator local -v -i \"{save_folder}\"")
    
    translated_folder = f"{save_folder}-translated"
    if os.path.exists(translated_folder):
        zip_filename = f"{translated_folder}.zip"
        shutil.make_archive(translated_folder, 'zip', translated_folder)
        st.success(f"✅ Proses selesai! File ZIP tersimpan di: {zip_filename}")
        st.download_button(label="Unduh Hasil Translate", data=open(zip_filename, "rb").read(), file_name=os.path.basename(zip_filename))
    else:
        st.error("❌ Gagal menemukan folder hasil translate!")

st.title("📖 Manga Scraper & Translator")
if st.button("Install Dependencies"):
    install_dependencies()

base_url = st.text_input("Masukkan URL Manga:")
total_pages = st.number_input("Masukkan jumlah halaman:", min_value=1, step=1)
if st.button("Mulai Scraping"):
    with st.spinner("Sedang memproses..."):
        scrape_manga(base_url, total_pages)