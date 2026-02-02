import streamlit as st
import google.generativeai as genai
import PIL.Image
from streamlit_option_menu import option_menu
import sqlite3
import hashlib
import datetime

# --- 1. KONFIGURASI HALAMAN & CSS MEDIS ---
st.set_page_config(
    page_title="MediCare AI",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Palet Warna: Medical Blue (#0288d1), Clean White, Light Grey
st.markdown("""
<style>
    .stApp { background-color: #f8fbfd; }
    
    /* Tombol Utama */
    .stButton>button {
        background-color: #0288d1; color: white; border-radius: 8px; border: none;
        height: 3em; font-weight: bold; transition: 0.3s;
    }
    .stButton>button:hover { background-color: #01579b; }

    /* Container Rapi */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        background-color: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    
    /* Judul */
    h1, h2, h3 { color: #01579b; font-family: 'Segoe UI', sans-serif; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE MANAGEMENT (SQLite) ---
# Fungsi untuk membuat tabel jika belum ada
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

# Enkripsi Password biar aman
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text: return hashed_text
    return False

# Fungsi Tambah User Baru
def add_user(username, password, nama):
    conn = sqlite3.connect('medicare.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users(username, password, nama_lengkap) VALUES (?,?,?)', 
                  (username, make_hashes(password), nama))
        conn.commit()
        return True
    except:
        return False # Username sudah ada
    finally:
        conn.close()

# Fungsi Login
def login_user(username, password):
    conn = sqlite3.connect('medicare.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username =? AND password = ?', 
              (username, make_hashes(password)))
    data = c.fetchall()
    conn.close()
    return data

# Simpan Chat ke Database
def save_consultation(username, question, answer):
    conn = sqlite3.connect('medicare.db')
    c = conn.cursor()
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute('INSERT INTO consultations(username, date, question, answer) VALUES (?,?,?,?)', 
              (username, date, question, answer))
    conn.commit()
    conn.close()

# Ambil Riwayat User
def get_history(username):
    conn = sqlite3.connect('medicare.db')
    c = conn.cursor()
    c.execute('SELECT date, question, answer FROM consultations WHERE username=? ORDER BY id DESC', (username,))
    data = c.fetchall()
    conn.close()
    return data

# Inisialisasi Database saat aplikasi jalan
init_db()

# --- 3. API KEY CONFIG ---
try:
    if "API_KEY" in st.secrets: api_key = st.secrets["API_KEY"]
    else: api_key = "MASUKKAN_KEY_LOKAL_JIKA_ADA"
    if api_key and "MASUKKAN" not in api_key: genai.configure(api_key=api_key)
except: pass

# --- 4. HALAMAN LOGIN & REGISTER (SISTEM BARU) ---
def auth_page():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>🏥 MediCare AI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Asisten Kesehatan Pribadi Anda</p>", unsafe_allow_html=True)
        
        # Tab untuk pilih Login atau Daftar
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Daftar Akun Baru"])
        
        with tab1: # Form Login
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Masuk", type="primary"):
                    result = login_user(username, password)
                    if result:
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = username
                        st.session_state['nama'] = result[0][2] # Ambil nama lengkap
                        st.success("Login Berhasil!")
                        st.rerun()
                    else:
                        st.error("Username atau Password salah")

        with tab2: # Form Register
            with st.form("signup_form"):
                new_user = st.text_input("Buat Username Baru")
                new_nama = st.text_input("Nama Lengkap")
                new_pass = st.text_input("Buat Password", type="password")
                if st.form_submit_button("Daftar Sekarang"):
                    if add_user(new_user, new_pass, new_nama):
                        st.success("Akun berhasil dibuat! Silakan Login di tab sebelah.")
                    else:
                        st.error("Username sudah dipakai, coba yang lain.")

# --- 5. DASHBOARD APLIKASI ---
def main_app():
    # Sidebar Navigation
    with st.sidebar:
        st.header(f"Halo, {st.session_state['nama']}")
        selected = option_menu(
            menu_title="Navigasi",
            options=["Dashboard", "Konsultasi AI", "Cek Kesehatan", "Rekam Medis", "Logout"],
            icons=["speedometer2", "chat-quote", "activity", "clipboard-data", "box-arrow-left"],
            default_index=0,
            styles={"nav-link-selected": {"background-color": "#0288d1"}}
        )

    # --- PAGE 1: DASHBOARD ---
    if selected == "Dashboard":
        st.title("📊 Dashboard Kesehatan")
        st.info("Selamat datang di pusat kontrol kesehatan Anda.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            with st.container(border=True):
                st.metric("Detak Jantung (Avg)", "72 bpm", "-2 bpm")
        with col2:
            with st.container(border=True):
                st.metric("Langkah Hari Ini", "4,200", "+500")
        with col3:
            with st.container(border=True):
                st.metric("Jam Tidur", "6.5 Jam", "-30 min")
        
        st.subheader("Artikel Kesehatan Harian")
        with st.expander("🍎 Tips Nutrisi: Pentingnya Serat"):
            st.write("Serat membantu pencernaan dan mengontrol gula darah. Sumber terbaik: Sayuran hijau, buah, dan biji-bijian.")

    # --- PAGE 2: KONSULTASI AI (CORE FEATURE) ---
    elif selected == "Konsultasi AI":
        st.title("🩺 Konsultasi Dokter AI")
        st.caption("Disclaimer: AI ini memberikan saran informasi, bukan pengganti diagnosa medis profesional.")

        # Chat Interface
        if "messages" not in st.session_state: st.session_state.messages = []

        # Tampilkan chat sementara (session ini)
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Input Area
        with st.container(border=True):
            c1, c2 = st.columns([1, 5])
            with c1:
                uploaded_file = st.file_uploader("📷 Foto Medis", type=["jpg","png","jpeg"], label_visibility="collapsed")
            with c2:
                user_input = st.chat_input("Keluhan Anda (Contoh: Saya demam dan batuk...)")
            
            if uploaded_file: st.image(uploaded_file, width=150, caption="Gambar terlampir")

        if user_input:
            # Tampilkan User Msg
            with st.chat_message("user"):
                st.write(user_input)
                if uploaded_file: st.image(uploaded_file, width=200)
            st.session_state.messages.append({"role":"user", "content":user_input})

            # Proses AI
            with st.spinner("Dr. AI sedang menganalisa..."):
                try:
                    model = genai.GenerativeModel("gemini-flash-latest")
                    content = [user_input]
                    prompt = """Kamu adalah asisten medis profesional yang empatik. 
                    Berikan analisa awal, saran pertolongan pertama, dan rekomendasi obat over-the-counter (bebas).
                    Wajib akhiri dengan saran untuk ke dokter jika gejala berlanjut. Jawab ringkas."""
                    
                    if uploaded_file:
                        content.append(PIL.Image.open(uploaded_file))
                        prompt += " Analisa gambar visual ini (kulit/luka/dll) dengan hati-hati."
                    
                    content[0] = prompt + content[0]
                    response = model.generate_content(content)
                    ai_reply = response.text

                    # Tampilkan AI Msg
                    with st.chat_message("assistant"):
                        st.markdown(ai_reply)
                    st.session_state.messages.append({"role":"assistant", "content":ai_reply})
                    
                    # SIMPAN KE DATABASE (Fitur Baru!)
                    save_consultation(st.session_state['username'], user_input, ai_reply)

                except Exception as e:
                    st.error(f"Error koneksi: {e}")

    # --- PAGE 3: CEK KESEHATAN (TOOLS) ---
    elif selected == "Cek Kesehatan":
        st.title("🧮 Kalkulator Kesehatan")
        
        tab_bmi, tab_kalori = st.tabs(["Berat Badan (BMI)", "Kebutuhan Kalori"])
        
        with tab_bmi:
            st.subheader("Cek Body Mass Index")
            col_b1, col_b2 = st.columns(2)
            berat = col_b1.number_input("Berat (kg)", 40, 150, 60)
            tinggi = col_b2.number_input("Tinggi (cm)", 100, 250, 170)
            
            if st.button("Hitung BMI"):
                t_meter = tinggi / 100
                bmi = berat / (t_meter ** 2)
                st.metric("Skor BMI Anda", f"{bmi:.1f}")
                
                if bmi < 18.5: st.warning("Kategori: Kekurangan Berat Badan")
                elif 18.5 <= bmi < 25: st.success("Kategori: Normal (Ideal)")
                elif 25 <= bmi < 30: st.warning("Kategori: Kelebihan Berat Badan")
                else: st.error("Kategori: Obesitas")

        with tab_kalori:
            st.subheader("Estimasi Kalori Harian (BMR)")
            usia = st.slider("Usia", 10, 90, 25)
            gender = st.radio("Gender", ["Pria", "Wanita"])
            if st.button("Hitung Kalori"):
                if gender == "Pria": bmr = 88.36 + (13.4 * berat) + (4.8 * tinggi) - (5.7 * usia)
                else: bmr = 447.6 + (9.2 * berat) + (3.1 * tinggi) - (4.3 * usia)
                st.info(f"Tubuh Anda butuh sekitar **{int(bmr)} kkal** per hari hanya untuk fungsi dasar.")

    # --- PAGE 4: REKAM MEDIS (DATABASE) ---
    elif selected == "Rekam Medis":
        st.title("📂 Riwayat Konsultasi")
        st.write("Data ini diambil langsung dari Database sistem.")
        
        history = get_history(st.session_state['username'])
        
        if len(history) == 0:
            st.info("Belum ada riwayat konsultasi.")
        else:
            for item in history:
                # Item = (date, question, answer)
                with st.expander(f"📅 {item[0]} - {item[1][:40]}..."):
                    st.markdown(f"**Keluhan:** {item[1]}")
                    st.markdown(f"**Saran AI:**\n{item[2]}")
                    st.caption("Disimpan permanen di Database.")

    # --- LOGOUT ---
    elif selected == "Logout":
        st.session_state['logged_in'] = False
        st.rerun()

# --- 6. MAIN EXECUTION ---
if __name__ == "__main__":
    if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
    
    if st.session_state['logged_in']:
        main_app()
    else:
        auth_page()