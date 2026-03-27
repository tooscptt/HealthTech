import streamlit as st
import google.generativeai as genai
import PIL.Image
from streamlit_option_menu import option_menu
import sqlite3
import hashlib
import datetime
import random
import pandas as pd
import numpy as np
import time

# --- 1. PAGE CONFIGURATION & METALLIC BLUE DESIGN SYSTEM ---
st.set_page_config(
    page_title="MediCare Pro",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS: Light Blue Metallic, Glassmorphism, Ultra-Rounded
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700;800&display=swap');

    /* Background & Font */
    html, body, [class*="css"], .stMarkdown, .stText {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    .stApp { 
        background-color: #f0f8ff !important; /* Alice Blue */
        color: #1b2a4e !important;
        overflow-x: hidden;
    }
    
    /* Glow Orbs (Light Blue Theme) */
    .glow-orb { position: fixed; border-radius: 50%; filter: blur(120px); opacity: 0.3; z-index: 0; pointer-events: none; }
    .orb-1 { width: 50vw; height: 50vw; background: #56ccf2; top: -10%; left: -10%; }
    .orb-2 { width: 40vw; height: 40vw; background: #2f80ed; bottom: -10%; right: -10%; }

    .block-container { z-index: 10 !important; position: relative !important; }

    /* Metallic Text (Blue Gradient) */
    h1, h2, h3 { 
        background: linear-gradient(135deg, #56ccf2 0%, #2f80ed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important; 
        letter-spacing: -0.5px;
    }

    /* Glassmorphism Cards (Ultra-Rounded) */
    div[data-testid="metric-container"], div[data-testid="stForm"], div[data-testid="stTabs"], .css-card {
        background: rgba(255, 255, 255, 0.7) !important;
        backdrop-filter: blur(15px) !important;
        -webkit-backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(86, 204, 242, 0.3) !important;
        border-radius: 25px !important; 
        padding: 20px !important;
        box-shadow: 0 10px 30px rgba(47, 128, 237, 0.1), inset 0 0 15px rgba(255,255,255,0.5) !important;
        transition: 0.4s ease !important;
    }
    
    div[data-testid="metric-container"]:hover, .css-card:hover {
        transform: translateY(-5px) !important; 
        border-color: #56ccf2 !important;
        box-shadow: 0 15px 40px rgba(47, 128, 237, 0.15), inset 0 0 15px rgba(255,255,255,0.8) !important;
    }

    /* Seamless Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.8) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(86, 204, 242, 0.2) !important;
    }

    /* Capsule Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #56ccf2 0%, #2f80ed 100%) !important;
        color: white !important; 
        border: none !important; 
        border-radius: 50px !important;
        padding: 10px 25px !important; 
        font-weight: 700 !important;
        box-shadow: 0 5px 20px rgba(86, 204, 242, 0.4) !important; 
        transition: 0.3s !important;
    }
    .stButton > button:hover { 
        transform: scale(1.03) !important; 
        box-shadow: 0 8px 25px rgba(86, 204, 242, 0.6) !important; 
    }

    /* Capsule Inputs */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox > div > div {
        border-radius: 30px !important;
        border: 1px solid rgba(86, 204, 242, 0.3) !important;
        background-color: rgba(255,255,255,0.8) !important;
        color: #1b2a4e !important;
        padding-left: 15px !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #56ccf2 !important;
        box-shadow: 0 0 10px rgba(86, 204, 242, 0.3) !important;
    }

    /* Metrics Styling */
    [data-testid="stMetricValue"] { color: #2f80ed !important; font-weight: 900 !important; font-size: 2.5rem !important; }
    
    /* Myth/Fact Boxes */
    .mitos { background: rgba(255, 235, 238, 0.8); padding: 15px; border-radius: 15px; border-left: 5px solid #ef5350; font-size: 0.95em; color: #c62828;}
    .fakta { background: rgba(232, 245, 233, 0.8); padding: 15px; border-radius: 15px; border-left: 5px solid #66bb6a; font-size: 0.95em; color: #2e7d32;}

    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
</style>
<div class="glow-orb orb-1"></div>
<div class="glow-orb orb-2"></div>
""", unsafe_allow_html=True)

# --- 2. DATABASE MANAGEMENT (SQLite) ---
def init_db():
    conn = sqlite3.connect('medicare_pro.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, nama_lengkap TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS consultations 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, 
                  date TEXT, question TEXT, answer TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mental_logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, 
                  date TEXT, score INTEGER, category TEXT)''')
    conn.commit()
    conn.close()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def add_user(username, password, nama):
    conn = sqlite3.connect('medicare_pro.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users(username, password, nama_lengkap) VALUES (?,?,?)', 
                  (username, make_hashes(password), nama))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def login_user(username, password):
    conn = sqlite3.connect('medicare_pro.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username =? AND password = ?', 
              (username, make_hashes(password)))
    data = c.fetchall()
    conn.close()
    return data

def save_consultation(username, question, answer):
    conn = sqlite3.connect('medicare_pro.db')
    c = conn.cursor()
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute('INSERT INTO consultations(username, date, question, answer) VALUES (?,?,?,?)', 
              (username, date, question, answer))
    conn.commit()
    conn.close()

def save_mental_test(username, score, category):
    conn = sqlite3.connect('medicare_pro.db')
    c = conn.cursor()
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute('INSERT INTO mental_logs(username, date, score, category) VALUES (?,?,?,?)', 
              (username, date, score, category))
    conn.commit()
    conn.close()

def get_history_chat(username):
    conn = sqlite3.connect('medicare_pro.db')
    c = conn.cursor()
    c.execute('SELECT date, question, answer FROM consultations WHERE username=? ORDER BY id DESC', (username,))
    data = c.fetchall()
    conn.close()
    return data

def get_history_mental(username):
    conn = sqlite3.connect('medicare_pro.db')
    c = conn.cursor()
    c.execute('SELECT date, score, category FROM mental_logs WHERE username=? ORDER BY id DESC', (username,))
    data = c.fetchall()
    conn.close()
    return data

init_db()

# --- 3. API KEY & CONTENT DATA ---
try:
    if "API_KEY" in st.secrets: api_key = st.secrets["API_KEY"]
    else: api_key = ""
    if api_key: genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash") # Upgrade to faster model
except: pass

# MOCK DATA
HUGE_TIPS = [
    "Drinking water 20 minutes before meals helps control portion sizes.",
    "Walking barefoot on grass (earthing) can reduce stress.",
    "Replace white sugar with stevia or honey for more stable blood sugar.",
    "Sleeping on your left side is good for acid reflux (GERD) sufferers.",
    "Consuming cooked tomatoes is better than raw because the Lycopene content increases.",
    "Weightlifting increases bone density and prevents osteoporosis.",
    "Morning sun exposure (8-10 AM) is the best source of Vitamin D.",
    "Reading a book before bed is better than scrolling your phone for sleep quality.",
    "Washing hands with soap for 20 seconds kills 99% of germs.",
    "Meditating 10 minutes a day can lower high blood pressure.",
    "Eating slowly (chewing 32 times) helps digestion and prevents bloating."
]

MYTH_FACTS = [
    {"title": "Catching a Cold", "m": "'Kerokan' (coin rubbing) expels wind from the body.", "f": "It only widens the capillary blood vessels in the skin."},
    {"title": "Night Showers", "m": "Night showers cause rheumatism.", "f": "Cold water only triggers pain in sufferers who ALREADY have rheumatism."},
    {"title": "Carrots & Eyes", "m": "Eating lots of carrots cures nearsightedness.", "f": "Vitamin A only maintains eye health, it cannot reduce nearsightedness."},
    {"title": "Coffee & Heart", "m": "Drinking coffee definitely causes heart disease.", "f": "Moderate coffee consumption (1-2 cups) actually contains good antioxidants."},
    {"title": "Vaccines", "m": "Vaccines cause autism in children.", "f": "Global research proves there is no connection between vaccines and autism."},
    {"title": "Chocolate", "m": "Chocolate causes acne.", "f": "The sugar and milk in chocolate trigger acne, not the pure cocoa."}
]

ENCYCLOPEDIA = {
    "Internal Medicine": {
        "Diabetes": "High blood sugar levels because insulin is not working optimally. Symptoms: Frequent thirst, frequent urination.",
        "Hypertension": "Blood pressure >140/90 mmHg. Often without symptoms but triggers strokes.",
        "GERD": "Stomach acid rises into the esophagus. Avoid spicy food, coffee, and sleeping right after eating."
    },
    "Dermatology": {
        "Eczema": "Itchy, red, dry skin inflammation. Usually due to allergies or stress.",
        "Acne": "Blockage of hair follicles by oil and dead skin cells.",
        "Tinea Versicolor": "Fungal infection on the skin. Itchy white/brown patches when sweating."
    },
    "Mental Health": {
        "Anxiety": "Excessive anxiety that is difficult to control. Symptoms: Palpitations, cold sweat.",
        "Burnout": "Physical & emotional exhaustion due to prolonged work stress.",
        "Insomnia": "Difficulty falling asleep or staying asleep soundly."
    }
}

if 'show_login' not in st.session_state: st.session_state['show_login'] = False

# --- 4. AUTHENTICATION FOCUS LAYER (POPUP STYLE) ---
def render_auth_layer():
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
        st.markdown("<h2>🔐 Secure Authentication</h2>", unsafe_allow_html=True)
        st.write("Please sign in or create an account to unlock Premium Medical Features.")
        st.markdown("</div>", unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["Sign In", "Create Account"])
        
        with tab_login:
            user = st.text_input("Username", key="log_user")
            pwd = st.text_input("Password", type="password", key="log_pass")
            if st.button("Sign In ➔", use_container_width=True):
                with st.spinner("Connecting..."):
                    time.sleep(1)
                    res = login_user(user, pwd)
                    if res:
                        st.session_state.update({'is_logged_in': True, 'username': user, 'nama': res[0][2]})
                        st.session_state['show_login'] = False
                        st.rerun()
                    else: st.error("❌ Invalid username or password!")
            st.caption("💡 **Demo:** Create an account first or use your registered account.")

        with tab_register:
            nu = st.text_input("Choose Username", key="reg_user")
            nn = st.text_input("Full Name", key="reg_name")
            np = st.text_input("Create Password", type="password", key="reg_pass")
            cp = st.text_input("Confirm Password", type="password", key="reg_conf")
            if st.button("Register Account ➔", use_container_width=True):
                with st.spinner("Creating account..."):
                    time.sleep(1)
                    if np != cp: st.error("❌ Passwords do not match!")
                    elif len(nu) < 3: st.error("❌ Username too short!")
                    else:
                        if add_user(nu, np, nn):
                            st.success("✅ Registration successful! Please Sign In.")
                        else: st.error("❌ Username already exists.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("❌ Close / Back", use_container_width=True):
            st.session_state['show_login'] = False
            st.rerun()

# --- 5. 15+ EXCLUSIVE FEATURES (1 PAGE = 1 FEATURE) ---

def f1_dashboard():
    st.title("Main Health Dashboard")
    if not st.session_state.get('is_logged_in', False):
        st.info("👀 **Guest Mode:** You are viewing the public dashboard preview.")
    
    st.write("Latest information for your healthy lifestyle.")
    
    # A. DAILY TIPS
    with st.container(border=True):
        c1, c2 = st.columns([1, 8])
        with c1: st.markdown("<h1 style='font-size:3rem; margin:0;'>💡</h1>", unsafe_allow_html=True)
        with c2:
            st.subheader("Tip of the Day")
            st.write(random.choice(HUGE_TIPS))

    st.markdown("<br>", unsafe_allow_html=True)

    # B. MYTH VS FACT
    st.subheader("🧐 Myth vs Fact")
    daily_myths = random.sample(MYTH_FACTS, 3)
    cols = st.columns(3)
    for idx, col in enumerate(cols):
        with col:
            with st.container(border=True):
                st.markdown(f"**{daily_myths[idx]['title']}**")
                st.markdown(f'<div class="mitos">❌ {daily_myths[idx]["m"]}</div>', unsafe_allow_html=True)
                st.markdown("<div style='text-align:center; font-weight:bold; margin:5px 0;'>VS</div>", unsafe_allow_html=True)
                st.markdown(f'<div class="fakta">✅ {daily_myths[idx]["f"]}</div>', unsafe_allow_html=True)

def f2_ai_consult():
    st.title("🤖 Dr. AI Consultant")
    st.caption("Discuss your physical complaints here.")
    
    chat_box = st.container(height=400, border=True)
    with chat_box:
        if "msgs" not in st.session_state: st.session_state.msgs = []
        for m in st.session_state.msgs:
            with st.chat_message(m["role"]):
                st.write(m["content"])
    
    with st.container(border=True):
        c1, c2 = st.columns([1, 5])
        with c1: upl = st.file_uploader("📷", type=["jpg","png"], label_visibility="collapsed")
        with c2: txt = st.chat_input("Your complaint...")
        if upl: st.image(upl, width=100, style={"border-radius":"10px"})
        
    if txt:
        with chat_box:
            with st.chat_message("user"): st.write(txt)
        st.session_state.msgs.append({"role":"user", "content":txt})
        
        with st.spinner("Analyzing..."):
            try:
                prompt = f"Answer as a friendly doctor for patient {st.session_state.get('nama', 'Guest')}. Give initial diagnosis & pharmacy drug suggestions in English. "
                content = [txt]
                if upl:
                    content.append(PIL.Image.open(upl))
                    prompt += "Analyze this medical image. "
                content[0] = prompt + content[0]
                
                resp = model.generate_content(content)
                ai_reply = resp.text
                
                with chat_box:
                    with st.chat_message("assistant"): st.write(ai_reply)
                st.session_state.msgs.append({"role":"assistant", "content":ai_reply})
                save_consultation(st.session_state['username'], txt, ai_reply)
            except Exception as e: st.error("AI Connection Error")

def f3_bmi():
    st.title("⚖️ BMI Smart Check")
    st.write("Calculate your Body Mass Index.")
    c_a, c_b = st.columns(2)
    bb = c_a.number_input("Weight (kg)", 30.0, 200.0, 60.0)
    tb = c_b.number_input("Height (cm)", 100.0, 250.0, 170.0)
    if st.button("Calculate BMI"):
        bmi = bb / ((tb/100)**2)
        st.metric("BMI Score", f"{bmi:.1f}")
        if bmi < 18.5: st.warning("Underweight")
        elif 18.5 <= bmi < 25: st.success("Normal (Ideal)")
        else: st.error("Overweight / Obese")

def f4_hydration():
    st.title("💧 Hydration Target")
    st.write("Formula: 30ml x Body Weight")
    bb = st.number_input("Enter your weight (kg)", 30.0, 200.0, 60.0)
    if st.button("Calculate Water Needs"):
        air = bb * 30
        st.info(f"Your body needs a minimum of **{air} ml** (approx {round(air/250)} glasses) of water per day.")

def f5_mental_test():
    st.title("🧠 Mental Health Screening")
    st.write("Simple test (PHQ-2) to detect early stress/depression levels.")
    st.warning("This test is not a medical diagnosis. Contact a psychologist if results are concerning.")
    
    with st.form("mental_test"):
        opts = ["Never", "Several days", "More than a week", "Nearly every day"]
        q1 = st.selectbox("1. Over the last 2 weeks, how often have you been bothered by feeling down, depressed, or hopeless?", opts)
        q2 = st.selectbox("2. How often have you had little interest or pleasure in doing things?", opts)
        q3 = st.selectbox("3. Have you felt tired or had little energy?", opts)
        
        if st.form_submit_button("View Results & Save"):
            mapping = {"Never":0, "Several days":1, "More than a week":2, "Nearly every day":3}
            score = mapping[q1] + mapping[q2] + mapping[q3]
            
            st.divider()
            st.metric("Your Stress Score", f"{score}/9")
            
            kategori = ""
            if score <= 2:
                kategori = "Stable / Normal"
                st.success(f"✅ **{kategori}**. Keep up your healthy lifestyle.")
            elif score <= 5:
                kategori = "Mild Stress"
                st.warning(f"⚠️ **{kategori}**. Try resting, exercising, or talking to a friend.")
            else:
                kategori = "Depression Indication"
                st.error(f"🚨 **{kategori}**. Consulting a professional is recommended.")
            
            save_mental_test(st.session_state['username'], score, kategori)

def f6_dictionary():
    st.title("📚 Medical Dictionary")
    st.write("Your pocket health dictionary.")
    
    tab_dalam, tab_kulit, tab_jiwa = st.tabs(["Internal Medicine", "Dermatology", "Mental Health"])
    
    with tab_dalam:
        for k, v in ENCYCLOPEDIA["Internal Medicine"].items():
            with st.expander(f"🩺 {k}"): st.write(v)
    with tab_kulit:
        for k, v in ENCYCLOPEDIA["Dermatology"].items():
            with st.expander(f"🧴 {k}"): st.write(v)
    with tab_jiwa:
        for k, v in ENCYCLOPEDIA["Mental Health"].items():
            with st.expander(f"🧠 {k}"): st.write(v)

def f7_medical_records():
    st.title("📂 Medical Records")
    
    tab_chat, tab_mental = st.tabs(["AI Chat History", "Mental Test History"])
    
    with tab_chat:
        hist = get_history_chat(st.session_state['username'])
        if hist:
            for h in hist:
                with st.expander(f"🗨️ {h[0]} - {h[1][:30]}..."):
                    st.write(f"**Q:** {h[1]}")
                    st.write(f"**A:** {h[2]}")
        else: st.info("No chat history yet.")

    with tab_mental:
        hist_m = get_history_mental(st.session_state['username'])
        if hist_m:
            for m in hist_m:
                with st.container(border=True):
                    c_a, c_b = st.columns([1, 4])
                    with c_a: st.metric("Score", f"{m[1]}")
                    with c_b:
                        st.write(f"**Date:** {m[0]}")
                        st.write(f"**Status:** {m[2]}")
        else: st.info("No mental test history yet.")

def f8_appointments():
    st.title("📅 Appointments")
    st.date_input("Schedule a visit with a doctor", datetime.datetime.now())
    st.table(pd.DataFrame({"Doctor": ["Dr. Smith", "Dr. Jane"], "Date": ["Upcoming", "Completed"]}))

def f9_medication():
    st.title("💊 Medication Plan")
    st.write("Track your daily pills.")
    st.checkbox("Vitamin C - 08:00 AM", value=True)
    st.checkbox("Omega 3 - 01:00 PM")

def f10_lab_results():
    st.title("🔬 Lab Results")
    st.info("Upload or view your recent blood work and scans.")
    st.file_uploader("Upload Lab PDF", type=["pdf"])

def f11_telehealth():
    st.title("📞 Telehealth Call")
    st.image("https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=800", caption="Connecting to Doctor...")
    st.button("End Call", type="primary")

def f12_activity():
    st.title("🏃‍♂️ Activity Log")
    st.metric("Steps Today", "8,432", "+1,200")
    st.bar_chart({"Steps": [5000, 7000, 8432, 6000]})

def f13_nutrition():
    st.title("🥗 Nutrition Plan")
    st.write("Log your daily meals.")
    st.data_editor(pd.DataFrame({"Meal": ["Breakfast", "Lunch"], "Calories": [450, 600]}), use_container_width=True)

def f14_hospital():
    st.title("🏥 Find Hospital")
    st.map(pd.DataFrame(np.random.randn(5, 2) / [50, 50] + [-6.8, 108.5], columns=['lat', 'lon']))

def f15_insurance():
    st.title("🛡️ Insurance Manager")
    st.write("**Provider:** HealthCare Pro")
    st.progress(70, "Annual Limit Used (70%)")

def f16_settings():
    st.title("⚙️ Profile Settings")
    st.text_input("Update Email")
    st.toggle("Push Notifications", value=True)
    st.button("Save Changes")

# --- 6. MAIN ROUTING & SMART FOCUS LOGIC ---
def main():
    if 'is_logged_in' not in st.session_state: st.session_state['is_logged_in'] = False
    is_logged = st.session_state['is_logged_in']

    # SIDEBAR
    with st.sidebar:
        if is_logged:
            user = st.session_state.get('nama', 'User')
            st.markdown(f"<h2 style='text-align:center;'>Welcome,<br>{user}!</h2>", unsafe_allow_html=True)
            if st.button("Logout", use_container_width=True):
                st.session_state['is_logged_in'] = False
                st.rerun()
        else:
            st.markdown("<h2 style='text-align:center;'>MediCare Pro</h2>", unsafe_allow_html=True)
            st.write("<p style='text-align:center; color:#6c757d; font-size:0.9rem;'>Guest Mode</p>", unsafe_allow_html=True)
            if st.button("🔐 Sign In / Register", use_container_width=True):
                st.session_state['show_login'] = True
                st.rerun()

        st.divider()
        menu = option_menu(
            menu_title="Core Modules",
            options=[
                "Dashboard", "AI Consult", "BMI Check", "Hydration", "Mental Test", 
                "Dictionary", "Records", "Appointments", "Medication", "Lab Results", 
                "Telehealth", "Activity Log", "Nutrition", "Find Hospital", "Insurance", "Settings"
            ],
            icons=[
                "house", "robot", "calculator", "droplet", "brain", 
                "book", "folder", "calendar", "capsule", "file-medical", 
                "camera-video", "activity", "egg-fried", "geo-alt", "shield-check", "gear"
            ],
            default_index=0,
            styles={
                "nav-link-selected": {"background": "linear-gradient(135deg, #56ccf2 0%, #2f80ed 100%)", "color": "white"},
                "nav-link": {"color": "#1b2a4e", "font-weight": "600", "font-size": "0.9rem", "border-radius": "15px"}
            }
        )

    # RENDER SMART FOCUS LAYER
    if st.session_state['show_login'] and not is_logged:
        render_auth_layer()
        st.stop()

    # MAIN CONTENT ROUTING
    if menu == "Dashboard": f1_dashboard()
    else:
        if not is_logged:
            st.markdown("<br><br><br><h1 style='text-align:center;'>🔒 Access Restricted</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; color:#6c757d;'>Please sign in to unlock this medical feature.</p>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1, 0.5, 1])
            with c2:
                if st.button("Sign In to Access ➔", use_container_width=True):
                    st.session_state['show_login'] = True
                    st.rerun()
        else:
            if menu == "AI Consult": f2_ai_consult()
            elif menu == "BMI Check": f3_bmi()
            elif menu == "Hydration": f4_hydration()
            elif menu == "Mental Test": f5_mental_test()
            elif menu == "Dictionary": f6_dictionary()
            elif menu == "Records": f7_medical_records()
            elif menu == "Appointments": f8_appointments()
            elif menu == "Medication": f9_medication()
            elif menu == "Lab Results": f10_lab_results()
            elif menu == "Telehealth": f11_telehealth()
            elif menu == "Activity Log": f12_activity()
            elif menu == "Nutrition": f13_nutrition()
            elif menu == "Find Hospital": f14_hospital()
            elif menu == "Insurance": f15_insurance()
            elif menu == "Settings": f16_settings()

if __name__ == "__main__":
    main()