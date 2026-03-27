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
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS: Clean, Minimalist, Light Blue Metallic
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700;800&display=swap');

    html, body, [class*="css"], .stMarkdown, .stText {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    .stApp { 
        background-color: #f4f7fb !important; 
        color: #1b2a4e !important;
        overflow-x: hidden;
    }
    
    .glow-orb { position: fixed; border-radius: 50%; filter: blur(140px); opacity: 0.2; z-index: 0; pointer-events: none; }
    .orb-1 { width: 50vw; height: 50vw; background: #56ccf2; top: -10%; left: -10%; }
    .orb-2 { width: 40vw; height: 40vw; background: #2f80ed; bottom: -10%; right: -10%; }

    .block-container { z-index: 10 !important; position: relative !important; }

    h1, h2, h3 { 
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important; 
        letter-spacing: -0.5px;
    }

    div[data-testid="metric-container"], div[data-testid="stForm"], div[data-testid="stTabs"], .css-card {
        background: rgba(255, 255, 255, 0.85) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(86, 204, 242, 0.2) !important;
        border-radius: 16px !important; 
        padding: 24px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03) !important;
        transition: 0.3s ease !important;
    }
    
    div[data-testid="metric-container"]:hover, .css-card:hover {
        transform: translateY(-3px) !important; 
        border-color: #56ccf2 !important;
        box-shadow: 0 8px 25px rgba(47, 128, 237, 0.1) !important;
    }

    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(0, 0, 0, 0.05) !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%) !important;
        color: white !important; 
        border: none !important; 
        border-radius: 8px !important;
        padding: 10px 24px !important; 
        font-weight: 600 !important;
        transition: 0.3s !important;
    }
    .stButton > button:hover { 
        transform: translateY(-2px) !important; 
        box-shadow: 0 6px 15px rgba(30, 60, 114, 0.3) !important; 
    }

    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox > div > div {
        border-radius: 8px !important;
        border: 1px solid #e2e8f0 !important;
        background-color: #ffffff !important;
        color: #1b2a4e !important;
        padding-left: 15px !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #2a5298 !important;
        box-shadow: 0 0 0 2px rgba(42, 82, 152, 0.2) !important;
    }

    [data-testid="stMetricValue"] { color: #1e3c72 !important; font-weight: 800 !important; font-size: 2.2rem !important; }
    
    .clinical-note { background: #f8fafc; padding: 16px; border-radius: 8px; border-left: 4px solid #3b82f6; font-size: 0.95em; color: #334155; margin-bottom: 10px;}
    
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
    model = genai.GenerativeModel("gemini-1.5-flash") 
except: pass

# MOCK DATA
HUGE_TIPS = [
    "Drinking water 20 minutes before meals helps control portion sizes.",
    "Walking barefoot on natural surfaces can reduce stress indicators.",
    "Replacing refined sugar with natural alternatives stabilizes blood glucose.",
    "A left-side sleeping position is recommended for acid reflux management.",
    "Consuming cooked tomatoes increases Lycopene bioavailability.",
    "Resistance training increases bone density and prevents osteoporosis.",
    "Morning sun exposure regulates circadian rhythms and provides Vitamin D.",
    "Reducing screen time before sleep significantly improves sleep quality."
]

ENCYCLOPEDIA = {
    "Internal Medicine": {
        "Diabetes Mellitus": "A metabolic disease that causes high blood sugar. Symptoms include frequent urination and increased thirst.",
        "Hypertension": "Consistently elevated blood pressure above 140/90 mmHg. A major risk factor for cardiovascular disease.",
        "GERD": "Gastroesophageal reflux disease. A digestive disorder affecting the lower esophageal sphincter."
    },
    "Dermatology": {
        "Atopic Dermatitis": "A condition that makes skin red and itchy, often referred to as eczema.",
        "Acne Vulgaris": "A skin condition that occurs when hair follicles become plugged with oil and dead skin cells.",
        "Psoriasis": "A skin disease that causes red, itchy scaly patches, most commonly on the knees, elbows, trunk and scalp."
    },
    "Mental Health": {
        "Generalized Anxiety Disorder": "Severe, ongoing anxiety that interferes with daily activities.",
        "Major Depressive Disorder": "A mental health disorder characterized by persistently depressed mood or loss of interest.",
        "Insomnia": "A sleep disorder that can make it hard to fall asleep, hard to stay asleep, or cause you to wake up too early."
    }
}

if 'show_login' not in st.session_state: st.session_state['show_login'] = False

# --- 4. AUTHENTICATION FOCUS LAYER (CLEAN DESIGN) ---
def render_auth_layer():
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
        st.markdown("<h2>System Authentication</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color:#64748b;'>Secure portal for MediCare Pro users.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["Sign In", "Register New Account"])
        
        with tab_login:
            user = st.text_input("Username", key="log_user")
            pwd = st.text_input("Password", type="password", key="log_pass")
            if st.button("Authenticate", use_container_width=True):
                with st.spinner("Verifying credentials..."):
                    time.sleep(1)
                    res = login_user(user, pwd)
                    if res:
                        st.session_state.update({'is_logged_in': True, 'username': user, 'nama': res[0][2]})
                        st.session_state['show_login'] = False
                        st.rerun()
                    else: st.error("Authentication failed. Invalid credentials.")
            st.caption("Demo Access: Create a new account in the Register tab to test.")

        with tab_register:
            nu = st.text_input("Desired Username", key="reg_user")
            nn = st.text_input("Full Legal Name", key="reg_name")
            np = st.text_input("Create Password", type="password", key="reg_pass")
            cp = st.text_input("Confirm Password", type="password", key="reg_conf")
            if st.button("Create Account", use_container_width=True):
                with st.spinner("Processing registration..."):
                    time.sleep(1)
                    if np != cp: st.error("Verification failed: Passwords do not match.")
                    elif len(nu) < 3: st.error("Validation failed: Username must be at least 3 characters.")
                    else:
                        if add_user(nu, np, nn):
                            st.success("Registration successful. Proceed to Sign In.")
                        else: st.error("Registration failed: Username already allocated.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Cancel / Return to Dashboard", use_container_width=True):
            st.session_state['show_login'] = False
            st.rerun()

# --- 5. EXCLUSIVE FEATURES ---

def f1_dashboard():
    st.title("Health Operations Dashboard")
    if not st.session_state.get('is_logged_in', False):
        st.info("Guest View Mode Active. Limited functionality.")
    
    st.markdown("<p style='color:#64748b;'>Overview of your clinical and systemic metrics.</p>", unsafe_allow_html=True)
    
    # CLINICAL METRICS (Clean Look)
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("Overall Health Index", "92/100", "+2.5% vs Last Month")
    with m2: st.metric("Active Modules", "14", "System Optimal")
    with m3: st.metric("Upcoming Appointments", "0", "No actions required")
    with m4: st.metric("Data Security", "Encrypted", "End-to-End")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # DASHBOARD CHARTS & INSIGHTS
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Clinical Insight")
        st.markdown(f"<div class='clinical-note'><strong>Daily Recommendation:</strong><br>{random.choice(HUGE_TIPS)}</div>", unsafe_allow_html=True)
        
        st.subheader("System Status")
        st.markdown(f"<div class='clinical-note'><strong>AI Diagnostic Engine:</strong> Online<br><strong>Database Connection:</strong> Secure<br><strong>Last Sync:</strong> {datetime.datetime.now().strftime('%H:%M %p')}</div>", unsafe_allow_html=True)

    with col2:
        st.subheader("Activity Overview (7 Days)")
        # Generating clean mock data
        chart_data = pd.DataFrame(
            np.random.randint(4000, 10000, size=(7, 2)),
            columns=['Steps Recorded', 'Active Calories Burned']
        )
        st.bar_chart(chart_data)

def f2_ai_consult():
    st.title("Dr. AI Clinical Consultant")
    st.caption("Advanced AI diagnostic preliminary support.")
    
    chat_box = st.container(height=400, border=True)
    with chat_box:
        if "msgs" not in st.session_state: st.session_state.msgs = []
        for m in st.session_state.msgs:
            with st.chat_message(m["role"]):
                st.write(m["content"])
    
    with st.container(border=True):
        c1, c2 = st.columns([1, 5])
        with c1: upl = st.file_uploader("Image Analysis", type=["jpg","png"], label_visibility="collapsed")
        with c2: txt = st.chat_input("Input clinical symptoms or inquiries...")
        if upl: st.image(upl, width=150, style={"border-radius":"8px"})
        
    if txt:
        with chat_box:
            with st.chat_message("user"): st.write(txt)
        st.session_state.msgs.append({"role":"user", "content":txt})
        
        with st.spinner("Processing clinical data..."):
            try:
                prompt = f"Respond as a professional medical doctor. Patient name: {st.session_state.get('nama', 'Patient')}. Provide a preliminary analysis based on the symptoms. Use professional medical terminology but keep it understandable. "
                content = [txt]
                if upl:
                    content.append(PIL.Image.open(upl))
                    prompt += "Analyze the provided medical visual. "
                content[0] = prompt + content[0]
                
                resp = model.generate_content(content)
                ai_reply = resp.text
                
                with chat_box:
                    with st.chat_message("assistant"): st.write(ai_reply)
                st.session_state.msgs.append({"role":"assistant", "content":ai_reply})
                save_consultation(st.session_state['username'], txt, ai_reply)
            except Exception as e: st.error("Engine failure. Please verify connection.")

def f3_bmi():
    st.title("Body Mass Index Analysis")
    st.write("Calculate and track your BMI index.")
    c_a, c_b = st.columns(2)
    bb = c_a.number_input("Weight (kg)", 30.0, 200.0, 60.0)
    tb = c_b.number_input("Height (cm)", 100.0, 250.0, 170.0)
    if st.button("Execute Calculation"):
        bmi = bb / ((tb/100)**2)
        st.metric("Calculated BMI", f"{bmi:.2f}")
        if bmi < 18.5: st.warning("Status: Underweight")
        elif 18.5 <= bmi < 25: st.success("Status: Normal Weight")
        else: st.error("Status: Overweight / Obese")

def f4_hydration():
    st.title("Hydration Target Tracker")
    st.write("Calculate optimal daily fluid intake based on body mass.")
    bb = st.number_input("Current Weight (kg)", 30.0, 200.0, 60.0)
    if st.button("Calculate Requirement"):
        air = bb * 30
        st.markdown(f"<div class='clinical-note'><strong>Recommended Intake:</strong> {air} ml per day.</div>", unsafe_allow_html=True)

def f5_mental_test():
    st.title("Psychological Screening (PHQ-2)")
    st.write("Preliminary screening for depression indicators.")
    st.caption("Note: This does not replace formal psychiatric evaluation.")
    
    with st.form("mental_test"):
        opts = ["Not at all", "Several days", "More than half the days", "Nearly every day"]
        q1 = st.selectbox("1. Over the last 2 weeks, how often have you been bothered by feeling down, depressed, or hopeless?", opts)
        q2 = st.selectbox("2. How often have you had little interest or pleasure in doing things?", opts)
        q3 = st.selectbox("3. Have you felt excessively tired or lacked energy?", opts)
        
        if st.form_submit_button("Process Evaluation"):
            mapping = {"Not at all":0, "Several days":1, "More than half the days":2, "Nearly every day":3}
            score = mapping[q1] + mapping[q2] + mapping[q3]
            
            st.divider()
            st.metric("Evaluation Score", f"{score}/9")
            
            kategori = ""
            if score <= 2:
                kategori = "Nominal"
                st.success(f"Result: {kategori}. No significant indicators detected.")
            elif score <= 5:
                kategori = "Mild Indicators"
                st.warning(f"Result: {kategori}. Monitor symptoms and consider stress management.")
            else:
                kategori = "Elevated Indicators"
                st.error(f"Result: {kategori}. Clinical consultation recommended.")
            
            save_mental_test(st.session_state['username'], score, kategori)

def f6_dictionary():
    st.title("Medical Reference Database")
    st.write("Access verified medical terminology and disease information.")
    
    tab_dalam, tab_kulit, tab_jiwa = st.tabs(["Internal Medicine", "Dermatology", "Psychiatry"])
    
    with tab_dalam:
        for k, v in ENCYCLOPEDIA["Internal Medicine"].items():
            with st.expander(f"Reference: {k}"): st.write(v)
    with tab_kulit:
        for k, v in ENCYCLOPEDIA["Dermatology"].items():
            with st.expander(f"Reference: {k}"): st.write(v)
    with tab_jiwa:
        for k, v in ENCYCLOPEDIA["Mental Health"].items():
            with st.expander(f"Reference: {k}"): st.write(v)

def f7_medical_records():
    st.title("Patient Records")
    
    tab_chat, tab_mental = st.tabs(["Diagnostic Queries", "Psychological Logs"])
    
    with tab_chat:
        hist = get_history_chat(st.session_state['username'])
        if hist:
            for h in hist:
                with st.expander(f"Query Log: {h[0]}"):
                    st.write(f"**Input:** {h[1]}")
                    st.write(f"**Output:** {h[2]}")
        else: st.info("No records found in database.")

    with tab_mental:
        hist_m = get_history_mental(st.session_state['username'])
        if hist_m:
            for m in hist_m:
                with st.container(border=True):
                    c_a, c_b = st.columns([1, 4])
                    with c_a: st.metric("Score", f"{m[1]}")
                    with c_b:
                        st.write(f"**Timestamp:** {m[0]}")
                        st.write(f"**Clinical Status:** {m[2]}")
        else: st.info("No records found in database.")

def f8_appointments():
    st.title("Appointment Scheduling")
    st.date_input("Select proposed consultation date", datetime.datetime.now())
    st.table(pd.DataFrame({"Practitioner": ["Dr. Smith, MD", "Dr. Jane, DO"], "Status": ["Scheduled", "Fulfilled"]}))

def f9_medication():
    st.title("Pharmacology Tracker")
    st.write("Active prescriptions and supplements.")
    st.checkbox("Vitamin C 500mg - 08:00 AM", value=True)
    st.checkbox("Omega 3 1000mg - 01:00 PM")

def f10_lab_results():
    st.title("Laboratory Results")
    st.info("Secure document upload for assay results.")
    st.file_uploader("Upload PDF Document", type=["pdf"])

def f11_telehealth():
    st.title("Telehealth Interface")
    st.markdown("<div class='clinical-note'>System ready for secure video transmission. Waiting for practitioner connection.</div>", unsafe_allow_html=True)
    st.button("Terminate Connection")

def f12_activity():
    st.title("Physical Activity Metrics")
    st.metric("Daily Steps", "8,432", "+1,200 vs Average")
    st.bar_chart({"Steps Recorded": [5000, 7000, 8432, 6000]})

def f13_nutrition():
    st.title("Nutritional Intake")
    st.write("Caloric tracking module.")
    st.data_editor(pd.DataFrame({"Meal Type": ["Breakfast", "Lunch"], "Calories (kcal)": [450, 600]}), use_container_width=True)

def f14_hospital():
    st.title("Facility Locator")
    st.write("Proximity map for affiliated healthcare facilities.")
    st.map(pd.DataFrame(np.random.randn(5, 2) / [50, 50] + [-6.8, 108.5], columns=['lat', 'lon']))

def f15_insurance():
    st.title("Policy Administration")
    st.write("**Active Provider:** HealthCare Pro Corporate")
    st.progress(70, "Annual Coverage Utilization (70%)")

def f16_settings():
    st.title("System Preferences")
    st.text_input("Registered Email Address")
    st.toggle("Enable System Notifications", value=True)
    st.button("Update Configuration")

# --- 6. MAIN ROUTING & SMART FOCUS LOGIC ---
def main():
    if 'is_logged_in' not in st.session_state: st.session_state['is_logged_in'] = False
    is_logged = st.session_state['is_logged_in']

    # SIDEBAR
    with st.sidebar:
        if is_logged:
            user = st.session_state.get('nama', 'User')
            st.markdown(f"<h3 style='text-align:center;'>{user}</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; color:#64748b; font-size:0.8rem; margin-top:-10px;'>Authenticated User</p>", unsafe_allow_html=True)
            if st.button("End Session", use_container_width=True):
                st.session_state['is_logged_in'] = False
                st.rerun()
        else:
            st.markdown("<h2 style='text-align:center;'>MediCare Pro</h2>", unsafe_allow_html=True)
            st.write("<p style='text-align:center; color:#64748b; font-size:0.9rem;'>Unauthenticated Access</p>", unsafe_allow_html=True)
            if st.button("Sign In / Register", use_container_width=True):
                st.session_state['show_login'] = True
                st.rerun()

        st.divider()
        menu = option_menu(
            menu_title="Navigation",
            options=[
                "Dashboard", "AI Consult", "BMI Check", "Hydration", "Mental Test", 
                "Dictionary", "Records", "Appointments", "Medication", "Lab Results", 
                "Telehealth", "Activity Log", "Nutrition", "Find Hospital", "Insurance", "Settings"
            ],
            icons=[
                "grid", "cpu", "calculator", "droplet", "activity", 
                "book", "folder", "calendar", "capsule", "file-medical", 
                "camera-video", "graph-up", "egg-fried", "geo-alt", "shield-check", "gear"
            ],
            default_index=0,
            styles={
                "nav-link-selected": {"background": "linear-gradient(135deg, #2a5298 0%, #1e3c72 100%)", "color": "white"},
                "nav-link": {"color": "#1b2a4e", "font-weight": "600", "font-size": "0.9rem", "border-radius": "8px"}
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
            st.markdown("<br><br><br><h2 style='text-align:center;'>Access Denied</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; color:#64748b;'>Authentication required to access this clinical module.</p>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1, 0.5, 1])
            with c2:
                if st.button("Authenticate Now", use_container_width=True):
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