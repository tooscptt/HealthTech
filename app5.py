import streamlit as st
import google.generativeai as genai
import PIL.Image
from streamlit_option_menu import option_menu
import sqlite3
import hashlib
import datetime
import random

# --- 1. KONFIGURASI HALAMAN & TEMA ---
st.set_page_config(
    page_title="MediCare AI",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Custom: Tampilan Medis yang Bersih (Biru & Putih)
st.markdown("""
<style>
    /* Background utama */
    .stApp { background-color: #f0f7fa; }
    
    /* Font Judul */
    h1, h2, h3 { color: #0277bd; font-family: 'Segoe UI', sans-serif; }
    
    /* Tombol Biru Keren */
    .stButton>button {
        background-color: #0288d1; color: white; border-radius: 10px;
        height: 3em; font-weight: bold; border: none; transition: 0.3s;
    }
    .stButton>button:hover { background-color: #01579b; }

    /* Kotak Mitos & Fakta */
    .mitos-box {
        background-color: #ffebee; padding: 15px; border-radius: 10px;
        border-left: 5px solid #ef5350; margin-bottom: 10px;
    }
    .fakta-box {
        background-color: #e8f5e9; padding: 15px; border-radius: 10px;
        border-left: 5px solid #66bb6a; margin-bottom: 10px;
    }
    
    /* Card Container */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        background-color: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE (SQLite) ---
def init_db():
    conn = sqlite3.connect('medicare.db')
    c = conn.cursor()
    # Tabel User
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, nama_lengkap TEXT)''')
    # Tabel Riwayat Konsultasi
    c.execute('''CREATE TABLE IF NOT EXISTS consultations 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, 
                  date TEXT, question TEXT, answer TEXT)''')
    conn.commit()
    conn.close()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def add_user(username, password, nama):
    conn = sqlite3.connect('medicare.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users(username, password, nama_lengkap) VALUES (?,?,?)', 
                  (username, make_hashes(password), nama))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def login_user(username, password):
    conn = sqlite3.connect('medicare.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username =? AND password = ?', 
              (username, make_hashes(password)))
    data = c.fetchall()
    conn.close()
    return data

def save_consultation(username, question, answer):
    conn = sqlite3.connect('medicare.db')
    c = conn.cursor()
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute('INSERT INTO consultations(username, date, question, answer) VALUES (?,?,?,?)', 
              (username, date, question, answer))
    conn.commit()
    conn.close()

def get_history(username):
    conn = sqlite3.connect('medicare.db')
    c = conn.cursor()
    c.execute('SELECT date, question, answer FROM consultations WHERE username=? ORDER BY id DESC', (username,))
    data = c.fetchall()
    conn.close()
    return data

# Jalankan init database
init_db()

# --- 3. SETUP API KEY ---
try:
    if "API_KEY" in st.secrets: api_key = st.secrets["API_KEY"]
    else: api_key = "MASUKKAN_KEY_LOKAL_JIKA_ADA"
    
    if api_key and "MASUKKAN" not in api_key:
        genai.configure(api_key=api_key)
except: pass

# --- 4. LIST DATA EDUKASI (DATABASE KONTEN) ---
# Tips Harian yang akan diacak
DAILY_TIPS = [
    "Minum air putih 2 liter sehari meningkatkan fokus & energi.",
    "Kurangi konsumsi gula untuk kulit yang lebih awet muda.",
    "Jalan kaki 30 menit sehari mengurangi risiko penyakit jantung.",
    "Tidur cukup (7-8 jam) adalah kunci sistem imun yang kuat.",
    "Makan sayuran hijau membantu detoksifikasi alami tubuh.",
    "Hindari melihat layar HP 1 jam sebelum tidur agar nyenyak."
]

# --- 5. HALAMAN LOGIN & REGISTER ---
def auth_page():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container(border=True):
            st.markdown("<h1 style='text-align: center;'>🏥 MediCare AI</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: grey;'>Asisten Kesehatan Keluarga Cerdas</p>", unsafe_allow_html=True)
            
            # Emoji Dokter Besar
            st.markdown("<h1 style='text-align: center; font-size: 60px;'>👨‍⚕️</h1>", unsafe_allow_html=True)

            tab_login, tab_daftar = st.tabs(["🔑 Masuk", "📝 Daftar Baru"])
            
            with tab_login:
                with st.form("login_form"):
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    if st.form_submit_button("Masuk Aplikasi", type="primary"):
                        result = login_user(username, password)
                        if result:
                            st.session_state['logged_in'] = True
                            st.session_state['username'] = username
                            st.session_state['nama'] = result[0][2]
                            st.rerun()
                        else:
                            st.error("Username atau Password Salah!")
            
            with tab_daftar:
                with st.form("register_form"):
                    new_user = st.text_input("Username Baru")
                    new_nama = st.text_input("Nama Lengkap Anda")
                    new_pass = st.text_input("Password Baru", type="password")
                    if st.form_submit_button("Daftar Sekarang"):
                        if add_user(new_user, new_pass, new_nama):
                            st.success("Akun berhasil dibuat! Silakan Login.")
                        else:
                            st.error("Username sudah dipakai orang lain.")

# --- 6. APLIKASI UTAMA (SETELAH LOGIN) ---
def main_app():
    # Sidebar Menu
    with st.sidebar:
        st.header(f"Hai, {st.session_state['nama'].split()[0]}!")
        selected = option_menu(
            menu_title="Menu Utama",
            options=["Beranda Edukasi", "Konsultasi AI", "Cek Kesehatan", "Rekam Medis", "Logout"],
            icons=["house-heart", "chat-square-text", "activity", "journal-medical", "box-arrow-left"],
            default_index=0,
            styles={"nav-link-selected": {"background-color": "#0288d1"}}
        )
        st.markdown("---")
        st.caption("© 2026 MediCare AI Project")

    # --- MENU 1: BERANDA (DASHBOARD EDUKASI) ---
    if selected == "Beranda Edukasi":
        st.markdown(f"# 👋 Selamat Datang, {st.session_state['nama']}!")
        st.write("Semoga Anda sehat selalu. Simak informasi kesehatan hari ini.")
        st.divider()

        # 1. KARTU TIPS HARIAN (RANDOM)
        with st.container(border=True):
            c_icon, c_text = st.columns([1, 8])
            with c_icon:
                st.markdown("<h1>💡</h1>", unsafe_allow_html=True)
            with c_text:
                st.subheader("Tips Sehat Hari Ini")
                st.info(random.choice(DAILY_TIPS))

        # 2. MITOS VS FAKTA (GRID LAYOUT)
        st.subheader("🤔 Mitos atau Fakta?")
        col_a, col_b = st.columns(2)
        
        with col_a:
            with st.container(border=True):
                st.markdown("### 🥶 Tentang Masuk Angin")
                st.markdown('<div class="mitos-box"><b>MITOS:</b> Kerokan bisa "mengeluarkan angin" jahat dari dalam tubuh.</div>', unsafe_allow_html=True)
                st.markdown('<div class="fakta-box"><b>FAKTA:</b> Kerokan hanya melebarkan pembuluh darah kapiler, membuat tubuh terasa hangat dan rileks sementara.</div>', unsafe_allow_html=True)

        with col_b:
            with st.container(border=True):
                st.markdown("### 🚿 Mandi Malam")
                st.markdown('<div class="mitos-box"><b>MITOS:</b> Mandi malam pasti menyebabkan penyakit rematik di tua nanti.</div>', unsafe_allow_html=True)
                st.markdown('<div class="fakta-box"><b>FAKTA:</b> Tidak ada bukti medis langsung. Namun, air dingin bisa memicu nyeri sendi bagi yang <b>sudah punya</b> rematik.</div>', unsafe_allow_html=True)

        st.write("") 

        # 3. POJOK PENGETAHUAN
        st.subheader("📚 Ensiklopedia Penyakit Umum")
        with st.expander("🩸 Hipertensi (Darah Tinggi)"):
            st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b2/Sphygmomanometer_&_Cuff.jpg/320px-Sphygmomanometer_&_Cuff.jpg", width=200)
            st.write("""
            **Apa itu?** Tekanan darah tinggi yang sering disebut "The Silent Killer" karena jarang bergejala.
            **Pencegahan:** Kurangi garam, olahraga rutin, hindari rokok.
            """)
        
        with st.expander("🍭 Diabetes Melitus (Kencing Manis)"):
            st.write("""
            **Gejala 3P:** Sering Haus (Polidipsi), Sering Pipis (Poliuri), Cepat Lapar (Polifagi).
            **Tips:** Kurangi nasi putih dan minuman manis kemasan. Perbanyak sayur.
            """)

    # --- MENU 2: KONSULTASI AI ---
    elif selected == "Konsultasi AI":
        st.title("🩺 Dokter AI Pribadi")
        st.caption("Tanyakan keluhan Anda atau upload foto (luka/obat/hasil lab).")

        # Chat History Container
        chat_box = st.container(height=400, border=True)
        with chat_box:
            if "messages" not in st.session_state: st.session_state.messages = []
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # Input Area
        with st.container(border=True):
            c_up, c_in = st.columns([1, 5])
            with c_up:
                upl = st.file_uploader("📷", type=["jpg","png"], label_visibility="collapsed")
            with c_in:
                txt = st.chat_input("Tulis keluhan Anda di sini...")
            
            if upl: st.image(upl, width=100, caption="Foto Terlampir")

        # Logika AI
        if txt:
            # Tampilkan user input
            with chat_box:
                with st.chat_message("user"):
                    st.write(txt)
                    if upl: st.image(upl, width=200)
            st.session_state.messages.append({"role":"user", "content":txt})

            # Proses AI
            with st.spinner("Dokter AI sedang menganalisa..."):
                try:
                    model = genai.GenerativeModel("gemini-flash-latest")
                    prompt_sys = f"Kamu adalah asisten dokter yang ramah. Jawablah keluhan pasien bernama {st.session_state['nama']}. Berikan diagnosa awal, saran perawatan di rumah, dan rekomendasi obat apotek (OTC). "
                    content = [txt]
                    
                    if upl:
                        content.append(PIL.Image.open(upl))
                        prompt_sys += "Analisa gambar visual yang dikirim pasien ini. "
                    
                    content[0] = prompt_sys + content[0]
                    
                    response = model.generate_content(content)
                    ai_reply = response.text

                    with chat_box:
                        with st.chat_message("assistant"):
                            st.markdown(ai_reply)
                    
                    st.session_state.messages.append({"role":"assistant", "content":ai_reply})
                    # Simpan ke Database
                    save_consultation(st.session_state['username'], txt, ai_reply)

                except Exception as e:
                    st.error("Gagal terhubung ke AI. Cek koneksi internet.")

    # --- MENU 3: CEK KESEHATAN ---
    elif selected == "Cek Kesehatan":
        st.title("🧮 Kalkulator Tubuh Sehat")
        
        tab_bmi, tab_bmr = st.tabs(["Berat Ideal (BMI)", "Kebutuhan Kalori (BMR)"])
        
        with tab_bmi:
            with st.container(border=True):
                st.subheader("Cek Body Mass Index (BMI)")
                c1, c2 = st.columns(2)
                bb = c1.number_input("Berat Badan (kg)", 30, 200, 60)
                tb = c2.number_input("Tinggi Badan (cm)", 100, 250, 170)
                
                if st.button("Hitung BMI"):
                    bmi = bb / ((tb/100)**2)
                    st.metric("Skor BMI Anda", f"{bmi:.1f}")
                    if bmi < 18.5: st.warning("Kategori: Kurus (Underweight)")
                    elif 18.5 <= bmi < 25: st.success("Kategori: Normal (Ideal) ✅")
                    elif 25 <= bmi < 30: st.warning("Kategori: Gemuk (Overweight)")
                    else: st.error("Kategori: Obesitas ⚠️")

        with tab_bmr:
            with st.container(border=True):
                st.subheader("Hitung Kalori Harian")
                usia = st.slider("Usia Anda", 10, 90, 25)
                gender = st.radio("Jenis Kelamin", ["Pria", "Wanita"])
                
                if st.button("Hitung Kebutuhan Kalori"):
                    if gender == "Pria": cal = 88.36 + (13.4*bb) + (4.8*tb) - (5.7*usia)
                    else: cal = 447.6 + (9.2*bb) + (3.1*tb) - (4.3*usia)
                    st.info(f"Tubuh Anda membutuhkan sekitar **{int(cal)} kkal** per hari dalam kondisi istirahat.")

    # --- MENU 4: REKAM MEDIS ---
    elif selected == "Rekam Medis":
        st.title("📂 Riwayat Konsultasi")
        st.write("Daftar percakapan Anda dengan Dokter AI sebelumnya.")
        
        history = get_history(st.session_state['username'])
        
        if not history:
            st.info("Belum ada data konsultasi.")
        else:
            for item in history:
                # item = (date, question, answer)
                with st.expander(f"📅 {item[0]} - {item[1][:40]}..."):
                    st.markdown(f"**Keluhan:** {item[1]}")
                    st.markdown(f"**Saran Dokter:**\n\n{item[2]}")
                    st.caption("Tersimpan aman di Database.")

    # --- LOGOUT ---
    elif selected == "Logout":
        st.session_state['logged_in'] = False
        st.rerun()

# --- 7. EKSEKUSI UTAMA ---
if __name__ == "__main__":
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if st.session_state['logged_in']:
        main_app()
    else:
        auth_page()