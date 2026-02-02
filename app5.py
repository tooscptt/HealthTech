import streamlit as st
import google.generativeai as genai
import PIL.Image
from streamlit_option_menu import option_menu
import sqlite3
import hashlib
import datetime
import random # Untuk tips acak

# --- 1. KONFIGURASI HALAMAN & CSS MEDIS ---
st.set_page_config(
    page_title="MediCare AI",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Style Elegan & Bersih (Medical Blue)
st.markdown("""
<style>
    /* Background & Font Utama */
    .stApp { background-color: #f4f7f6; }
    h1, h2, h3, h4 { color: #0277bd; font-family: 'Segoe UI', sans-serif; }
    
    /* Tombol Biru Medis */
    .stButton>button {
        background-color: #0288d1; color: white; border-radius: 8px; border: none;
        height: 3em; font-weight: bold; transition: 0.3s;
    }
    .stButton>button:hover { background-color: #01579b; }

    /* Container Kotak Putih (Card Effect) */
    .css-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border-left: 5px solid #0288d1;
    }
    
    /* Highlight Mitos/Fakta */
    .mitos { background-color: #ffebee; padding: 10px; border-radius: 8px; border: 1px solid #ef5350; }
    .fakta { background-color: #e8f5e9; padding: 10px; border-radius: 8px; border: 1px solid #66bb6a; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE MANAGEMENT (SQLite) ---
def init_db():
    conn = sqlite3.connect('medicare.db')
    c = conn.cursor()
    # Tabel User
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, nama_lengkap TEXT)''')
    # Tabel Riwayat Chat
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

init_db()

# --- 3. API KEY CONFIG ---
try:
    if "API_KEY" in st.secrets: api_key = st.secrets["API_KEY"]
    else: api_key = "MASUKKAN_KEY_LOKAL_JIKA_ADA"
    if api_key and "MASUKKAN" not in api_key: genai.configure(api_key=api_key)
except: pass

# --- 4. DATA EDUKASI STATIS (CONTENT DATABASE) ---
TIPS_LIST = [
    "Minum air putih minimal 8 gelas sehari membantu ginjal menyaring racun.",
    "Jalan kaki 30 menit sehari bisa menurunkan risiko penyakit jantung hingga 30%.",
    "Kurangi garam! Konsumsi garam berlebih memicu hipertensi.",
    "Tidur 7-8 jam per malam meningkatkan sistem imun tubuh secara signifikan.",
    "Stres berlebih dapat memicu masalah pencernaan (GERD). Luangkan waktu untuk relaksasi."
]

# --- 5. HALAMAN LOGIN ---
def auth_page():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container(border=True):
            st.markdown("<h1 style='text-align: center;'>🏥 MediCare AI</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: grey;'>Sistem Pintar Kesehatan Keluarga</p>", unsafe_allow_html=True)
            
            # Gambar Ilustrasi (Emoji Besar aman)
            st.markdown("<h1 style='text-align: center; font-size: 60px;'>👨‍⚕️</h1>", unsafe_allow_html=True)

            tab1, tab2 = st.tabs(["Masuk", "Daftar Baru"])
            
            with tab1:
                with st.form("login"):
                    user = st.text_input("Username")
                    pwd = st.text_input("Password", type="password")
                    if st.form_submit_button("Masuk", type="primary"):
                        res = login_user(user, pwd)
                        if res:
                            st.session_state.update({'logged_in': True, 'username': user, 'nama': res[0][2]})
                            st.rerun()
                        else: st.error("Akun tidak ditemukan")
            
            with tab2:
                with st.form("register"):
                    new_u = st.text_input("Username Baru")
                    new_n = st.text_input("Nama Lengkap")
                    new_p = st.text_input("Password Baru", type="password")
                    if st.form_submit_button("Daftar"):
                        if add_user(new_u, new_p, new_n): st.success("Berhasil! Silakan Login.")
                        else: st.error("Username sudah dipakai.")

# --- 6. DASHBOARD UTAMA ---
def main_app():
    # Sidebar
    with st.sidebar:
        st.header(f"Hai, {st.session_state['nama'].split()[0]}!")
        selected = option_menu(
            menu_title=None,
            options=["Beranda", "Konsultasi AI", "Cek Kesehatan", "Rekam Medis", "Logout"],
            icons=["house", "chat-dots", "heart-pulse", "journal-medical", "box-arrow-left"],
            default_index=0,
            styles={"nav-link-selected": {"background-color": "#0288d1"}}
        )
        
        # Quote Sidebar
        st.markdown("---")
        st.caption("💪 *Kesehatan adalah investasi terbaik Anda.*")

    # --- PAGE 1: BERANDA / DASHBOARD EDUKASI ---
    if selected == "Beranda":
        # Header Sapaan
        st.markdown(f"# Selamat Datang, {st.session_state['nama']}! 👋")
        st.write("Semoga hari Anda sehat dan menyenangkan. Berikut update kesehatan untuk Anda.")
        st.divider()

        # 1. TIPS HARIAN (Random)
        with st.container(border=True):
            col_icon, col_text = st.columns([1, 6])
            with col_icon:
                st.markdown("<h1>💡</h1>", unsafe_allow_html=True)
            with col_text:
                st.subheader("Tips Sehat Hari Ini")
                st.info(random.choice(TIPS_LIST))

        # 2. MITOS VS FAKTA (Grid Layout)
        st.subheader("🤔 Mitos atau Fakta?")
        st.write("Jangan mudah tertipu info kesehatan yang beredar di grup WhatsApp!")
        
        c1, c2 = st.columns(2)
        with c1:
            with st.container(border=True):
                st.markdown("### 🥶 Masuk Angin")
                st.markdown('<div class="mitos"><b>MITOS:</b> Kerokan bisa "mengeluarkan angin" dari dalam tubuh.</div>', unsafe_allow_html=True)
                st.write("")
                st.markdown('<div class="fakta"><b>FAKTA:</b> Kerokan hanya melebarkan pembuluh darah di kulit, memberi sensasi hangat dan rileks sementara, bukan mengeluarkan angin.</div>', unsafe_allow_html=True)
        
        with c2:
            with st.container(border=True):
                st.markdown("### 🚿 Mandi Malam")
                st.markdown('<div class="mitos"><b>MITOS:</b> Mandi malam pasti menyebabkan rematik di masa tua.</div>', unsafe_allow_html=True)
                st.write("")
                st.markdown('<div class="fakta"><b>FAKTA:</b> Tidak ada bukti medis langsung. Namun, mandi air dingin saat malam bisa memperparah nyeri sendi bagi yang <b>sudah punya</b> rematik.</div>', unsafe_allow_html=True)

        st.write("") # Spacer

        # 3. POJOK EDUKASI (Expanders)
        st.subheader("📚 Pustaka Penyakit Umum")
        
        with st.expander("🩸 Hipertensi (Darah Tinggi) - Si Pembunuh Senyap"):
            st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b2/Sphygmomanometer_&_Cuff.jpg/320px-Sphygmomanometer_&_Cuff.jpg", width=200)
            st.write("""
            **Apa itu?** Tekanan darah sistolik ≥ 140 mmHg atau diastolik ≥ 90 mmHg.
            **Bahaya:** Sering tanpa gejala, tapi bisa menyebabkan stroke dan serangan jantung.
            **Pencegahan:**
            1. Kurangi garam (max 1 sdt/hari).
            2. Olahraga rutin.
            3. Hindari rokok dan alkohol.
            """)
        
        with st.expander("🍭 Diabetes Melitus (Kencing Manis)"):
            st.write("""
            **Gejala Klasik (3P):**
            - Polidipsi (Sering haus)
            - Poliuri (Sering pipis malam hari)
            - Polifagi (Cepat lapar)
            
            **Tips:** Batasi gula, nasi putih, dan tepung. Perbanyak sayur dan aktivitas fisik.
            """)
            
        with st.expander("🧠 Kesehatan Mental (Stress & Anxiety)"):
            st.write("""
            Kesehatan mental sama pentingnya dengan fisik.
            Jika Anda merasa cemas berlebihan, sulit tidur, atau kehilangan minat, jangan ragu mencari bantuan profesional.
            **Tips Relaksasi:** Latihan pernapasan 4-7-8 (Tarik 4s, Tahan 7s, Hembus 8s).
            """)

    # --- PAGE 2: KONSULTASI AI ---
    elif selected == "Konsultasi AI":
        st.title("🩺 Dokter AI Pribadi")
        st.caption("AI kami siap menganalisa keluhan atau foto medis Anda 24/7.")

        # Chat Container
        chat_box = st.container(height=400, border=True)
        with chat_box:
            if "messages" not in st.session_state: st.session_state.messages = []
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # Input Area
        with st.container(border=True):
            col_img, col_txt = st.columns([1, 5])
            with col_img:
                upl = st.file_uploader("📷", type=["jpg","png"], label_visibility="collapsed")
            with col_txt:
                txt = st.chat_input("Jelaskan keluhan Anda...")
            
            if upl: st.image(upl, width=100, caption="Preview")

        if txt:
            # User Msg
            with chat_box:
                with st.chat_message("user"):
                    st.write(txt)
                    if upl: st.image(upl, width=200)
            st.session_state.messages.append({"role":"user", "content":txt})

            # AI Logic
            with st.spinner("Menganalisa gejala..."):
                try:
                    model = genai.GenerativeModel("gemini-flash-latest")
                    content = [txt]
                    prompt = "Kamu dokter AI. Beri diagnosa awal, saran obat apotek (OTC), dan kapan harus ke RS. Jawab ringkas."
                    if upl:
                        content.append(PIL.Image.open(upl))
                        prompt += " Analisa gambar visual ini."
                    content[0] = prompt + content[0]

                    resp = model.generate_content(content)
                    ai_reply = resp.text

                    # AI Msg
                    with chat_box:
                        with st.chat_message("assistant"):
                            st.markdown(ai_reply)
                    st.session_state.messages.append({"role":"assistant", "content":ai_reply})
                    save_consultation(st.session_state['username'], txt, ai_reply)
                except Exception as e: st.error("Gagal koneksi.")

    # --- PAGE 3: CEK KESEHATAN ---
    elif selected == "Cek Kesehatan":
        st.title("🧮 Kalkulator Kesehatan")
        st.write("Alat bantu hitung kondisi tubuh mandiri.")
        
        tab_bmi, tab_kalori = st.tabs(["Indeks Massa Tubuh (BMI)", "Kebutuhan Kalori"])
        
        with tab_bmi:
            with st.container(border=True):
                st.subheader("Cek Berat Ideal")
                c1, c2 = st.columns(2)
                bb = c1.number_input("Berat (kg)", 30, 150, 60)
                tb = c2.number_input("Tinggi (cm)", 100, 250, 170)
                if st.button("Hitung BMI"):
                    bmi = bb / ((tb/100)**2)
                    st.metric("Skor BMI Anda", f"{bmi:.1f}")
                    if bmi < 18.5: st.warning("Kurus (Underweight)")
                    elif 18.5 <= bmi < 25: st.success("Normal (Ideal) ✅")
                    elif 25 <= bmi < 30: st.warning("Gemuk (Overweight)")
                    else: st.error("Obesitas ⚠️")

        with tab_kalori:
            with st.container(border=True):
                st.subheader("BMR (Basal Metabolic Rate)")
                us = st.slider("Usia", 15, 80, 25)
                gen = st.radio("Gender", ["Laki-laki", "Perempuan"])
                if st.button("Hitung Kalori Harian"):
                    if gen == "Laki-laki": cal = 88.36 + (13.4*bb) + (4.8*tb) - (5.7*us)
                    else: cal = 447.6 + (9.2*bb) + (3.1*tb) - (4.3*us)
                    st.info(f"Tubuh Anda membakar **{int(cal)} kkal** saat istirahat.")

    # --- PAGE 4: REKAM MEDIS ---
    elif selected == "Rekam Medis":
        st.title("📂 Riwayat Konsultasi")
        history = get_history(st.session_state['username'])
        if not history:
            st.info("Belum ada data konsultasi. Silakan chat dengan dokter AI.")
        else:
            for item in history:
                with st.expander(f"📅 {item[0]} - {item[1][:40]}..."):
                    st.markdown(f"**Q:** {item[1]}")
                    st.markdown(f"**A:** {item[2]}")

    # --- LOGOUT ---
    elif selected == "Logout":
        st.session_state.logged_in = False
        st.rerun()

# --- 7. MAIN RUN ---
if __name__ == "__main__":
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if st.session_state.logged_in: main_app()
    else: auth_page()