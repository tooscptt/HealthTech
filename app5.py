import streamlit as st
import google.generativeai as genai
import PIL.Image
from streamlit_option_menu import option_menu
import mysql.connector # Library MySQL
import hashlib
import datetime
import random
import pandas as pd

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="MediCare MySQL",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp { background-color: #f0f4f8; }
    h1, h2, h3 { color: #0277bd; font-family: 'Segoe UI', sans-serif; }
    .css-card { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .stButton>button { background-color: #0288d1; color: white; border-radius: 10px; height: 3em; width: 100%; border: none; font-weight: bold; }
    .nav-link-selected { background-color: #0288d1 !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. KONEKSI DATABASE MYSQL ---
def get_db_connection():
    # Konfigurasi Database XAMPP Default
    return mysql.connector.connect(
        host="localhost",
        user="root",      # User default XAMPP
        password="",      # Password default XAMPP (kosong)
        database="medicare_db" # Pastikan nama DB ini sudah dibuat di phpMyAdmin
    )

def init_db():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Tabel User
        c.execute('''CREATE TABLE IF NOT EXISTS users 
                     (username VARCHAR(50) PRIMARY KEY, password VARCHAR(255), nama_lengkap VARCHAR(100))''')
        
        # Tabel Chat
        c.execute('''CREATE TABLE IF NOT EXISTS consultations 
                     (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(50), 
                      date VARCHAR(20), question TEXT, answer TEXT)''')
        
        # Tabel Mental Logs
        c.execute('''CREATE TABLE IF NOT EXISTS mental_logs 
                     (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(50), 
                      date VARCHAR(20), score INT, category VARCHAR(50))''')
        
        # Tabel Obat
        c.execute('''CREATE TABLE IF NOT EXISTS medicines 
                     (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(50), 
                      nama_obat VARCHAR(100), dosis VARCHAR(100), waktu VARCHAR(20))''')
                      
        conn.commit()
        c.close()
        conn.close()
    except Exception as e:
        st.error(f"Gagal koneksi Database: {e}. Pastikan XAMPP nyala & DB 'medicare_db' sudah dibuat.")

# Fungsi Helper
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- FUNGSI CRUD MYSQL ---

def add_user(username, password, nama):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        # Di MySQL pakai %s bukan ?
        c.execute('INSERT INTO users(username, password, nama_lengkap) VALUES (%s, %s, %s)', 
                  (username, make_hashes(password), nama))
        conn.commit()
        conn.close()
        return True
    except: return False

def login_user(username, password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = %s AND password = %s', 
              (username, make_hashes(password)))
    data = c.fetchall()
    conn.close()
    return data

def save_consultation(username, question, answer):
    conn = get_db_connection()
    c = conn.cursor()
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute('INSERT INTO consultations(username, date, question, answer) VALUES (%s, %s, %s, %s)', 
              (username, date, question, answer))
    conn.commit()
    conn.close()

def save_mental_test(username, score, category):
    conn = get_db_connection()
    c = conn.cursor()
    date = datetime.datetime.now().strftime("%Y-%m-%d") 
    c.execute('INSERT INTO mental_logs(username, date, score, category) VALUES (%s, %s, %s, %s)', 
              (username, date, score, category))
    conn.commit()
    conn.close()

def add_medicine(username, nama, dosis, waktu):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO medicines(username, nama_obat, dosis, waktu) VALUES (%s, %s, %s, %s)', 
              (username, nama, dosis, waktu))
    conn.commit()
    conn.close()

def get_medicines(username):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM medicines WHERE username = %s', (username,))
    data = c.fetchall()
    conn.close()
    return data

def delete_medicine(id_obat):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM medicines WHERE id = %s', (id_obat,))
    conn.commit()
    conn.close()

def get_mental_history_df(username):
    conn = get_db_connection()
    try:
        # Pandas bisa baca langsung dari koneksi MySQL
        df = pd.read_sql(f"SELECT date, score, category FROM mental_logs WHERE username='{username}'", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

def get_chat_history(username):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT date, question, answer FROM consultations WHERE username=%s ORDER BY id DESC', (username,))
    data = c.fetchall()
    conn.close()
    return data

# Inisialisasi DB saat start
init_db()

# --- 3. API KEY ---
try:
    if "API_KEY" in st.secrets: api_key = st.secrets["API_KEY"]
    else: api_key = "MASUKKAN_KEY_LOKAL_JIKA_ADA"
    if api_key and "MASUKKAN" not in api_key: genai.configure(api_key=api_key)
except: pass

# --- KONTEN ---
HUGE_TIPS = [
    "Minum air putih 20 menit sebelum makan membantu diet.",
    "Kurangi gula untuk kulit lebih bersih.",
    "Tidur 7-8 jam per hari meningkatkan fokus."
]

ENCYCLOPEDIA = {
    "Penyakit Dalam": {"Diabetes": "Gula darah tinggi.", "Hipertensi": "Darah tinggi."},
    "Mental": {"Anxiety": "Kecemasan berlebih.", "Burnout": "Kelelahan kerja."}
}

# --- 4. HALAMAN LOGIN ---
def auth_page():
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        with st.container(border=True):
            st.markdown("<h1 style='text-align: center; color:#0288d1;'>🏥 MediCare MySQL</h1>", unsafe_allow_html=True)
            t1, t2 = st.tabs(["Masuk", "Daftar"])
            with t1:
                with st.form("login"):
                    u = st.text_input("Username")
                    p = st.text_input("Password", type="password")
                    if st.form_submit_button("Masuk"):
                        res = login_user(u, p)
                        if res:
                            st.session_state.update({'logged_in': True, 'username': u, 'nama': res[0][2]})
                            st.rerun()
                        else: st.error("Gagal Masuk")
            with t2:
                with st.form("reg"):
                    nu = st.text_input("Username")
                    nn = st.text_input("Nama Lengkap")
                    np = st.text_input("Password", type="password")
                    if st.form_submit_button("Daftar Akun"):
                        if add_user(nu, np, nn): st.success("Berhasil! Silakan Login.")
                        else: st.error("Username sudah ada.")

# --- 5. APLIKASI UTAMA ---
def main_app():
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/387/387561.png", width=80)
        st.markdown(f"### {st.session_state['nama'].split()[0]}")
        menu = option_menu(
            menu_title="Menu Utama",
            options=["Beranda", "Dokter AI", "Ahli Gizi", "Kotak Obat", "Tes Mental", "Rekam Medis", "Logout"],
            icons=["house", "robot", "egg-fried", "capsule", "emoji-dizzy", "graph-up", "box-arrow-left"],
            default_index=0,
            styles={"nav-link-selected": {"background-color": "#0288d1"}}
        )

    if menu == "Beranda":
        st.title("👋 Dashboard")
        st.info(f"Tips: {random.choice(HUGE_TIPS)}")
        c1, c2, c3, c4 = st.columns(4)
        c1.info("Dokter AI"); c2.success("Ahli Gizi"); c3.warning("Obat"); c4.error("Mental")
        
        st.divider()
        st.subheader("Kamus Penyakit")
        t1, t2 = st.tabs(["Fisik", "Mental"])
        with t1: st.write(ENCYCLOPEDIA["Penyakit Dalam"])
        with t2: st.write(ENCYCLOPEDIA["Mental"])

    elif menu == "Dokter AI":
        st.title("🩺 Dokter AI")
        chat_box = st.container(height=400, border=True)
        with chat_box:
            if "msgs" not in st.session_state: st.session_state.msgs = []
            for m in st.session_state.msgs:
                with st.chat_message(m["role"]): st.write(m["content"])
        
        with st.container(border=True):
            c1, c2 = st.columns([1, 5])
            with c1: upl = st.file_uploader("📷", type=["jpg","png"], label_visibility="collapsed")
            with c2: txt = st.chat_input("Keluhan...")
            if upl: st.image(upl, width=100)
            
        if txt:
            st.session_state.msgs.append({"role":"user", "content":txt})
            with chat_box:
                with st.chat_message("user"): st.write(txt)
            try:
                model = genai.GenerativeModel("gemini-flash-latest")
                prompt = f"Dokter, pasien {st.session_state['nama']}: {txt}"
                if upl: prompt += " (Ada gambar)"
                content = [prompt, PIL.Image.open(upl)] if upl else [prompt]
                
                resp = model.generate_content(content)
                reply = resp.text
                st.session_state.msgs.append({"role":"assistant", "content":reply})
                with chat_box:
                    with st.chat_message("assistant"): st.write(reply)
                save_consultation(st.session_state['username'], txt, reply)
            except: st.error("Error AI")

    elif menu == "Ahli Gizi":
        st.title("🥗 Diet Plan")
        bb = st.number_input("Berat (kg)", 40, 150, 60)
        tb = st.number_input("Tinggi (cm)", 100, 200, 170)
        tujuan = st.selectbox("Tujuan", ["Turun Berat", "Naik Berat", "Otot"])
        if st.button("Buat Menu"):
            with st.spinner("AI bekerja..."):
                try:
                    model = genai.GenerativeModel("gemini-flash-latest")
                    prompt = f"Buat meal plan 1 hari untuk BB {bb}kg, TB {tb}cm, Tujuan {tujuan}."
                    st.markdown(model.generate_content(prompt).text)
                except: st.error("Error AI")

    elif menu == "Kotak Obat":
        st.title("💊 Obat Saya")
        with st.expander("Tambah Obat"):
            with st.form("obat"):
                nm = st.text_input("Nama Obat")
                ds = st.text_input("Dosis")
                wk = st.time_input("Waktu")
                if st.form_submit_button("Simpan"):
                    add_medicine(st.session_state['username'], nm, ds, str(wk))
                    st.success("Disimpan!")
                    st.rerun()
        
        meds = get_medicines(st.session_state['username'])
        if meds:
            for m in meds:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2,2,1])
                    c1.write(f"**{m[2]}** ({m[3]})")
                    c2.write(f"⏰ {m[4]}")
                    if c3.button("Hapus", key=m[0]):
                        delete_medicine(m[0])
                        st.rerun()

    elif menu == "Tes Mental":
        st.title("🧠 Cek Stres")
        with st.form("mental"):
            q1 = st.slider("Tingkat Cemas (0-10)", 0, 10, 0)
            if st.form_submit_button("Simpan"):
                cat = "Aman" if q1 < 5 else "Perlu Healing"
                st.metric("Status", cat)
                save_mental_test(st.session_state['username'], q1, cat)

    elif menu == "Rekam Medis":
        st.title("📂 Riwayat")
        t1, t2 = st.tabs(["Grafik Mental", "Chat"])
        with t1:
            df = get_mental_history_df(st.session_state['username'])
            if not df.empty:
                st.line_chart(df, x="date", y="score")
                st.dataframe(df)
            else: st.info("Belum ada data.")
        with t2:
            chats = get_chat_history(st.session_state['username'])
            for c in chats:
                with st.expander(f"{c[0]}"):
                    st.write(f"Q: {c[1]}")
                    st.write(f"A: {c[2]}")

    elif menu == "Logout":
        st.session_state['logged_in'] = False
        st.rerun()

if __name__ == "__main__":
    if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
    if st.session_state['logged_in']: main_app()
    else: auth_page()