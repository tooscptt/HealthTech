import streamlit as st
import google.generativeai as genai
import PIL.Image
from streamlit_option_menu import option_menu
import sqlite3
import hashlib
import datetime
import random
import PyPDF2 # Library baca PDF
import io

# --- 1. KONFIGURASI HALAMAN & CSS PRO ---
st.set_page_config(
    page_title="MediCare AI Pro",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Custom untuk Tampilan Premium
st.markdown("""
<style>
    .stApp { background-color: #f0f4f8; }
    h1, h2, h3 { color: #01579b; font-family: 'Helvetica', sans-serif; }
    
    /* Card Style */
    div.stContainer {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e1e4e8;
    }
    
    /* Tombol Custom */
    .stButton>button {
        background-color: #0288d1; color: white; border-radius: 10px;
        height: 3em; width: 100%; font-weight: bold; border: none;
    }
    .stButton>button:hover { background-color: #0277bd; }
    
    /* Highlight Pesan AI */
    .stChatMessage[data-testid="stChatMessage"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 15px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE MANAGEMENT ---
def init_db():
    conn = sqlite3.connect('medicare_pro.db')
    c = conn.cursor()
    # User Table dengan tambahan kolom (Gol Darah, Umur)
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, nama TEXT, 
                  gender TEXT, umur INTEGER, gol_darah TEXT)''')
    # Consultation Table
    c.execute('''CREATE TABLE IF NOT EXISTS consultations 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, 
                  date TEXT, category TEXT, question TEXT, answer TEXT)''')
    conn.commit()
    conn.close()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def register_user(user, pw, nama, gender, umur, goldar):
    conn = sqlite3.connect('medicare_pro.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users VALUES (?,?,?,?,?,?)', 
                  (user, make_hashes(pw), nama, gender, umur, goldar))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def login_user(user, pw):
    conn = sqlite3.connect('medicare_pro.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username=? AND password=?', (user, make_hashes(pw)))
    data = c.fetchall()
    conn.close()
    return data

def save_history(user, cat, q, a):
    conn = sqlite3.connect('medicare_pro.db')
    c = conn.cursor()
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute('INSERT INTO consultations(username, date, category, question, answer) VALUES (?,?,?,?,?)', 
              (user, date, cat, q, a))
    conn.commit()
    conn.close()

def get_history(user):
    conn = sqlite3.connect('medicare_pro.db')
    c = conn.cursor()
    c.execute('SELECT date, category, question, answer FROM consultations WHERE username=? ORDER BY id DESC', (user,))
    data = c.fetchall()
    conn.close()
    return data

init_db()

# --- 3. HELPER FUNCTIONS ---
# Fungsi Baca PDF (Lab Report)
def read_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# API Key Setup
try:
    if "API_KEY" in st.secrets: api_key = st.secrets["API_KEY"]
    else: api_key = "MASUKKAN_KEY_LOKAL_JIKA_ADA"
    if api_key and "MASUKKAN" not in api_key: genai.configure(api_key=api_key)
except: pass

# --- 4. HALAMAN AUTH ---
def auth_page():
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        with st.container():
            st.markdown("<h1 style='text-align: center; color: #0288d1;'>🏥 MediCare Pro</h1>", unsafe_allow_html=True)
            st.markdown("<center>Asisten Medis Cerdas Berbasis AI</center>", unsafe_allow_html=True)
            st.write("")
            
            tab1, tab2 = st.tabs(["🔓 LOGIN", "📝 DAFTAR"])
            
            with tab1:
                with st.form("login"):
                    u = st.text_input("Username")
                    p = st.text_input("Password", type="password")
                    if st.form_submit_button("Masuk"):
                        data = login_user(u, p)
                        if data:
                            # Simpan info user ke session
                            st.session_state.update({
                                'logged_in': True, 'user': u, 'nama': data[0][2],
                                'gender': data[0][3], 'umur': data[0][4], 'goldar': data[0][5]
                            })
                            st.rerun()
                        else: st.error("Gagal Login")
            
            with tab2:
                with st.form("register"):
                    nu = st.text_input("Username Baru")
                    np = st.text_input("Password", type="password")
                    nn = st.text_input("Nama Lengkap")
                    col_a, col_b = st.columns(2)
                    ng = col_a.selectbox("Gender", ["Pria", "Wanita"])
                    no = col_b.number_input("Umur", 10, 100, 25)
                    nb = st.selectbox("Golongan Darah", ["A", "B", "AB", "O", "Tidak Tahu"])
                    
                    if st.form_submit_button("Daftar Akun"):
                        if register_user(nu, np, nn, ng, no, nb): st.success("Berhasil! Silakan Login.")
                        else: st.error("Username sudah ada.")

# --- 5. DASHBOARD & FITUR ---
def main_app():
    # SIDEBAR PROFILE
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/387/387561.png", width=80)
        st.markdown(f"### {st.session_state['nama']}")
        st.caption(f"{st.session_state['gender']} | {st.session_state['umur']} Th | Gol: {st.session_state['goldar']}")
        
        menu = option_menu(
            menu_title="Menu Utama",
            options=["Beranda", "Chat Dokter AI", "Analisa Lab (PDF)", "Cari RS Terdekat", "Rekam Medis", "Logout"],
            icons=["house", "chat-dots", "file-earmark-medical", "geo-alt", "folder2-open", "box-arrow-left"],
            default_index=0,
            styles={"nav-link-selected": {"background-color": "#0288d1"}}
        )

    # --- MENU 1: BERANDA ---
    if menu == "Beranda":
        st.title(f"Selamat Pagi, {st.session_state['nama']}! ☀️")
        st.write("Apa yang ingin Anda periksakan hari ini?")
        st.divider()

        # TIPS KESEHATAN (Random)
        tips = [
            "Kurangi gula! Konsumsi gula berlebih mempercepat penuaan kulit.",
            "Jalan kaki 10.000 langkah setara membakar 400-500 kalori.",
            "Dehidrasi ringan bisa menyebabkan sakit kepala dan sulit fokus.",
            "Layar gadget memancarkan sinar biru (blue light) yang bisa ganggu tidur."
        ]
        st.info(f"💡 **Info Sehat:** {random.choice(tips)}")

        # NAVIGASI CEPAT (GRID)
        c1, c2, c3 = st.columns(3)
        with c1:
            with st.container():
                st.markdown("### 🤒 Ada Keluhan?")
                st.write("Konsultasikan gejala demam, batuk, atau nyeri.")
                st.button("Mulai Chat", on_click=lambda: st.write("Klik menu 'Chat Dokter AI' di kiri"))
        with c2:
            with st.container():
                st.markdown("### 📄 Cek Hasil Lab")
                st.write("Punya file PDF hasil darah? Biar AI jelaskan.")
                st.button("Upload PDF", on_click=lambda: st.write("Klik menu 'Analisa Lab' di kiri"))
        with c3:
            with st.container():
                st.markdown("### 🚑 Darurat?")
                st.write("Temukan IGD atau Apotek terdekat dari lokasi Anda.")
                st.button("Cari Lokasi", on_click=lambda: st.write("Klik menu 'Cari RS' di kiri"))

        # MITOS VS FAKTA
        st.subheader("🧐 Mitos vs Fakta Medis")
        col_m, col_f = st.columns(2)
        with col_m:
            st.error("❌ **MITOS:** Memakai kacamata minus membuat mata semakin rusak/ketergantungan.")
        with col_f:
            st.success("✅ **FAKTA:** Kacamata adalah alat bantu. Mata bertambah minus biasanya karena faktor genetik atau kebiasaan buruk (baca jarak dekat), bukan karena kacamata.")

    # --- MENU 2: CHAT DOKTER AI ---
    elif menu == "Chat Dokter AI":
        st.title("🩺 Konsultasi Umum")
        st.caption("AI kami dilatih untuk triase awal dan edukasi kesehatan.")
        
        if "chat_history" not in st.session_state: st.session_state.chat_history = []
        
        # Tampilkan Chat
        for chat in st.session_state.chat_history:
            with st.chat_message(chat["role"]): st.markdown(chat["content"])

        # Input
        user_in = st.chat_input("Contoh: Kepala saya pusing berputar dan mual...")
        if user_in:
            with st.chat_message("user"): st.write(user_in)
            st.session_state.chat_history.append({"role":"user", "content":user_in})
            
            with st.spinner("Dokter AI sedang mengetik..."):
                try:
                    model = genai.GenerativeModel("gemini-flash-latest")
                    # Prompt Personalisasi
                    context = f"User bernama {st.session_state['nama']}, {st.session_state['gender']}, {st.session_state['umur']} tahun. "
                    prompt = context + "Jawab sebagai dokter yang ramah. Berikan kemungkinan penyebab, saran penanganan di rumah, dan tanda bahaya. Jawab ringkas."
                    
                    response = model.generate_content(prompt + user_in)
                    reply = response.text
                    
                    with st.chat_message("assistant"): st.markdown(reply)
                    st.session_state.chat_history.append({"role":"assistant", "content":reply})
                    save_history(st.session_state['user'], "Umum", user_in, reply)
                except Exception as e: st.error("Koneksi Error.")

    # --- MENU 3: ANALISA LAB (FITUR BARU & CANGGIH) ---
    elif menu == "Analisa Lab (PDF)":
        st.title("🔬 Analisa Hasil Laboratorium")
        st.write("Bingung baca kertas hasil cek darah? Upload fotonya (PDF) di sini.")
        
        uploaded_pdf = st.file_uploader("Upload File PDF Hasil Lab", type="pdf")
        
        if uploaded_pdf:
            st.success("File berhasil diupload! AI sedang membaca...")
            with st.spinner("Mengekstrak data medis..."):
                try:
                    # 1. Ekstrak Teks dari PDF
                    text_data = read_pdf(uploaded_pdf)
                    
                    # 2. Kirim ke AI
                    model = genai.GenerativeModel("gemini-flash-latest")
                    prompt = """
                    Kamu adalah dokter ahli patologi klinik. Berikut adalah teks dari hasil lab pasien.
                    Tugasmu:
                    1. Rangkum poin-poin yang TIDAK NORMAL (High/Low).
                    2. Jelaskan dalam bahasa awam apa artinya.
                    3. Berikan saran makanan/gaya hidup untuk memperbaiki nilai tersebut.
                    
                    Data Lab:
                    """
                    response = model.generate_content(prompt + text_data[:2000]) # Batasi karakter biar aman
                    
                    st.markdown("### 📋 Penjelasan Dokter AI")
                    with st.container():
                        st.markdown(response.text)
                        
                    save_history(st.session_state['user'], "Lab Analysis", "Upload PDF Lab", response.text)
                    
                except Exception as e:
                    st.error(f"Gagal membaca PDF. Pastikan file tidak rusak. Error: {e}")

    # --- MENU 4: CARI RS (FITUR LOKASI) ---
    elif menu == "Cari RS Terdekat":
        st.title("🚑 Layanan Darurat")
        st.write("Temukan fasilitas kesehatan di sekitar lokasi Anda saat ini.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info("Klik tombol di bawah untuk membuka Google Maps.")
            # Link HTML untuk membuka Google Maps search query
            st.markdown("""
            <a href="https://www.google.com/maps/search/rumah+sakit+terdekat/" target="_blank">
                <button style="background-color:#d32f2f; color:white; padding:15px; border:none; border-radius:10px; width:100%; font-weight:bold; cursor:pointer;">
                🏥 CARI RUMAH SAKIT TERDEKAT
                </button>
            </a>
            """, unsafe_allow_html=True)
            
        with col2:
            st.info("Cari Apotek 24 Jam")
            st.markdown("""
            <a href="https://www.google.com/maps/search/apotek+terdekat/" target="_blank">
                <button style="background-color:#1976d2; color:white; padding:15px; border:none; border-radius:10px; width:100%; font-weight:bold; cursor:pointer;">
                💊 CARI APOTEK TERDEKAT
                </button>
            </a>
            """, unsafe_allow_html=True)
            
        st.write("")
        with st.expander("📞 Nomor Darurat Indonesia"):
            st.markdown("""
            * **Ambulans:** 118 / 119
            * **Polisi:** 110
            * **Pemadam Kebakaran:** 113
            * **SAR / Basarnas:** 115
            """)

    # --- MENU 5: REKAM MEDIS ---
    elif menu == "Rekam Medis":
        st.title("📂 Riwayat Medis Digital")
        history = get_history(st.session_state['user'])
        
        if not history:
            st.info("Belum ada data konsultasi.")
        else:
            for item in history:
                # item = (date, category, question, answer)
                with st.expander(f"{item[1]} | {item[0]}"):
                    st.caption(f"Keluhan/Input: {item[2]}")
                    st.markdown(f"**Saran Dokter:**\n\n{item[3]}")

    # --- LOGOUT ---
    elif menu == "Logout":
        st.session_state.logged_in = False
        st.rerun()

# --- 6. MAIN RUN ---
if __name__ == "__main__":
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if st.session_state.logged_in: main_app()
    else: auth_page()