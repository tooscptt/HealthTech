import streamlit as st
import google.generativeai as genai
import PIL.Image
from streamlit_option_menu import option_menu
import sqlite3
import hashlib
import datetime
import random
import pandas as pd # Untuk Grafik

# --- 1. KONFIGURASI HALAMAN & CSS ---
st.set_page_config(
    page_title="MediCare Ultimate",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp { background-color: #f0f4f8; }
    h1, h2, h3 { color: #0277bd; font-family: 'Segoe UI', sans-serif; }
    
    /* Card Style */
    .css-card {
        background-color: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px;
    }
    
    /* Tombol */
    .stButton>button {
        background-color: #0288d1; color: white; border-radius: 10px;
        height: 3em; border: none; font-weight: bold; width: 100%; transition: 0.3s;
    }
    .stButton>button:hover { background-color: #01579b; }

    /* Navigasi */
    .nav-link-selected { background-color: #0288d1 !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE MANAGEMENT ---
def init_db():
    conn = sqlite3.connect('medicare_ultimate.db')
    c = conn.cursor()
    # User
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, nama_lengkap TEXT)''')
    # Chat History
    c.execute('''CREATE TABLE IF NOT EXISTS consultations 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, 
                  date TEXT, question TEXT, answer TEXT)''')
    # Mental Score
    c.execute('''CREATE TABLE IF NOT EXISTS mental_logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, 
                  date TEXT, score INTEGER, category TEXT)''')
    # Obat (FITUR BARU)
    c.execute('''CREATE TABLE IF NOT EXISTS medicines 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, 
                  nama_obat TEXT, dosis TEXT, waktu TEXT)''')
    conn.commit()
    conn.close()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# User Functions
def add_user(username, password, nama):
    conn = sqlite3.connect('medicare_ultimate.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users(username, password, nama_lengkap) VALUES (?,?,?)', 
                  (username, make_hashes(password), nama))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def login_user(username, password):
    conn = sqlite3.connect('medicare_ultimate.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username =? AND password = ?', 
              (username, make_hashes(password)))
    data = c.fetchall()
    conn.close()
    return data

# Data Functions
def save_consultation(username, question, answer):
    conn = sqlite3.connect('medicare_ultimate.db')
    c = conn.cursor()
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute('INSERT INTO consultations(username, date, question, answer) VALUES (?,?,?,?)', 
              (username, date, question, answer))
    conn.commit()
    conn.close()

def save_mental_test(username, score, category):
    conn = sqlite3.connect('medicare_ultimate.db')
    c = conn.cursor()
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute('INSERT INTO mental_logs(username, date, score, category) VALUES (?,?,?,?)', 
              (username, date, score, category))
    conn.commit()
    conn.close()

# Obat Functions (CRUD)
def add_medicine(username, nama, dosis, waktu):
    conn = sqlite3.connect('medicare_ultimate.db')
    c = conn.cursor()
    c.execute('INSERT INTO medicines(username, nama_obat, dosis, waktu) VALUES (?,?,?,?)', 
              (username, nama, dosis, waktu))
    conn.commit()
    conn.close()

def get_medicines(username):
    conn = sqlite3.connect('medicare_ultimate.db')
    c = conn.cursor()
    c.execute('SELECT * FROM medicines WHERE username=?', (username,))
    data = c.fetchall()
    conn.close()
    return data

def delete_medicine(id_obat):
    conn = sqlite3.connect('medicare_ultimate.db')
    c = conn.cursor()
    c.execute('DELETE FROM medicines WHERE id=?', (id_obat,))
    conn.commit()
    conn.close()

# History Functions
def get_history_chat(username):
    conn = sqlite3.connect('medicare_ultimate.db')
    c = conn.cursor()
    c.execute('SELECT date, question, answer FROM consultations WHERE username=? ORDER BY id DESC', (username,))
    data = c.fetchall()
    conn.close()
    return data

def get_history_mental_df(username): # Untuk Grafik
    conn = sqlite3.connect('medicare_ultimate.db')
    # Membaca langsung ke DataFrame pandas
    df = pd.read_sql_query(f"SELECT date, score, category FROM mental_logs WHERE username='{username}'", conn)
    conn.close()
    return df

init_db()

# --- 3. API KEY ---
try:
    if "API_KEY" in st.secrets: api_key = st.secrets["API_KEY"]
    else: api_key = "MASUKKAN_KEY_LOKAL_JIKA_ADA"
    if api_key and "MASUKKAN" not in api_key: genai.configure(api_key=api_key)
except: pass

# --- 4. HALAMAN LOGIN ---
def auth_page():
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        with st.container(border=True):
            st.markdown("<h1 style='text-align: center; color:#0288d1;'>🏥 MediCare Ultimate</h1>", unsafe_allow_html=True)
            st.markdown("<center>Health Super App</center>", unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["Login", "Register"])
            with tab1:
                with st.form("login"):
                    u = st.text_input("Username")
                    p = st.text_input("Password", type="password")
                    if st.form_submit_button("Masuk"):
                        res = login_user(u, p)
                        if res:
                            st.session_state.update({'logged_in': True, 'username': u, 'nama': res[0][2]})
                            st.rerun()
                        else: st.error("Gagal Masuk")
            with tab2:
                with st.form("reg"):
                    nu = st.text_input("Username")
                    nn = st.text_input("Nama Lengkap")
                    np = st.text_input("Password", type="password")
                    if st.form_submit_button("Daftar"):
                        if add_user(nu, np, nn): st.success("Berhasil!")
                        else: st.error("Username ada")

# --- 5. APLIKASI UTAMA ---
def main_app():
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/387/387561.png", width=80)
        st.markdown(f"### {st.session_state['nama'].split()[0]}")
        menu = option_menu(
            menu_title="Navigasi",
            options=["Dashboard", "Dokter AI", "Ahli Gizi AI", "Kotak Obat", "Tes Mental", "Kuis Sehat", "Rekam Medis", "Logout"],
            icons=["house", "robot", "egg-fried", "capsule", "emoji-dizzy", "joystick", "graph-up", "box-arrow-left"],
            default_index=0,
            styles={"nav-link-selected": {"background-color": "#0288d1"}}
        )

    # --- MENU 1: DASHBOARD ---
    if menu == "Dashboard":
        st.title("👋 Dashboard Utama")
        st.write("Pantau kesehatan Anda hari ini.")
        
        # Grid Menu
        c1, c2, c3, c4 = st.columns(4)
        with c1: 
            st.info("**Dokter AI**\n\nDiagnosa Gejala")
        with c2: 
            st.success("**Ahli Gizi**\n\nDiet Plan")
        with c3: 
            st.warning("**Kotak Obat**\n\nJadwal")
        with c4: 
            st.error("**Mental**\n\nCek Stres")
            
        st.divider()
        st.subheader("💡 Fakta Kesehatan Hari Ini")
        fakta = [
            "Tertawa 100 kali setara dengan 15 menit bersepeda stasioner.",
            "Otak manusia tetap aktif bekerja bahkan saat kita tidur.",
            "Kulit adalah organ terbesar tubuh manusia.",
            "Jantung memompa sekitar 7.500 liter darah setiap hari."
        ]
        st.success(random.choice(fakta))

    # --- MENU 2: DOKTER AI ---
    elif menu == "Dokter AI":
        st.title("🩺 Dokter Umum AI")
        st.caption("Konsultasi gejala fisik dan penyakit umum.")
        
        chat_box = st.container(height=400, border=True)
        with chat_box:
            if "msgs" not in st.session_state: st.session_state.msgs = []
            for m in st.session_state.msgs:
                with st.chat_message(m["role"]): st.write(m["content"])
        
        with st.container(border=True):
            c1, c2 = st.columns([1, 5])
            with c1: upl = st.file_uploader("📷", type=["jpg","png"], label_visibility="collapsed")
            with c2: txt = st.chat_input("Keluhan Anda...")
            if upl: st.image(upl, width=100)
            
        if txt:
            st.session_state.msgs.append({"role":"user", "content":txt})
            with chat_box:
                with st.chat_message("user"): st.write(txt)
            
            try:
                model = genai.GenerativeModel("gemini-flash-latest")
                prompt = f"Jawab sebagai dokter. Pasien: {st.session_state['nama']}. " + txt
                if upl: prompt += " Analisa gambar ini."
                content = [prompt]
                if upl: content.append(PIL.Image.open(upl))
                
                resp = model.generate_content(content)
                reply = resp.text
                
                st.session_state.msgs.append({"role":"assistant", "content":reply})
                with chat_box:
                    with st.chat_message("assistant"): st.write(reply)
                save_consultation(st.session_state['username'], txt, reply)
            except: st.error("Error AI")

    # --- MENU 3: AHLI GIZI (FITUR BARU) ---
    elif menu == "Ahli Gizi AI":
        st.title("🥗 Perencanaan Diet AI")
        st.write("Buat jadwal makan personal berdasarkan tujuan Anda.")
        
        with st.container(border=True):
            c1, c2 = st.columns(2)
            bb = c1.number_input("Berat Badan (kg)", 30, 150, 60)
            tb = c2.number_input("Tinggi Badan (cm)", 100, 250, 170)
            goal = st.selectbox("Tujuan Diet", ["Menurunkan Berat Badan", "Menambah Berat Badan", "Mempertahankan Berat", "Membentuk Otot"])
            alergi = st.text_input("Alergi Makanan (Opsional)", placeholder="Contoh: Kacang, Udang")
            
            if st.button("🍽️ Buat Rencana Makan (Meal Plan)"):
                with st.spinner("AI sedang meracik menu..."):
                    try:
                        model = genai.GenerativeModel("gemini-flash-latest")
                        prompt = f"""
                        Buatkan Rencana Makan (Meal Plan) 1 hari lengkap (Pagi, Siang, Malam, Snack) untuk orang dengan:
                        Berat: {bb}kg, Tinggi: {tb}cm. Tujuan: {goal}. Alergi: {alergi}.
                        Sertakan estimasi kalori per menu. Format rapi pakai Markdown.
                        """
                        resp = model.generate_content(prompt)
                        st.markdown("### 📋 Rekomendasi Menu Anda")
                        st.markdown(resp.text)
                    except: st.error("Gagal koneksi AI")

    # --- MENU 4: KOTAK OBAT (CRUD) ---
    elif menu == "Kotak Obat":
        st.title("💊 Manajemen Obat")
        st.write("Catat jadwal minum obat agar tidak lupa.")
        
        with st.expander("➕ Tambah Obat Baru"):
            with st.form("add_med"):
                nm = st.text_input("Nama Obat")
                ds = st.text_input("Dosis (misal: 1 tablet sesudah makan)")
                wk = st.time_input("Waktu Minum")
                if st.form_submit_button("Simpan"):
                    add_medicine(st.session_state['username'], nm, ds, str(wk))
                    st.success("Tersimpan!")
                    st.rerun()
        
        st.divider()
        st.subheader("Daftar Obat Anda")
        meds = get_medicines(st.session_state['username'])
        if meds:
            for m in meds:
                # m = (id, user, nama, dosis, waktu)
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    c1.markdown(f"**{m[2]}**")
                    c1.caption(m[3])
                    c2.markdown(f"⏰ {m[4]}")
                    if c3.button("Hapus", key=f"del_{m[0]}"):
                        delete_medicine(m[0])
                        st.rerun()
        else:
            st.info("Belum ada data obat.")

    # --- MENU 5: TES MENTAL ---
    elif menu == "Tes Mental":
        st.title("🧠 Skrining Stres (PHQ-2)")
        
        with st.form("mental"):
            q1 = st.slider("Seberapa sering merasa murung/sedih?", 0, 3, 0, help="0=Tidak Pernah, 3=Tiap Hari")
            q2 = st.slider("Seberapa sering kehilangan minat?", 0, 3, 0)
            
            if st.form_submit_button("Cek Hasil"):
                score = q1 + q2
                cat = "Stabil" if score < 2 else "Stres Ringan" if score < 4 else "Depresi"
                st.metric("Skor Anda", f"{score}/6", cat)
                if score >= 3: st.warning("Disarankan konsultasi psikolog.")
                else: st.success("Kesehatan mental terjaga.")
                save_mental_test(st.session_state['username'], score, cat)

    # --- MENU 6: KUIS SEHAT (GAMIFICATION) ---
    elif menu == "Kuis Sehat":
        st.title("🎮 Kuis Pengetahuan")
        st.write("Uji wawasan kesehatanmu!")
        
        quiz_data = [
            {"q": "Berapa minimal gelas air per hari?", "opt": ["2 Gelas", "4 Gelas", "8 Gelas"], "a": "8 Gelas"},
            {"q": "Vitamin dari sinar matahari adalah?", "opt": ["Vit C", "Vit D", "Vit A"], "a": "Vit D"},
            {"q": "Organ untuk memompa darah?", "opt": ["Hati", "Jantung", "Ginjal"], "a": "Jantung"}
        ]
        
        q_pick = quiz_data[datetime.datetime.now().minute % 3] # Ganti soal tiap menit
        
        st.subheader(q_pick["q"])
        ans = st.radio("Pilih Jawaban:", q_pick["opt"])
        
        if st.button("Jawab"):
            if ans == q_pick["a"]:
                st.balloons()
                st.success("BENAR! 🎉")
            else:
                st.error("SALAH. Coba lagi!")

    # --- MENU 7: REKAM MEDIS (GRAFIK) ---
    elif menu == "Rekam Medis":
        st.title("📂 Analisis & Riwayat")
        
        tab_chart, tab_chat = st.tabs(["Grafik Mental", "Riwayat Chat"])
        
        with tab_chart:
            st.subheader("Grafik Tingkat Stres")
            df = get_history_mental_df(st.session_state['username'])
            if not df.empty:
                st.line_chart(df, x="date", y="score")
                st.dataframe(df)
            else:
                st.info("Belum ada data tes mental untuk ditampilkan di grafik.")
        
        with tab_chat:
            chats = get_history_chat(st.session_state['username'])
            for c in chats:
                with st.expander(f"{c[0]} - {c[1][:20]}..."):
                    st.write(f"Q: {c[1]}")
                    st.write(f"A: {c[2]}")

    # --- LOGOUT ---
    elif menu == "Logout":
        st.session_state['logged_in'] = False
        st.rerun()

# --- 6. RUN ---
if __name__ == "__main__":
    if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
    if st.session_state['logged_in']: main_app()
    else: auth_page()