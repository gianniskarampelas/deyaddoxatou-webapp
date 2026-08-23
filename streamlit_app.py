import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime

st.set_page_config(page_title="ΔΕΥΑ Δοξάτου", page_icon="💧", layout="wide")

# ---------------------------------------------------------
# 1. HELPER FUNCTIONS FOR DATABASE & SECURITY
# ---------------------------------------------------------
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

def init_db():
    conn = sqlite3.connect('streamlit_deyad.db')
    c = conn.cursor()
    # Πίνακας Χρηστών
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT
        )
    ''')
    # Πίνακας Αιτημάτων
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
    # Δημιουργία αρχικού Admin αν δεν υπάρχει
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?, ?, ?)", ('admin', make_hashes('1234'), 'Admin'))
    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------
# 2. AUTHENTICATION SYSTEM
# ---------------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ''
    st.session_state['role'] = ''

if not st.session_state['logged_in']:
    st.title("💧 Δ.Ε.Υ.Α. Δοξάτου")
    st.subheader("Σύνδεση Χρήστη")
    
    col1, _ = st.columns([1, 2])
    with col1:
        user_input = st.text_input("Όνομα Χρήστη")
        pwd_input = st.text_input("Συνθηματικό", type="password")
        
        if st.button("Είσοδος"):
            conn = sqlite3.connect('streamlit_deyad.db')
            c = conn.cursor()
            c.execute("SELECT password, role FROM users WHERE username=?", (user_input,))
            result = c.fetchone()
            conn.close()
            
            if result and check_hashes(pwd_input, result[0]):
                st.session_state['logged_in'] = True
                st.session_state['username'] = user_input
                st.session_state['role'] = result[1]
                st.rerun()
            else:
                st.error("Λανθασμένο όνομα χρήστη ή συνθηματικό.")
    st.stop()

# ---------------------------------------------------------
# 3. NAVIGATION & MENU
# ---------------------------------------------------------
st.sidebar.title("💧 ΔΕΥΑ Δοξάτου")
st.sidebar.write(f"👤 Χρήστης: **{st.session_state['username']}** ({st.session_state['role']})")

# Μενού επιλογών ανάλογα με τον Ρόλο
menu_options = ["📊 Dashboard", "➕ Νέο Αίτημα", "⚙️ Διαχείριση Βλαβών"]
if st.session_state['role'] == 'Admin':
    menu_options.append("👥 Διαχείριση Χρηστών")

menu = st.sidebar.radio("Μενού", menu_options)

if st.sidebar.button("Αποσύνδεση"):
    st.session_state['logged_in'] = False
    st.rerun()

# ---------------------------------------------------------
# 4. PAGES
# ---------------------------------------------------------

# --- DASHBOARD ---
if menu == "📊 Dashboard":
    st.header("📊 Πίνακας Ελέγχου Αιτημάτων")
    conn = sqlite3.connect('streamlit_deyad.db')
    df = pd.read_sql_query("SELECT * FROM requests", conn)
    conn.close()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Συνολικά Αιτήματα", len(df))
    col2.metric("Σε Εκκρεμότητα", len(df[df['status'] == 'Σε Εκκρεμότητα']) if not df.empty else 0)
    col3.metric("Ολοκληρωμένα", len(df[df['status'] == 'Ολοκληρώθηκε']) if not df.empty else 0)
    
    st.divider()
    st.dataframe(df, use_container_width=True)

# --- NEW REQUEST ---
elif menu == "➕ Νέο Αίτημα":
    st.header("➕ Νέο Αίτημα")
    with st.form("new_form"):
        title = st.text_input("Περιγραφή Βλάβης")
        category = st.selectbox("Κατηγορία", ["Ύδρευση", "Αποχέτευση", "Μετρητής"])
        priority = st.select_slider("Προτεραιότητα", ["Χαμηλή", "Μεσαία", "Υψηλή", "Επείγουσα"])
        if st.form_submit_button("Υποβολή") and title:
            conn = sqlite3.connect('streamlit_deyad.db')
            c = conn.cursor()
            c.execute("INSERT INTO requests (title, category, priority, status, date) VALUES (?, ?, ?, ?, ?)",
                      (title, category, priority, "Σε Εκκρεμότητα", datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            conn.close()
            st.success("Καταχωρήθηκε!")

# --- MANAGEMENT ---
elif menu == "⚙️ Διαχείριση Βλαβών":
    st.header("⚙️ Διαχείριση Βλαβών")
    conn = sqlite3.connect('streamlit_deyad.db')
    df = pd.read_sql_query("SELECT * FROM requests", conn)
    if not df.empty:
        req_id = st.selectbox("Επιλογή Αιτήματος #ID", df['id'])
        new_status = st.selectbox("Νέα Κατάσταση", ["Σε Εκκρεμότητα", "Σε Εξέλιξη", "Ολοκληρώθηκε"])
        if st.button("Ενημέρωση Κατάστασης"):
            c = conn.cursor()
            c.execute("UPDATE requests SET status=? WHERE id=?", (new_status, req_id))
            conn.commit()
            st.success("Ενημερώθηκε!")
            st.rerun()
    conn.close()

# --- USER MANAGEMENT (ADMIN ONLY) ---
elif menu == "👥 Διαχείριση Χρηστών":
    st.header("👥 Διαχείριση Χρηστών & Προσβάσεων")
    
    tab1, tab2 = st.tabs(["➕ Προσθήκη Χρήστη", "📋 Λίστα Χρηστών"])
    
    with tab1:
        with st.form("add_user_form"):
            new_username = st.text_input("Όνομα Χρήστη (Username)")
            new_password = st.text_input("Κωδικός", type="password")
            new_role = st.selectbox("Ρόλος", ["Τεχνικός", "Γραμματεία", "Admin"])
            
            if st.form_submit_button("Δημιουργία Χρήστη"):
                if new_username and new_password:
                    conn = sqlite3.connect('streamlit_deyad.db')
                    c = conn.cursor()
                    try:
                        c.execute("INSERT INTO users VALUES (?, ?, ?)", 
                                  (new_username, make_hashes(new_password), new_role))
                        conn.commit()
                        st.success(f"Ο χρήστης '{new_username}' δημιουργήθηκε ως {new_role}!")
                    except sqlite3.IntegrityError:
                        st.error("Το Username υπάρχει ήδη!")
                    finally:
                        conn.close()
                else:
                    st.warning("Συμπλήρωσε όλα τα πεδία.")

    with tab2:
        conn = sqlite3.connect('streamlit_deyad.db')
        users_df = pd.read_sql_query("SELECT username, role FROM users", conn)
        conn.close()
        st.dataframe(users_df, use_container_width=True)