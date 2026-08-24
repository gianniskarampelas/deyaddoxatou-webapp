import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime

# ---------------------------------------------------------
# 1. PAGE CONFIG & MODERN THEMING
# ---------------------------------------------------------
st.set_page_config(
    page_title="ΔΕΥΑ Δοξάτου - Σύστημα Διαχείρισης", 
    page_icon="💧", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Light Theme & Centered Card Support)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Gradient Background για Login */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0284c7 100%) !important;
    }

    /* Styling της Κεντρικής Κάρτας Login */
    div[data-testid="stForm"] {
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-radius: 1.25rem !important;
        padding: 2.5rem !important;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }

    /* Τίτλοι & Κείμενα μέσα στη φόρμα */
    div[data-testid="stForm"] h2, 
    div[data-testid="stForm"] p, 
    div[data-testid="stForm"] label {
        color: #0f172a !important;
    }

    /* Input Fields */
    div[data-testid="stForm"] input, select {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 0.75rem !important;
    }

    /* Buttons */
    .stButton>button {
        background: #0284c7 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 0.75rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.4) !important;
    }

    .stButton>button:hover {
        background: #0369a1 !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0f172a !important;
    }
    
    [data-testid="stSidebar"] * {
        color: #f1f5f9 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. HELPER FUNCTIONS FOR DATABASE & SECURITY
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
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT,
            email TEXT
        )
    ''')
    # Έλεγχος αν υπάρχει η στήλη email σε παλιά βάση
    try:
        c.execute("ALTER TABLE users ADD COLUMN email TEXT")
    except sqlite3.OperationalError:
        pass
        
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
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", ('admin', make_hashes('1234'), 'Admin', 'admin@deyad.gr'))
    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------
# 3. AUTHENTICATION SYSTEM (LOGIN SCREEN)
# ---------------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ''
    st.session_state['role'] = ''

if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.form("login_form"):
            st.markdown("""
                <div style='text-align: center; margin-bottom: 1.5rem;'>
                    <div style='font-size: 3rem; margin-bottom: 0.5rem;'>💧</div>
                    <h2 style='margin: 0; font-weight: 700;'>Δ.Ε.Υ.Α. Δοξάτου</h2>
                    <p style='color: #64748b; font-size: 0.875rem; margin-top: 0.25rem;'>Σύστημα Διαχείρισης Αιτημάτων</p>
                </div>
            """, unsafe_allow_html=True)
            
            user_input = st.text_input("Όνομα Χρήστη")
            pwd_input = st.text_input("Συνθηματικό", type="password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            btn_col1, btn_col2, btn_col3 = st.columns([1, 1.5, 1])
            with btn_col2:
                submitted = st.form_submit_button("Είσοδος στο Σύστημα")
            
            if submitted:
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
# 4. NAVIGATION & MENU
# ---------------------------------------------------------
st.sidebar.title("💧 ΔΕΥΑ Δοξάτου")
st.sidebar.write(f"👤 Χρήστης: **{st.session_state['username']}** ({st.session_state['role']})")

menu_options = ["📊 Dashboard", "➕ Νέο Αίτημα", "⚙️ Διαχείριση Βλαβών"]
if st.session_state['role'] == 'Admin':
    menu_options.append("👥 Διαχείριση Χρηστών")

menu = st.sidebar.radio("Μενού", menu_options)

if st.sidebar.button("Αποσύνδεση"):
    st.session_state['logged_in'] = False
    st.rerun()

# ---------------------------------------------------------
# 5. PAGES
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
            st.success("Καταχωρήθηκε επιτυχώς!")

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
            st.success("Ενημερώθηκε επιτυχώς!")
            st.rerun()
    conn.close()

# --- USER MANAGEMENT (ADMIN ONLY) ---
elif menu == "👥 Διαχείριση Χρηστών":
    st.header("👥 Διαχείριση Χρηστών & Προσβάσεων")
    
    tab1, tab2, tab3 = st.tabs(["📋 Λίστα Χρηστών", "➕ Προσθήκη Χρήστη", "✏️ Επεξεργασία / Διαγραφή"])
    
    # TAB 1: LIST
    with tab1:
        conn = sqlite3.connect('streamlit_deyad.db')
        users_df = pd.read_sql_query("SELECT username, email, role FROM users", conn)
        conn.close()
        st.dataframe(users_df, use_container_width=True)

    # TAB 2: ADD USER
    with tab2:
        with st.form("add_user_form"):
            new_username = st.text_input("Όνομα Χρήστη (Username)")
            new_email = st.text_input("Email")
            new_password = st.text_input("Κωδικός", type="password")
            new_role = st.selectbox("Ρόλος", ["Τεχνικός", "Γραμματεία", "Admin"])
            
            if st.form_submit_button("Δημιουργία Χρήστη"):
                if new_username and new_password:
                    conn = sqlite3.connect('streamlit_deyad.db')
                    c = conn.cursor()
                    try:
                        c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", 
                                  (new_username, make_hashes(new_password), new_role, new_email))
                        conn.commit()
                        st.success(f"Ο χρήστης '{new_username}' δημιουργήθηκε επιτυχώς!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Το Username υπάρχει ήδη!")
                    finally:
                        conn.close()
                else:
                    st.warning("Συμπλήρωσε Username και Κωδικό.")

    # TAB 3: EDIT / DELETE
    with tab3:
        conn = sqlite3.connect('streamlit_deyad.db')
        c = conn.cursor()
        c.execute("SELECT username FROM users")
        user_list = [row[0] for row in c.fetchall()]
        
        selected_user = st.selectbox("Επιλογή Χρήστη προς Επεξεργασία", user_list)
        
        if selected_user:
            c.execute("SELECT username, email, role FROM users WHERE username=?", (selected_user,))
            user_data = c.fetchone()
            
            with st.form("edit_user_form"):
                st.subheader(f"Επεξεργασία: {selected_user}")
                edit_username = st.text_input("Νέο Username", value=user_data[0])
                edit_email = st.text_input("Email", value=user_data[1] if user_data[1] else "")
                edit_role = st.selectbox("Ρόλος", ["Τεχνικός", "Γραμματεία", "Admin"], 
                                         index=["Τεχνικός", "Γραμματεία", "Admin"].index(user_data[2]) if user_data[2] in ["Τεχνικός", "Γραμματεία", "Admin"] else 0)
                edit_password = st.text_input("Νέος Κωδικός (Άφησέ το κενό αν δεν θέλεις να αλλαχθεί)", type="password")
                
                save_btn = st.form_submit_button("💾 Αποθήκευση Αλλαγών")
                
                if save_btn:
                    if edit_password:
                        hashed_p = make_hashes(edit_password)
                        c.execute("UPDATE users SET username=?, email=?, role=?, password=? WHERE username=?",
                                  (edit_username, edit_email, edit_role, hashed_p, selected_user))
                    else:
                        c.execute("UPDATE users SET username=?, email=?, role=? WHERE username=?",
                                  (edit_username, edit_email, edit_role, selected_user))
                    conn.commit()
                    st.success("Τα στοιχεία ενημερώθηκαν!")
                    st.rerun()

            st.divider()
            if selected_user != st.session_state['username']:
                if st.button(f"❌ Διαγραφή Χρήστη '{selected_user}'"):
                    c.execute("DELETE FROM users WHERE username=?", (selected_user,))
                    conn.commit()
                    st.warning(f"Ο χρήστης '{selected_user}' διαγράφηκε.")
                    st.rerun()
            else:
                st.info("Δεν μπορείτε να διαγράψετε τον εαυτό σας.")
        conn.close()