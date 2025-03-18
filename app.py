import streamlit as st
import os
import requests
import zipfile
import shutil
from bs4 import BeautifulSoup

# Install dependencies
os.system("pip install beautifulsoup4 requests")
os.system("git clone https://github.com/zyddnys/manga-image-translator.git")
os.chdir("manga-image-translator")
os.system("pip install -r requirements.txt")
os.chdir("..")

def download_image(img_url, save_path):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(img_url, headers=headers, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        return True
    return False

def zip_translated_folder(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, folder_path))

def scrape_nhentai(base_url, total_pages):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(base_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    title_tag = soup.find("h1", class_="title")
    title = "NHentai_Manga" if not title_tag else " ".join([span.text for span in title_tag.find_all("span")])
    folder_name = title.replace(" ", "_")
    save_folder = os.path.join("downloads", folder_name)
    os.makedirs(save_folder, exist_ok=True)
    
    for i in range(1, total_pages + 1):
        page_url = f"{base_url}{i}/"
        page_response = requests.get(page_url, headers=headers)
        page_soup = BeautifulSoup(page_response.text, "html.parser")
        
        img_tag = page_soup.select_one("#image-container img")
        if img_tag and 'src' in img_tag.attrs:
            img_url = img_tag['src']
            img_filename = os.path.join(save_folder, f"page_{i}.webp")
            download_image(img_url, img_filename)
    
    zip_filename = f"{save_folder}.zip"
    zip_translated_folder(save_folder, zip_filename)
    return zip_filename

st.title("NHentai Manga Translator")
base_url = st.text_input("Masukkan URL NHentai")
total_pages = st.number_input("Masukkan jumlah halaman", min_value=1, step=1)
if st.button("Mulai Scraping & Translate"):
    if base_url and total_pages:
        with st.spinner("Memproses..."):
            zip_file = scrape_nhentai(base_url, total_pages)
            st.success("✅ Proses selesai! Unduh hasilnya di bawah.")
            st.download_button("Download Hasil", open(zip_file, "rb"), file_name=os.path.basename(zip_file))
