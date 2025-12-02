import streamlit as st
import pandas as pd
import os

# =============================================================================
# KONFIGURASI HALAMAN
# =============================================================================
st.set_page_config(
    page_title="Sistem Pakar Laptop 3IA09",
    page_icon="💻",
    layout="centered"
)

# =============================================================================
# FUNGSI LOAD DATA (BACKEND)
# =============================================================================
@st.cache_data
def load_data():
    df_jurusan = pd.DataFrame()
    df_laptop = pd.DataFrame()
    
    # 1. Load Dataset Jurusan
    if os.path.exists('Dataset Jurusan.csv'):
        try:
            df_jurusan = pd.read_csv('Dataset Jurusan.csv')
            df_jurusan.columns = df_jurusan.columns.str.strip()
        except Exception as e:
            st.error(f"Gagal memuat Dataset Jurusan: {e}")
            
    # 2. Load Dataset Laptop
    if os.path.exists('Dataset Laptop.csv'):
        try:
            df_laptop = pd.read_csv('Dataset Laptop.csv')
            df_laptop.columns = df_laptop.columns.str.strip()
            
            # Cleaning Harga
            def clean_price(price):
                try:
                    p = str(price).replace('Rp','').replace('.','').replace(',','')
                    return int(p)
                except:
                    return 0
            df_laptop['Clean_Price'] = df_laptop['Price_IDR'].apply(clean_price)
            
            # Cleaning Layar
            def clean_screen(s):
                try:
                    val = float(s)
                    if val.is_integer():
                        return str(int(val))
                    return str(val)
                except:
                    return "Unknown"
            df_laptop['Clean_Screen'] = df_laptop['Screen_Size_Inch'].apply(clean_screen)
            
        except Exception as e:
            st.error(f"Gagal memuat Dataset Laptop: {e}")
            
    return df_jurusan, df_laptop

# Load data di awal
df_jurusan, df_laptop = load_data()

# =============================================================================
# SIDEBAR (INPUT USER)
# =============================================================================
st.sidebar.header("🔍 Filter Kebutuhan")

# 1. Input Jurusan
opsi_jurusan = sorted(df_jurusan['Jurusan'].dropna().unique().tolist()) if not df_jurusan.empty else []
input_jurusan = st.sidebar.selectbox("Pilih Jurusan:", opsi_jurusan)

# 2. Input Budget
input_budget = st.sidebar.number_input("Budget Maksimal (Rp):", min_value=0, value=15000000, step=500000, format="%d")

# 3. Input OS
raw_os = sorted(df_laptop['OS'].dropna().astype(str).unique().tolist()) if not df_laptop.empty else []
opsi_os = ["Semua"] + raw_os
input_os = st.sidebar.selectbox("Sistem Operasi:", opsi_os)

# 4. Input Layar
if not df_laptop.empty:
    unique_screens = df_laptop['Clean_Screen'].unique().tolist()
    valid_screens = [x for x in unique_screens if x != "Unknown"]
    valid_screens.sort(key=lambda x: float(x))
    opsi_screen = ["Semua"] + valid_screens
else:
    opsi_screen = ["Semua"]
input_screen = st.sidebar.selectbox("Ukuran Layar (Inch):", opsi_screen)

tombol_cari = st.sidebar.button("Cari Rekomendasi", type="primary")

# =============================================================================
# HALAMAN UTAMA
# =============================================================================
st.title("Rekomendasi Laptop Mahasiswa Gunadarma")
st.divider()

if tombol_cari:
    # --- LOGIKA FILTERING ---
    kategori_target = "Basic Productivity"
    fokus_info = "-"
    software_info = "-"
    
    if not df_jurusan.empty:
        row = df_jurusan[df_jurusan['Jurusan'] == input_jurusan].iloc[0]
        fokus_info = row.get('Fokus_Utama', '-')
        software_info = row.get('Software_Kunci', '-')
        
        vga = str(row.get('VGA_Rekomendasi', '')).lower()
        if "rtx" in vga or "gtx" in vga:
            kategori_target = "Creative & Engineering"
        elif "16" in str(row.get('RAM_Min', '')):
            kategori_target = "Programming & Development"
            
    # Tampilkan Info Jurusan
    st.info(f"**Fokus Jurusan:** {fokus_info} \n\n **Software:** {software_info}")

    # Filter Data Laptop
    results = df_laptop.copy()
    
    def get_category(row):
        cat = "Basic Productivity"
        gpu = str(row['GPU']).lower()
        ram = str(row['RAM'])
        if "rtx" in gpu or "gtx" in gpu or "radeon" in gpu:
            cat = "Creative & Engineering"
        elif "16" in ram or "32" in ram:
             if cat != "Creative & Engineering":
                cat = "Programming & Development"
        return cat

    results['Kategori_App'] = results.apply(get_category, axis=1)

    # Apply Filters
    results = results[results['Kategori_App'] == kategori_target]
    results = results[results['Clean_Price'] <= (input_budget + 500000)]
    if input_os != "Semua":
        results = results[results['OS'].astype(str).str.contains(input_os, case=False, na=False)]
    if input_screen != "Semua":
        results = results[results['Clean_Screen'] == input_screen]

    results = results.sort_values(by='Clean_Price', ascending=False)

    # --- TAMPILKAN HASIL ---
    
    if results.empty:
        st.warning("Tidak ada laptop yang cocok dengan kriteria tersebut. Coba naikkan budget atau ubah filter.")
    else:
        # Pisahkan 2 teratas (Prioritas) dan sisanya (Alternatif)
        top_2 = results.head(2)
        sisanya = results.iloc[2:]
        
        # FUNGSI RENDER KARTU (MODIFIED PRICE COLOR)
        def render_card(row, index):
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"#### #{index+1} {row['Brand']} {row['Model']}")
                    st.caption(f"{row['Processor']} | RAM {row['RAM']} | {row['GPU']}")
                    st.text(f"Storage: {row['Storage']} | Layar: {row['Clean_Screen']}\"")
                with col2:
                    # --- HARGA WARNA BIRU ---
                    # Format harga dulu
                    harga_formatted = f"Rp {row['Clean_Price']:,}".replace(",", ".")
                    # Tampilkan dengan Header 4 (####) dan Warna Biru (:blue[])
                    st.markdown(f"#### :blue[{harga_formatted}]")
                    
                    # --- CUSTOM BUTTON LOGIC ---
                    
                    # Tombol Tokopedia (Hijau Solid #03AC0E)
                    if str(row['Link_Tokopedia']) != 'nan':
                        st.markdown(f"""
                        <a href="{row['Link_Tokopedia']}" target="_blank" style="text-decoration: none;">
                            <div style="background-color: #03AC0E; color: white; padding: 8px; border-radius: 5px; text-align: center; font-weight: bold; margin-bottom: 5px; font-size: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                                Tokopedia
                            </div>
                        </a>
                        """, unsafe_allow_html=True)

                    # Tombol Shopee (Oren Solid #EE4D2D)
                    if str(row['Link_Shopee']) != 'nan':
                        st.markdown(f"""
                        <a href="{row['Link_Shopee']}" target="_blank" style="text-decoration: none;">
                            <div style="background-color: #EE4D2D; color: white; padding: 8px; border-radius: 5px; text-align: center; font-weight: bold; font-size: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                                Shopee
                            </div>
                        </a>
                        """, unsafe_allow_html=True)

        # 1. Tampilkan Rekomendasi Utama
        st.markdown("### ⭐ Pilihan Utama")
        for idx, row in top_2.iterrows():
            render_card(row, idx)

        # 2. Tampilkan Sisanya sebagai ALTERNATIF
        if not sisanya.empty:
            st.write("") 
            st.divider()
            
            # Judul Alternatif Biru
            st.markdown("#### :blue[Alternatif / Opsi Lainnya]")
            
            with st.expander("Lihat daftar lengkap alternatif"):
                for idx, row in sisanya.iterrows():
                    real_idx = idx 
                    render_card(row, real_idx)

else:
    st.info("Silakan pilih jurusan dan budget di menu sebelah kiri, lalu klik 'Cari Rekomendasi'.")