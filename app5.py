import streamlit as st
import google.generativeai as genai
import PIL.Image
from streamlit_option_menu import option_menu
import sqlite3
import hashlib
import datetime
import random

# --- 1. KONFIGURASI HALAMAN & CSS PRO ---
st.set_page_config(
    page_title="MediCare Plus",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Custom: Tampilan Medis Modern
st.markdown("""
<style>
    /* Background & Font */
    .stApp { background-color: #f8fbfd; }
    h1, h2, h3 { color: #0277bd; font-family: 'Segoe UI', sans-serif; }
    
    /* Tombol Utama */
    .stButton>button {
        background-color: #0288d1; color: white; border-radius: 8px;
        height: 3em; border: none; font-weight: bold; transition: 0.3s;
    }
    .stButton>button:hover { background-color: #01579b; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }

    /* Card Box */
    .css-card {
        background-color: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 15px;
        border: 1px solid #e1f5fe;
    }
    
    /* Kotak Mitos/Fakta */
    .mitos { background: #ffebee; padding: 10px; border-radius: 8px; border-left: 5px solid #ef5350; font-size: 0.9em; }
    .fakta { background: #e8f5e9; padding: 10px; border-radius: 8px; border-left: 5px solid #66bb6a; font-size: 0.9em; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE MANAGEMENT (SQLite) ---
def init_db():
    conn = sqlite3.connect('medicare_plus.db')
    c = conn.cursor()
    # Tabel User
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, nama_lengkap TEXT)''')
    # Tabel Riwayat Chat AI
    c.execute('''CREATE TABLE IF NOT EXISTS consultations 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, 
                  date TEXT, question TEXT, answer TEXT)''')
    # Tabel Riwayat Tes Mental (FITUR BARU)
    c.execute('''CREATE TABLE IF NOT EXISTS mental_logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, 
                  date TEXT, score INTEGER, category TEXT)''')
    conn.commit()
    conn.close()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def add_user(username, password, nama):
    conn = sqlite3.connect('medicare_plus.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users(username, password, nama_lengkap) VALUES (?,?,?)', 
                  (username, make_hashes(password), nama))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def login_user(username, password):
    conn = sqlite3.connect('medicare_plus.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username =? AND password = ?', 
              (username, make_hashes(password)))
    data = c.fetchall()
    conn.close()
    return data

def save_consultation(username, question, answer):
    conn = sqlite3.connect('medicare_plus.db')
    c = conn.cursor()
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute('INSERT INTO consultations(username, date, question, answer) VALUES (?,?,?,?)', 
              (username, date, question, answer))
    conn.commit()
    conn.close()

def save_mental_test(username, score, category):
    conn = sqlite3.connect('medicare_plus.db')
    c = conn.cursor()
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute('INSERT INTO mental_logs(username, date, score, category) VALUES (?,?,?,?)', 
              (username, date, score, category))
    conn.commit()
    conn.close()

def get_history_chat(username):
    conn = sqlite3.connect('medicare_plus.db')
    c = conn.cursor()
    c.execute('SELECT date, question, answer FROM consultations WHERE username=? ORDER BY id DESC', (username,))
    data = c.fetchall()
    conn.close()
    return data

def get_history_mental(username):
    conn = sqlite3.connect('medicare_plus.db')
    c = conn.cursor()
    c.execute('SELECT date, score, category FROM mental_logs WHERE username=? ORDER BY id DESC', (username,))
    data = c.fetchall()
    conn.close()
    return data

init_db()

# --- 3. API KEY & CONTENT DATA ---
try:
    if "API_KEY" in st.secrets: api_key = st.secrets["API_KEY"]
    else: api_key = "MASUKKAN_KEY_LOKAL_JIKA_ADA"
    if api_key and "MASUKKAN" not in api_key: genai.configure(api_key=api_key)
except: pass

# DATABASE KONTEN (TIPS, MITOS, ENSIKLOPEDIA)
HUGE_TIPS = [
    "Minum air putih 20 menit sebelum makan membantu mengontrol porsi makan.",
    "Jalan kaki tanpa alas kaki di rumput (earthing) dapat mengurangi stres.",
    "Ganti gula pasir dengan stevia atau madu untuk gula darah lebih stabil.",
    "Tidur miring ke kiri baik untuk penderita asam lambung (GERD).",
    "Konsumsi tomat matang lebih baik daripada mentah karena kandungan Lycopene meningkat.",
    "Olahraga angkat beban meningkatkan kepadatan tulang dan mencegah osteoporosis.",
    "Paparan sinar matahari pagi (jam 8-10) adalah sumber Vitamin D terbaik.",
    "Membaca buku sebelum tidur lebih baik daripada scrolling HP untuk kualitas tidur.",
    "Cuci tangan dengan sabun selama 20 detik membunuh 99% kuman.",
    "Meditasi 10 menit sehari dapat menurunkan tekanan darah tinggi.",
    "Makan perlahan (kunyah 32 kali) membantu pencernaan dan mencegah kembung."
]

MYTH_FACTS = [
    {"title": "Masuk Angin", "m": "Kerokan mengeluarkan angin dari tubuh.", "f": "Kerokan hanya melebarkan pembuluh darah kapiler di kulit."},
    {"title": "Mandi Malam", "m": "Mandi malam menyebabkan rematik.", "f": "Air dingin hanya memicu nyeri pada penderita yang SUDAH punya rematik."},
    {"title": "Wortel & Mata", "m": "Makan banyak wortel menyembuhkan mata minus.", "f": "Vitamin A hanya menjaga kesehatan mata, tidak bisa mengurangi minus."},
    {"title": "Kopi & Jantung", "m": "Minum kopi pasti bikin penyakit jantung.", "f": "Konsumsi kopi wajar (1-2 cangkir) justru mengandung antioksidan baik."},
    {"title": "Vaksin", "m": "Vaksin menyebabkan autisme pada anak.", "f": "Penelitian global membuktikan tidak ada hubungan antara vaksin dan autisme."},
    {"title": "Cokelat", "m": "Cokelat menyebabkan jerawat.", "f": "Gula dan susu dalam cokelat yang memicu jerawat, bukan kakao murninya."}
]

ENCYCLOPEDIA = {
    "Penyakit Dalam": {
        "Diabetes": "Kadar gula darah tinggi akibat insulin tidak bekerja maksimal. Gejala: Sering haus, sering pipis.",
        "Hipertensi": "Tekanan darah >140/90 mmHg. Sering tanpa gejala tapi memicu stroke.",
        "GERD": "Asam lambung naik ke kerongkongan. Hindari pedas, kopi, dan tidur setelah makan."
    },
    "Penyakit Kulit": {
        "Eksim": "Radang kulit gatal, merah, kering. Biasanya karena alergi atau stres.",
        "Jerawat": "Penyumbatan folikel rambut oleh minyak dan sel kulit mati.",
        "Panu": "Infeksi jamur pada kulit. Bercak putih/coklat gatal saat berkeringat."
    },
    "Kesehatan Mental": {
        "Anxiety": "Kecemasan berlebihan yang sulit dikontrol. Gejala: Jantung berdebar, keringat dingin.",
        "Burnout": "Kelelahan fisik & emosional akibat stres kerja berkepanjangan.",
        "Insomnia": "Kesulitan untuk tidur atau mempertahankan tidur nyenyak."
    }
}

# --- 4. HALAMAN LOGIN ---
def auth_page():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container(border=True):
            st.markdown("<h1 style='text-align: center; color:#0288d1;'>🏥 MediCare Plus</h1>", unsafe_allow_html=True)
            st.markdown("<h1 style='text-align: center; font-size: 50px;'>🩺</h1>", unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["Masuk", "Daftar"])
            with tab1:
                with st.form("login"):
                    u = st.text_input("Username")
                    p = st.text_input("Password", type="password")
                    if st.form_submit_button("Log In", type="primary"):
                        res = login_user(u, p)
                        if res:
                            st.session_state.update({'logged_in': True, 'username': u, 'nama': res[0][2]})
                            st.rerun()
                        else: st.error("Gagal Masuk")
            with tab2:
                with st.form("register"):
                    nu = st.text_input("Username")
                    nn = st.text_input("Nama Lengkap")
                    np = st.text_input("Password", type="password")
                    if st.form_submit_button("Sign Up"):
                        if add_user(nu, np, nn): st.success("Akun Dibuat! Silakan Login.")
                        else: st.error("Username sudah ada.")

# --- 5. APLIKASI UTAMA ---
def main_app():
    with st.sidebar:
        st.markdown(f"### Hai, {st.session_state['nama'].split()[0]} 👋")
        menu = option_menu(
            menu_title="Navigasi",
            options=["Beranda", "Konsultasi AI", "Cek Fisik", "Tes Mental", "Rekam Medis", "Logout"],
            icons=["house-door", "chat-text", "activity", "emoji-smile-upside-down", "journal-medical", "box-arrow-left"],
            default_index=0,
            styles={"nav-link-selected": {"background-color": "#0288d1"}}
        )
        st.info("Kesehatan adalah aset paling berharga.")

    # --- MENU 1: BERANDA (MAJOR UPGRADE) ---
    if menu == "Beranda":
        st.markdown(f"# Dashboard Kesehatan")
        st.write("Informasi terkini untuk gaya hidup sehat Anda.")
        
        # A. TIPS HARIAN (Random dari list besar)
        with st.container(border=True):
            c1, c2 = st.columns([1, 8])
            with c1: st.markdown("<h1>💡</h1>", unsafe_allow_html=True)
            with c2:
                st.subheader("Tips Hari Ini")
                st.write(random.choice(HUGE_TIPS))

        # B. MITOS VS FAKTA (Grid 3 Kolom)
        st.subheader("🧐 Mitos vs Fakta")
        # Ambil 3 item acak agar setiap refresh beda konten
        daily_myths = random.sample(MYTH_FACTS, 3)
        cols = st.columns(3)
        
        for idx, col in enumerate(cols):
            with col:
                with st.container(border=True):
                    st.markdown(f"**{daily_myths[idx]['title']}**")
                    st.markdown(f'<div class="mitos">❌ {daily_myths[idx]["m"]}</div>', unsafe_allow_html=True)
                    st.markdown("VS")
                    st.markdown(f'<div class="fakta">✅ {daily_myths[idx]["f"]}</div>', unsafe_allow_html=True)

        # C. ENSIKLOPEDIA (Tabs Kategori)
        st.divider()
        st.subheader("📚 Ensiklopedia Penyakit")
        st.write("Kamus saku kesehatan Anda.")
        
        tab_dalam, tab_kulit, tab_jiwa = st.tabs(["Penyakit Dalam", "Kulit & Kelamin", "Kesehatan Mental"])
        
        with tab_dalam:
            for k, v in ENCYCLOPEDIA["Penyakit Dalam"].items():
                with st.expander(f"🩺 {k}"): st.write(v)
        with tab_kulit:
            for k, v in ENCYCLOPEDIA["Penyakit Kulit"].items():
                with st.expander(f"🧴 {k}"): st.write(v)
        with tab_jiwa:
            for k, v in ENCYCLOPEDIA["Kesehatan Mental"].items():
                with st.expander(f"🧠 {k}"): st.write(v)

    # --- MENU 2: KONSULTASI AI ---
    elif menu == "Konsultasi AI":
        st.title("🤖 Dokter AI")
        st.caption("Diskusikan keluhan fisik Anda di sini.")
        
        chat_box = st.container(height=400, border=True)
        with chat_box:
            if "msgs" not in st.session_state: st.session_state.msgs = []
            for m in st.session_state.msgs:
                with st.chat_message(m["role"]):
                    st.write(m["content"])
        
        with st.container(border=True):
            c1, c2 = st.columns([1, 5])
            with c1: upl = st.file_uploader("📷", type=["jpg","png"], label_visibility="collapsed")
            with c2: txt = st.chat_input("Keluhan Anda...")
            if upl: st.image(upl, width=100)
            
        if txt:
            with chat_box:
                with st.chat_message("user"): st.write(txt)
            st.session_state.msgs.append({"role":"user", "content":txt})
            
            with st.spinner("Menganalisa..."):
                try:
                    model = genai.GenerativeModel("gemini-flash-latest")
                    prompt = f"Jawab sebagai dokter ramah untuk pasien {st.session_state['nama']}. Beri diagnosa awal & saran obat apotek. "
                    content = [txt]
                    if upl:
                        content.append(PIL.Image.open(upl))
                        prompt += "Analisa gambar medis ini. "
                    content[0] = prompt + content[0]
                    
                    resp = model.generate_content(content)
                    ai_reply = resp.text
                    
                    with chat_box:
                        with st.chat_message("assistant"): st.write(ai_reply)
                    st.session_state.msgs.append({"role":"assistant", "content":ai_reply})
                    save_consultation(st.session_state['username'], txt, ai_reply)
                except Exception as e: st.error("Error Koneksi AI")

    # --- MENU 3: CEK FISIK (BMI & AIR) ---
    elif menu == "Cek Fisik":
        st.title("🧮 Kalkulator Tubuh")
        
        t1, t2 = st.tabs(["Berat Ideal (BMI)", "Kebutuhan Air (Hidrasi)"])
        
        with t1:
            with st.container(border=True):
                st.subheader("Cek BMI")
                c_a, c_b = st.columns(2)
                bb = c_a.number_input("Berat (kg)", 30, 200, 60)
                tb = c_b.number_input("Tinggi (cm)", 100, 250, 170)
                if st.button("Hitung BMI"):
                    bmi = bb / ((tb/100)**2)
                    st.metric("Skor BMI", f"{bmi:.1f}")
                    if bmi < 18.5: st.warning("Underweight")
                    elif 18.5 <= bmi < 25: st.success("Normal")
                    else: st.error("Overweight/Obesitas")

        with t2:
            with st.container(border=True):
                st.subheader("💧 Target Minum Air")
                st.write("Rumus: 30ml x Berat Badan")
                if st.button("Hitung Kebutuhan Air"):
                    air = bb * 30
                    st.info(f"Tubuh Anda butuh minimal **{air} ml** ({round(air/250)} gelas) air per hari.")

    # --- MENU 4: TES MENTAL (FITUR BARU) ---
    elif menu == "Tes Mental":
        st.title("🧠 Skrining Kesehatan Mental")
        st.write("Tes sederhana (PHQ-2) untuk mendeteksi tingkat stres/depresi dini.")
        st.warning("Tes ini bukan diagnosa medis. Hubungi psikolog jika hasil mengkhawatirkan.")
        
        with st.form("mental_test"):
            q1 = st.selectbox("1. Dalam 2 minggu terakhir, seberapa sering Anda merasa sedih/putus asa?", 
                              ["Tidak pernah", "Beberapa hari", "Lebih dari seminggu", "Hampir setiap hari"])
            q2 = st.selectbox("2. Seberapa sering Anda kehilangan minat/senang dalam melakukan sesuatu?", 
                              ["Tidak pernah", "Beberapa hari", "Lebih dari seminggu", "Hampir setiap hari"])
            q3 = st.selectbox("3. Apakah Anda merasa lelah atau kurang bertenaga?", 
                              ["Tidak pernah", "Beberapa hari", "Lebih dari seminggu", "Hampir setiap hari"])
            
            submit_mental = st.form_submit_button("Lihat Hasil & Simpan")
            
            if submit_mental:
                # Logika Skor Sederhana
                mapping = {"Tidak pernah":0, "Beberapa hari":1, "Lebih dari seminggu":2, "Hampir setiap hari":3}
                score = mapping[q1] + mapping[q2] + mapping[q3]
                
                st.divider()
                st.metric("Skor Stres Anda", f"{score}/9")
                
                kategori = ""
                if score <= 2:
                    kategori = "Stabil / Normal"
                    st.success(f"✅ **{kategori}**. Pertahankan gaya hidup sehat Anda.")
                elif score <= 5:
                    kategori = "Stres Ringan"
                    st.warning(f"⚠️ **{kategori}**. Coba istirahat, olahraga, atau curhat ke teman.")
                else:
                    kategori = "Indikasi Depresi"
                    st.error(f"🚨 **{kategori}**. Disarankan berkonsultasi ke profesional.")
                
                # Simpan ke Database Baru
                save_mental_test(st.session_state['username'], score, kategori)

    # --- MENU 5: REKAM MEDIS ---
    elif menu == "Rekam Medis":
        st.title("📂 Riwayat Medis")
        
        tab_chat, tab_mental = st.tabs(["Riwayat Chat AI", "Riwayat Tes Mental"])
        
        with tab_chat:
            hist = get_history_chat(st.session_state['username'])
            if hist:
                for h in hist:
                    with st.expander(f"🗨️ {h[0]} - {h[1][:30]}..."):
                        st.write(f"**Q:** {h[1]}")
                        st.write(f"**A:** {h[2]}")
            else: st.info("Belum ada chat.")

        with tab_mental:
            hist_m = get_history_mental(st.session_state['username'])
            if hist_m:
                for m in hist_m:
                    # m = date, score, category
                    with st.container(border=True):
                        c_a, c_b = st.columns([1, 4])
                        with c_a: st.metric("Skor", f"{m[1]}")
                        with c_b:
                            st.write(f"**Tanggal:** {m[0]}")
                            st.write(f"**Status:** {m[2]}")
            else: st.info("Belum ada tes mental.")

    # --- LOGOUT ---
    elif menu == "Logout":
        st.session_state['logged_in'] = False
        st.rerun()

# --- 6. RUN ---
if __name__ == "__main__":
    if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
    if st.session_state['logged_in']: main_app()
    else: auth_page()