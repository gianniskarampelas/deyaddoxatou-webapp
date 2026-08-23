import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ---------------------------------------------------------
# 1. ΡΥΘΜΙΣΗ ΣΕΛΙΔΑΣ & CSS
# ---------------------------------------------------------
st.set_page_config(page_title="ΔΕΥΑ Δοξάτου - Streamlit", page_icon="💧", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size:2.2rem; color:#0284c7; font-weight:bold; }
    .stButton>button { background-color: #0284c7; color: white; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. ΒΑΣΗ ΔΕΔΟΜΕΝΩΝ (SQLite)
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect('streamlit_deyad.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            category TEXT,
            priority TEXT,
            status TEXT,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------
# 3. AUTHENTICATION (Session State)
# ---------------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.markdown("<h1 class='main-title'>💧 Δ.Ε.Υ.Α. Δοξάτου</h1>", unsafe_allow_html=True)
    st.subheader("Είσοδος στο Σύστημα")

    col1, col2 = st.columns([1, 2])
    with col1:
        user = st.text_input("Όνομα Χρήστη")
        pwd = st.text_input("Συνθηματικό", type="password")
        if st.button("Σύνδεση"):
            if user == "admin" and pwd == "1234":
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("Λάθος στοιχεία! (Δοκίμασε: admin / 1234)")
    st.stop()

# ---------------------------------------------------------
# 4. MAIN APP (Dashboard & Navigation)
# ---------------------------------------------------------
st.sidebar.image("https://img.icons8.com/color/96/000000/droplet.png", width=60)
st.sidebar.title("ΔΕΥΑ Δοξάτου")
menu = st.sidebar.radio("Μενού", ["📊 Dashboard", "➕ Νέο Αίτημα", "⚙️ Διαχείριση Βλαβών"])

if st.sidebar.button("Αποσύνδεση"):
    st.session_state['logged_in'] = False
    st.rerun()

# --- PAGE 1: DASHBOARD ---
if menu == "📊 Dashboard":
    st.markdown("<h1 class='main-title'>📊 Πίνακας Ελέγχου Αιτημάτων</h1>", unsafe_allow_html=True)

    conn = sqlite3.connect('streamlit_deyad.db')
    df = pd.read_sql_query("SELECT * FROM requests", conn)
    conn.close()

    col1, col2, col3 = st.columns(3)
    col1.metric("Συνολικά Αιτήματα", len(df))
    col2.metric("Σε Εκκρεμότητα", len(df[df['status'] == 'Σε Εκκρεμότητα']) if not df.empty else 0)
    col3.metric("Ολοκληρωμένα", len(df[df['status'] == 'Ολοκληρώθηκε']) if not df.empty else 0)

    st.divider()
    st.subheader("Λίστα Αιτημάτων")
    st.dataframe(df, use_container_width=True)

# --- PAGE 2: NEW REQUEST ---
elif menu == "➕ Νέο Αίτημα":
    st.markdown("<h1 class='main-title'>➕ Καταχώρηση Νέου Αιτήματος</h1>", unsafe_allow_html=True)

    with st.form("request_form"):
        title = st.text_input("Περιγραφή/Τίτλος Βλάβης")
        category = st.selectbox("Κατηγορία", ["Ύδρευση", "Αποχέτευση", "Βλάβη Δικτύου", "Μετρητής"])
        priority = st.select_slider("Προτεραιότητα", options=["Χαμηλή", "Μεσαία", "Υψηλή", "Επείγουσα"])

        submitted = st.form_submit_button("Υποβολή Αιτήματος")
        if submitted and title:
            conn = sqlite3.connect('streamlit_deyad.db')
            c = conn.cursor()
            c.execute("INSERT INTO requests (title, category, priority, status, date) VALUES (?, ?, ?, ?, ?)",
                      (title, category, priority, "Σε Εκκρεμότητα", datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            conn.close()
            st.success("Το αίτημα καταχωρήθηκε επιτυχώς!")

# --- PAGE 3: MANAGEMENT ---
elif menu == "⚙️ Διαχείριση Βλαβών":
    st.markdown("<h1 class='main-title'>⚙️ Ενημέρωση Κατάστασης</h1>", unsafe_allow_html=True)

    conn = sqlite3.connect('streamlit_deyad.db')
    df = pd.read_sql_query("SELECT * FROM requests", conn)

    if not df.empty:
        req_id = st.selectbox("Επιλογή Αιτήματος #ID", df['id'])
        new_status = st.selectbox("Νέα Κατάσταση", ["Σε Εκκρεμότητα", "Σε Εξέλιξη", "Ολοκληρώθηκε"])

        if st.button("Ενημέρωση"):
            c = conn.cursor()
            c.execute("UPDATE requests SET status = ? WHERE id = ?", (new_status, req_id))
            conn.commit()
            st.success(f"Το αίτημα #{req_id} ενημερώθηκε σε '{new_status}'!")
            st.rerun()
    else:
        st.info("Δεν υπάρχουν αιτήματα προς διαχείριση.")
    conn.close()
