import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import os
from datetime import datetime
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from fpdf import FPDF

# ---------------------------------------------------------
# 1. PAGE CONFIG & MODERN THEMING
# ---------------------------------------------------------
st.set_page_config(
    page_title="ΔΕΥΑ Δοξάτου - Σύστημα Διαχείρισης", 
    page_icon="💧", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background-color: #f1f5f9 !important;
    }

    .comment-box {
        background-color: #f8fafc;
        border-left: 4px solid #0284c7;
        padding: 10px 15px;
        border-radius: 0.5rem;
        margin-bottom: 10px;
    }
    .comment-user {
        font-weight: 700;
        color: #0f172a;
        font-size: 0.9rem;
    }
    .comment-date {
        color: #94a3b8;
        font-size: 0.75rem;
        margin-left: 10px;
    }
    .comment-text {
        color: #334155;
        font-size: 0.95rem;
        margin-top: 4px;
    }

    [data-testid="stSidebar"] .stButton>button {
        background-color: #ef4444 !important;
        color: white !important;
        border: none !important;
        width: 100% !important;
    }
    [data-testid="stSidebar"] .stButton>button:hover {
        background-color: #dc2626 !important;
    }

    div[data-testid="stForm"] {
        background-color: #ffffff !important;
        border-radius: 1.25rem !important;
        padding: 2.5rem !important;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1) !important;
        border: 1px solid #e2e8f0 !important;
    }

    .stButton>button {
        border-radius: 0.5rem !important;
        font-weight: 600 !important;
    }

    [data-testid="stSidebar"] {
        background-color: #0f172a !important;
    }
    
    [data-testid="stSidebar"] * {
        color: #f1f5f9 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. HELPER FUNCTIONS, PDF GENERATOR & GEOCODING
# ---------------------------------------------------------
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

def clean_val(val, default=""):
    if pd.isna(val) or val is None:
        return default
    s_val = str(val).strip()
    if s_val in ["", "nan", "None", "NaN", "<NA>"]:
        return default
    return s_val

def get_status_badge(status):
    status_str = clean_val(status, "Σε Εκκρεμότητα")
    colors = {
        "Σε Εκκρεμότητα": "#eab308",            # Κίτρινο
        "Ανατέθηκε / Προς Εκτέλεση": "#0284c7", # Μπλε
        "Σε Αναμονή Εγκρίσεων": "#8b5cf6",     # Μοβ
        "Ολοκληρώθηκε": "#10b981"               # Πράσινο
    }
    bg_color = colors.get(status_str, "#64748b")
    
    return f"""
        <span style="
            background-color: {bg_color};
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 700;
            display: inline-block;
            box-shadow: 0 2px 5px rgba(0,0,0,0.15);
        ">
            {status_str}
        </span>
    """

def generate_pdf_report(req_data, comments):
    """Δημιουργία PDF Αναφοράς Εργασίας (Unicode Safe)"""
    pdf = FPDF()
    pdf.add_page()
    
    # Προσπάθεια φόρτωσης Unicode γραμματοσειράς για Ελληνικά
    try:
        pdf.add_font("DejaVu", "", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", uni=True)
        pdf.add_font("DejaVu", "B", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", uni=True)
        font_name = "DejaVu"
    except Exception:
        # Fallback σε περίπτωση που δεν υπάρχει η DejaVu στο σύστημα
        font_name = "Helvetica"

    def safe_text(txt):
        """Καθαρίζει το κείμενο αν χρησιμοποιείται η Helvetica"""
        if font_name == "Helvetica":
            # Μετατροπή ελληνικών σε λατινικούς χαρακτήρες (Greeklish) για να μην κρασάρει
            greek_map = str.maketrans(
                "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩαβγδεζηθικλμνξοπρστυφχψωςΆΈΉΊΌΎΏάέήίόύώ",
                "ABGDEZHIKLMNXOPRSTYFXPOabgdezhiklmnxoprstyf线oaaeeiiooywaeeiiooyw"
            )
            return str(txt).translate(greek_map)
        return str(txt)

    pdf.set_font(font_name, 'B', 16 if font_name != "Helvetica" else 'B')
    pdf.cell(0, 10, f"ΔΕΥΑ ΔΟΞΑΤΟΥ - ΤΕΛΙΚΗ ΑΝΑΦΟΡΑ #{req_data['id']}" if font_name != "Helvetica" else f"DEYA DOXATOU - REPORT #{req_data['id']}", ln=True, align='C')
    
    pdf.set_font(font_name, '', 10)
    pdf.cell(0, 8, safe_text(f"Ημερομηνία Έκδοσης: {datetime.now().strftime('%d/%m/%Y %H:%M')}"), ln=True, align='C')
    pdf.line(10, 30, 200, 30)
    pdf.ln(8)
    
    # Στοιχεία Εργασίας
    pdf.set_font(font_name, 'B', 12)
    pdf.cell(0, 8, safe_text(f"Τίτλος: {req_data['title']}"), ln=True)
    pdf.set_font(font_name, '', 11)
    pdf.cell(0, 6, safe_text(f"Πελάτης: {clean_val(req_data['client_name'], '-')}"), ln=True)
    pdf.cell(0, 6, safe_text(f"Κατηγορία: {clean_val(req_data['category'], '-')}"), ln=True)
    pdf.cell(0, 6, safe_text(f"Προτεραιότητα: {clean_val(req_data['priority'], '-')}"), ln=True)
    pdf.cell(0, 6, safe_text(f"Ανατέθηκε σε: {clean_val(req_data['assigned_to'], '-')}"), ln=True)
    pdf.cell(0, 6, safe_text(f"Διεύθυνση: {clean_val(req_data['address'], '-')}"), ln=True)
    pdf.cell(0, 6, safe_text(f"Κατάσταση: {clean_val(req_data['status'], '-')}"), ln=True)
    pdf.ln(5)
    
    # Οδηγίες
    pdf.set_font(font_name, 'B', 12)
    pdf.cell(0, 8, safe_text("Οδηγίες / Σημειώσεις:"), ln=True)
    pdf.set_font(font_name, '', 10)
    pdf.multi_cell(0, 6, safe_text(clean_val(req_data['notes'], 'Δεν καταχωρήθηκαν οδηγίες.')))
    pdf.ln(5)
    
    # Σχόλια & Ιστορικό
    pdf.set_font(font_name, 'B', 12)
    pdf.cell(0, 8, safe_text("Ιστορικό Επικοινωνίας & Ενέργειες:"), ln=True)
    pdf.set_font(font_name, '', 9)
    
    if comments:
        for u_name, msg, c_at in comments:
            pdf.cell(0, 5, safe_text(f"[{c_at}] {u_name}: {msg}"), ln=True)
    else:
        pdf.cell(0, 5, safe_text("Δεν υπάρχουν καταγεγραμμένα σχόλια."), ln=True)
        
    return pdf.output()

def geocode_address_search(search_query):
    if not search_query or len(search_query.strip()) < 3:
        return []
    
    geolocator = Nominatim(user_agent="deyad_workflow_app")
    query_str = search_query
    if "Ελλάδα" not in query_str and "Greece" not in query_str:
        query_str += ", Ελλάδα"
        
    try:
        locations = geolocator.geocode(query_str, exactly_one=False, limit=5)
        if locations:
            results = []
            for loc in locations:
                results.append({
                    'address': loc.address,
                    'lat': loc.latitude,
                    'lon': loc.longitude
                })
            return results
    except (GeocoderTimedOut, GeocoderServiceError):
        pass
    return []

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
            address TEXT,
            lat REAL,
            lon REAL,
            notes TEXT,
            date TEXT,
            client_name TEXT,
            assigned_to TEXT,
            deadline TEXT
        )
    ''')
    
    columns_to_add = [
        ("address", "TEXT"), ("lat", "REAL"), ("lon", "REAL"), ("notes", "TEXT"),
        ("client_name", "TEXT"), ("assigned_to", "TEXT"), ("deadline", "TEXT")
    ]
    for col_name, col_type in columns_to_add:
        try:
            c.execute(f"ALTER TABLE requests ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass
            
    c.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER,
            filename TEXT,
            doc_type TEXT,
            uploaded_by TEXT,
            uploaded_at TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER,
            username TEXT,
            message TEXT,
            created_at TEXT
        )
    ''')

    c.execute("SELECT * FROM users WHERE username='superadmin'")
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", ('superadmin', make_hashes('1234'), 'Super Admin', 'it@deyad.gr'))
        
    c.execute("SELECT * FROM users WHERE username='stefi'")
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", ('stefi', make_hashes('1234'), 'Admin (Γραμματεία)', 'stefi@deyad.gr'))
        
    c.execute("SELECT * FROM users WHERE username='makis'")
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", ('makis', make_hashes('1234'), 'Τεχνικός/Μηχανικός', 'makis@deyad.gr'))
        
    conn.commit()
    conn.close()

init_db()

if not os.path.exists("uploads"):
    os.makedirs("uploads")

# ---------------------------------------------------------
# 3. MODAL DIALOGS FOR USER MANAGEMENT
# ---------------------------------------------------------

@st.dialog("➕ Δημιουργία Νέου Χρήστη")
def add_user_dialog():
    with st.form("add_user_modal_form"):
        new_username = st.text_input("Όνομα Χρήστη (Username)")
        new_email = st.text_input("Email")
        new_password = st.text_input("Κωδικός Πρόσβασης", type="password")
        new_role = st.selectbox("Ρόλος", ["Τεχνικός/Μηχανικός", "Admin (Γραμματεία)", "Super Admin (IT)"])
        
        submit = st.form_submit_button("💾 Αποθήκευση Χρήστη", use_container_width=True)
        if submit:
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
                st.warning("Παρακαλώ συμπληρώστε τα πεδία Username και Κωδικός.")

@st.dialog("✏️ Επεξεργασία Χρήστη")
def edit_user_dialog(username):
    conn = sqlite3.connect('streamlit_deyad.db')
    c = conn.cursor()
    c.execute("SELECT username, email, role FROM users WHERE username=?", (username,))
    user_data = c.fetchone()
    conn.close()
    
    if user_data:
        with st.form("edit_user_modal_form"):
            st.markdown(f"**Χρήστης:** `{username}`")
            edit_username = st.text_input("Όνομα Χρήστη", value=user_data[0])
            edit_email = st.text_input("Email", value=clean_val(user_data[1]))
            
            roles = ["Τεχνικός/Μηχανικός", "Admin (Γραμματεία)", "Super Admin (IT)"]
            curr_role_idx = roles.index(user_data[2]) if user_data[2] in roles else 0
            edit_role = st.selectbox("Ρόλος", roles, index=curr_role_idx)
            
            edit_password = st.text_input("Νέος Κωδικός (Αφήστε το κενό αν δεν θέλετε αλλαγή)", type="password")
            
            submit = st.form_submit_button("💾 Ενημέρωση Στοιχείων", use_container_width=True)
            if submit:
                conn = sqlite3.connect('streamlit_deyad.db')
                c = conn.cursor()
                if edit_password:
                    hashed_p = make_hashes(edit_password)
                    c.execute("UPDATE users SET username=?, email=?, role=?, password=? WHERE username=?",
                              (edit_username, edit_email, edit_role, hashed_p, username))
                else:
                    c.execute("UPDATE users SET username=?, email=?, role=? WHERE username=?",
                              (edit_username, edit_email, edit_role, username))
                conn.commit()
                conn.close()
                st.success("Τα στοιχεία ενημερώθηκαν!")
                st.rerun()

@st.dialog("❌ Επιβεβαίωση Διαγραφής")
def delete_user_dialog(username):
    st.write(f"Είστε σίγουροι ότι θέλετε να διαγράψετε τον χρήστη **{username}**;")
    st.caption("Η ενέργεια αυτή δεν μπορεί να αναιρεθεί.")
    
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("❌ Ναι, Διαγραφή", type="primary", use_container_width=True):
            conn = sqlite3.connect('streamlit_deyad.db')
            c = conn.cursor()
            c.execute("DELETE FROM users WHERE username=?", (username,))
            conn.commit()
            conn.close()
            st.success(f"Ο χρήστης '{username}' διαγράφηκε.")
            st.rerun()
    with col_no:
        if st.button("Ακύρωση", use_container_width=True):
            st.rerun()

# ---------------------------------------------------------
# 4. AUTHENTICATION (LOGIN)
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
                    <h2 style='margin: 0; font-weight: 700; color: #0f172a;'>Δ.Ε.Υ.Α. Δοξάτου</h2>
                    <p style='color: #64748b; font-size: 0.875rem; margin-top: 0.25rem;'>Εσωτερικό Σύστημα Διαχείρισης Εργασιών</p>
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
# 5. NAVIGATION & SIDEBAR
# ---------------------------------------------------------
st.sidebar.title("💧 ΔΕΥΑ Δοξάτου")
st.sidebar.write(f"👤 Χρήστης: **{st.session_state['username']}**")
st.sidebar.caption(f"Ρόλος: {st.session_state['role']}")

menu_options = ["📊 Πίνακας Εργασιών", "➕ Νέο Αίτημα", "🔍 Διαχείριση & Προβολή Έργου"]

if st.session_state['role'] == 'Super Admin':
    menu_options.append("👥 Διαχείριση Χρηστών")

menu = st.sidebar.radio("Μενού", menu_options)

if st.sidebar.button("Αποσύνδεση"):
    st.session_state['logged_in'] = False
    st.rerun()

# ---------------------------------------------------------
# 6. PAGES
# ---------------------------------------------------------

# --- DASHBOARD ---
if menu == "📊 Πίνακας Εργασιών":
    st.header("📊 Πίνακας Ελέγχου Εργασιών")
    conn = sqlite3.connect('streamlit_deyad.db')
    df = pd.read_sql_query("SELECT id, title, client_name, category, assigned_to, priority, status, deadline, date FROM requests", conn)
    conn.close()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Συνολικά Αιτήματα", len(df))
    col2.metric("Σε Εκκρεμότητα", len(df[df['status'] == 'Σε Εκκρεμότητα']) if not df.empty else 0)
    col3.metric("Σε Εξέλιξη", len(df[df['status'] == 'Ανατέθηκε / Προς Εκτέλεση']) if not df.empty else 0)
    col4.metric("Ολοκληρωμένα", len(df[df['status'] == 'Ολοκληρώθηκε']) if not df.empty else 0)
    
    st.divider()
    st.dataframe(df, use_container_width=True)

# --- NEW REQUEST ---
# --- NEW REQUEST ---
elif menu == "➕ Νέο Αίτημα":
    st.header("➕ Καταχώρηση Νέου Αιτήματος / Εργασίας")
    
    conn = sqlite3.connect('streamlit_deyad.db')
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE role LIKE '%Τεχνικός%' OR role='Super Admin'")
    tech_list = [row[0] for row in c.fetchall()]
    if not tech_list:
        tech_list = ["Makis", "superadmin"]
    conn.close()

    if 'form_lat' not in st.session_state:
        st.session_state['form_lat'] = 41.0964
    if 'form_lon' not in st.session_state:
        st.session_state['form_lon'] = 24.2301
    if 'form_address' not in st.session_state:
        st.session_state['form_address'] = ""

    col_form, col_map = st.columns([1.2, 1])

    with col_form:
        st.subheader("📝 Στοιχεία Εργασίας")
        
        # DROPDOWN ΜΕ ΤΙΣ ΕΠΙΣΗΜΕΣ ΑΙΤΗΣΕΙΣ ΤΗΣ ΔΕΥΑΔ
        preset_titles = [
            "Αίτηση Γενική",
            "Αίτηση Σύνδεσης στην Αποχέτευση",
            "Αίτηση Δήλωσης Ενοικιαστή",
            "Αίτηση Διαγραφής Ενοικιαστή",
            "Αίτηση Διακανονισμού Ληξιπρόθεσμων Οφειλών",
            "Αίτηση Διακοπής Υδροδότησης",
            "Αίτηση Μείωσης Λογαριασμού",
            "Αίτηση Μεταφοράς Υδρομέτρου",
            "Αίτηση Υπαγωγής σε Κοινωνικό Τιμολόγιο",
            "Αίτηση Παροχής Νερού",
            "Αίτηση Αλλαγής Ιδιοκτήτη",
            "Αναφορά Βλάβης / Έκτακτη Επέμβαση",
            "Άλλο (Χειροκίνητη πληκτρολόγηση)"
        ]

        selected_title_option = st.selectbox("Τύπος Αίτησης / Τίτλος Εργασίας", preset_titles)

        if selected_title_option == "Άλλο (Χειροκίνητη πληκτρολόγηση)":
            title = st.text_input("Εξειδικεύστε τον Τίτλο Εργασίας", placeholder="π.χ. Αντικατάσταση σπασμένης βάνας")
        else:
            title = selected_title_option

        client_name = st.text_input("Ονοματεπώνυμο Δημότη / Πελάτη", placeholder="π.χ. Σωτήρης Αλβανόπουλος")
        
        c1, c2 = st.columns(2)
        category = c1.selectbox("Κατηγορία", ["Ύδρευση - Εγκατάσταση Υδρομέτρου", "Ύδρευση - Μετακίνηση Υδρομέτρου", "Ύδρευση - Βλάβη Σωλήνα", "Αποχέτευση - Εμπλοκή", "Έλεγχος Πίεσης", "Διοικητικό / Λογιστήριο"])
        priority = c2.select_slider("Προτεραιότητα", ["Χαμηλή", "Μεσαία", "Υψηλή", "Επείγουσα"])
        
        c3, c4 = st.columns(2)
        assigned_to = c3.selectbox("Ανάθεση σε:", tech_list)
        deadline = c4.date_input("Προθεσμία Παράδοσης")
        
        st.markdown("---")
        st.markdown("##### 📍 Αναζήτηση Διεύθυνσης & Εντοπισμός στο Χάρτη")
        
        search_addr = st.text_input("Γράψτε τη διεύθυνση:", value=st.session_state['form_address'], placeholder="π.χ. Δημοκρατίας 15, Δοξάτο ή Μεγ. Αλεξάνδρου, Δράμα")
        
        if st.button("🔍 Αναζήτηση & Εντοπισμός στο Χάρτη", use_container_width=True):
            if search_addr:
                results = geocode_address_search(search_addr)
                if results:
                    st.session_state['search_results'] = results
                    st.success(f"Βρέθηκαν {len(results)} πιθανές τοποθεσίες! Επιλέξτε παρακάτω:")
                else:
                    st.error("Δεν βρέθηκε η διεύθυνση. Δοκιμάστε να προσθέσετε την πόλη/περιοχή.")

        if 'search_results' in st.session_state and st.session_state['search_results']:
            options = [f"{r['address']}" for r in st.session_state['search_results']]
            selected_opt = st.selectbox("🎯 Επιλέξτε την ακριβή διεύθυνση:", options)
            
            chosen = next(r for r in st.session_state['search_results'] if r['address'] == selected_opt)
            st.session_state['form_lat'] = chosen['lat']
            st.session_state['form_lon'] = chosen['lon']
            st.session_state['form_address'] = chosen['address']

        st.markdown("---")
        notes = st.text_area("Οδηγίες προς Τεχνικό", placeholder="Ενημερώστε τις οδηγίες...")
        
        st.markdown("##### 📄 Αρχικό Δικαιολογητικό (Γραμματεία)")
        uploaded_file = st.file_uploader("Επισύναψη Αρχείου (PDF, PNG, JPG)", type=["pdf", "png", "jpg", "jpeg"])
        
        submit_btn = st.button("💾 Καταχώρηση & Αναφορά", type="primary", use_container_width=True)

    with col_map:
        st.subheader("🗺️ Προεπισκόπηση Τοποθεσίας")
        cur_lat = st.session_state['form_lat']
        cur_lon = st.session_state['form_lon']
        
        m = folium.Map(location=[cur_lat, cur_lon], zoom_start=16)
        folium.Marker(
            [cur_lat, cur_lon], 
            popup=title if title else "Σημείο Εργασίας", 
            tooltip=st.session_state['form_address'] if st.session_state['form_address'] else "ΔΕΥΑΔ",
            icon=folium.Icon(color="red", icon="wrench")
        ).add_to(m)
        
        st_folium(m, width=450, height=380, key="new_req_map")
        st.caption(f"📍 Συντεταγμένες: `{cur_lat:.6f}, {cur_lon:.6f}`")

    if submit_btn:
        if title:
            conn = sqlite3.connect('streamlit_deyad.db')
            c = conn.cursor()
            
            final_addr = st.session_state['form_address'] if st.session_state['form_address'] else search_addr
            
            c.execute("""
                INSERT INTO requests (title, client_name, category, priority, status, assigned_to, deadline, address, lat, lon, notes, date) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (title, client_name, category, priority, "Ανατέθηκε / Προς Εκτέλεση", assigned_to, str(deadline), final_addr, cur_lat, cur_lon, notes, datetime.now().strftime("%Y-%m-%d %H:%M")))
            
            req_id = c.lastrowid

            if uploaded_file is not None:
                file_save_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
                with open(os.path.join("uploads", file_save_name), "wb") as f:
                    f.write(uploaded_file.getbuffer())

                c.execute("""
                    INSERT INTO documents (request_id, filename, doc_type, uploaded_by, uploaded_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (req_id, file_save_name, "Αρχικό Δικαιολογητικό (Γραμματεία)", st.session_state['username'], datetime.now().strftime("%d/%m/%Y %H:%M")))

            conn.commit()
            conn.close()
            
            st.session_state['form_lat'] = 41.0964
            st.session_state['form_lon'] = 24.2301
            st.session_state['form_address'] = ""
            if 'search_results' in st.session_state:
                del st.session_state['search_results']
                
            st.success("Το αίτημα καταχωρήθηκε επιτυχώς!")
            st.rerun()
        else:
            st.warning("Παρακαλώ συμπληρώστε τουλάχιστον τον Τίτλο Εργασίας.")

# --- PROJECT DETAIL, DOCS & INTERNAL CHAT ---
elif menu == "🔍 Διαχείριση & Προβολή Έργου":
    conn = sqlite3.connect('streamlit_deyad.db')
    df = pd.read_sql_query("SELECT * FROM requests", conn)
    
    if not df.empty:
        options_list = [f"{row['id']} - {row['title']} ({clean_val(row['client_name'], 'Χωρίς Πελάτη')})" for idx, row in df.iterrows()]
        selected_id_str = st.selectbox("📌 Επιλογή Αιτήματος προς Διαχείριση:", options_list)
        req_id = int(selected_id_str.split(" - ")[0])
        req_data = df[df['id'] == req_id].iloc[0]

        st.divider()

        col_left, col_right = st.columns([1.6, 1])

        with col_left:
            col_t1, col_t2 = st.columns([3, 1])
            with col_t1:
                st.markdown(f"### **{req_data['title']}**")
                st.markdown(get_status_badge(req_data['status']), unsafe_allow_html=True)
            
            # GET COMMENTS FOR PDF
            c_comm = conn.cursor()
            c_comm.execute("SELECT username, message, created_at FROM comments WHERE request_id=? ORDER BY id ASC", (req_id,))
            comments = c_comm.fetchall()

            # SHOW PDF BUTTON IF STATUS IS "Ολοκληρώθηκε"
            with col_t2:
                if req_data['status'] == "Ολοκληρώθηκε":
                    pdf_bytes = generate_pdf_report(req_data, comments)
                    st.download_button(
                        label="📄 PDF Αναφορά",
                        data=bytes(pdf_bytes),
                        file_name=f"Report_DEYAD_{req_id}.pdf",
                        mime="application/pdf",
                        type="primary",
                        use_container_width=True
                    )
            
            st.write("")
            
            c_client = clean_val(req_data['client_name'], default="-")
            c_assigned = clean_val(req_data['assigned_to'], default="-")
            c_deadline = clean_val(req_data['deadline'], default="-")
            c_address = clean_val(req_data['address'], default="-")

            info_col1, info_col2, info_col3 = st.columns(3)
            info_col1.write(f"**Πελάτης:**\n{c_client}")
            info_col2.write(f"**Ανατέθηκε σε:**\n{c_assigned}")
            info_col3.write(f"**Προθεσμία:**\n{c_deadline}")
            
            st.markdown("---")
            
            r_lat = req_data['lat'] if pd.notnull(req_data['lat']) and req_data['lat'] != 0 else 41.0964
            r_lon = req_data['lon'] if pd.notnull(req_data['lon']) and req_data['lon'] != 0 else 24.2301
            gmaps_nav = f"https://www.google.com/maps/search/?api=1&query={r_lat},{r_lon}"
            
            st.write(f"📍 **Διεύθυνση Έργου:** {c_address}")
            st.markdown(f"[🔗 **Άνοιγμα στο Maps**]({gmaps_nav})")
            
            fm = folium.Map(location=[r_lat, r_lon], zoom_start=16)
            folium.Marker([r_lat, r_lon], popup=req_data['title'], tooltip=c_address).add_to(fm)
            st_folium(fm, width=600, height=260, key=f"view_map_{req_id}")

            st.markdown("---")
            
            st.subheader("📄 Αρχεία & Δικαιολογητικά")
            c_docs = conn.cursor()
            c_docs.execute("SELECT filename, doc_type, uploaded_by, uploaded_at FROM documents WHERE request_id=? ORDER BY id DESC", (req_id,))
            docs = c_docs.fetchall()
            
            if docs:
                for doc in docs:
                    fname, dtype, uby, uat = doc
                    fpath = os.path.join("uploads", fname)
                    
                    st.markdown(f"**{dtype}**")
                    col_doc_info, col_btn = st.columns([3, 1])
                    with col_doc_info:
                        st.caption(f"📎 `{fname}` | Από: **{uby}** | {uat}")
                    with col_btn:
                        if os.path.exists(fpath):
                            with open(fpath, "rb") as f:
                                st.download_button("📥 Προβολή", data=f, file_name=fname, key=f"dl_{fname}")
                    st.write("")
            else:
                st.info("Δεν έχουν μεταφορτωθεί αρχεία για αυτό το έργο.")

            st.markdown("---")

            st.subheader("💬 Εσωτερική Επικοινωνία")
            if comments:
                for comm in comments:
                    u_name, msg, c_at = comm
                    st.markdown(f"""
                        <div class="comment-box">
                            <div><span class="comment-user">{u_name}</span><span class="comment-date">{c_at}</span></div>
                            <div class="comment-text">{msg}</div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("Δεν υπάρχουν μηνύματα. Γράψτε το πρώτο!")

            with st.form("add_comment_form"):
                comment_input = st.text_area("Γράψτε ένα σχόλιο ή ενημέρωση...", placeholder="π.χ. Ολοκληρώθηκε ο έλεγχος στο πεδίο.", height=80)
                send_msg = st.form_submit_button("Αποστολή Μηνύματος")
                
                if send_msg and comment_input:
                    c_comm.execute("INSERT INTO comments (request_id, username, message, created_at) VALUES (?, ?, ?, ?)",
                                   (req_id, st.session_state['username'], comment_input, datetime.now().strftime("%d/%m/%Y %H:%M")))
                    conn.commit()
                    st.rerun()

        with col_right:
            st.subheader("⚙️ Διαχείριση Έργου")
            
            c_users = conn.cursor()
            c_users.execute("SELECT username FROM users WHERE role LIKE '%Τεχνικός%' OR role='Super Admin'")
            tech_options = [row[0] for row in c_users.fetchall()]
            if not tech_options:
                tech_options = ["makis", "superadmin"]

            statuses = ["Σε Εκκρεμότητα", "Ανατέθηκε / Προς Εκτέλεση", "Σε Αναμονή Εγκρίσεων", "Ολοκληρώθηκε"]
            
            cur_stat = clean_val(req_data['status'], "Σε Εκκρεμότητα")
            curr_status_idx = statuses.index(cur_stat) if cur_stat in statuses else 0
            
            cur_tech = clean_val(req_data['assigned_to'])
            curr_tech_idx = tech_options.index(cur_tech) if cur_tech in tech_options else 0

            with st.form("edit_project_form"):
                new_status = st.selectbox("Κατάσταση:", statuses, index=curr_status_idx)
                new_assigned = st.selectbox("Ανάθεση σε:", tech_options, index=curr_tech_idx)
                
                new_deadline = st.text_input("Προθεσμία Παράδοσης:", value=clean_val(req_data['deadline']))
                new_address = st.text_input("Διεύθυνση Έργου:", value=clean_val(req_data['address']))
                new_notes = st.text_area("Οδηγίες προς Τεχνικό:", value=clean_val(req_data['notes']))
                
                save_changes = st.form_submit_button("Αποθήκευση Αλλαγών")
                
                if save_changes:
                    c_up = conn.cursor()
                    c_up.execute("""
                        UPDATE requests 
                        SET status=?, assigned_to=?, deadline=?, address=?, notes=? 
                        WHERE id=?
                    """, (new_status, new_assigned, new_deadline, new_address, new_notes, req_id))
                    conn.commit()
                    st.success("Οι αλλαγές αποθηκεύτηκαν!")
                    st.rerun()

            st.divider()

            st.subheader("+ Νέο Έγγραφο")
            with st.form("upload_doc_form"):
                doc_file = st.file_uploader("Αρχείο:", type=["pdf", "png", "jpg", "jpeg"])
                doc_type = st.selectbox("Τύπος Εγγράφου:", ["Αρχικό Δικαιολογητικό (Γραμματεία)", "Τελικό / Τεχνική Αναφορά (Τεχνικός)"])
                
                upload_btn = st.form_submit_button("Ανέβασμα")
                
                if upload_btn and doc_file:
                    file_save_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{doc_file.name}"
                    with open(os.path.join("uploads", file_save_name), "wb") as f:
                        f.write(doc_file.getbuffer())

                    c_inst = conn.cursor()
                    c_inst.execute("""
                        INSERT INTO documents (request_id, filename, doc_type, uploaded_by, uploaded_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (req_id, file_save_name, doc_type, st.session_state['username'], datetime.now().strftime("%d/%m/%Y %H:%M")))
                    conn.commit()
                    st.success("Το έγγραφο ανέβηκε επιτυχώς!")
                    st.rerun()

    else:
        st.info("Δεν υπάρχουν καταχωρημένα αιτήματα ακόμα. Δημιουργήστε το πρώτο από το μενού **«➕ Νέο Αίτημα»**!")
        
    conn.close()

# --- USER MANAGEMENT (SUPER ADMIN ONLY) ---
elif menu == "👥 Διαχείριση Χρηστών":
    col_header, col_add_btn = st.columns([3, 1])
    with col_header:
        st.header("👥 Διαχείριση Χρηστών & Προσβάσεων")
    with col_add_btn:
        st.write("")
        if st.button("➕ Προσθήκη Νέου Χρήστη", type="primary", use_container_width=True):
            add_user_dialog()

    st.divider()

    conn = sqlite3.connect('streamlit_deyad.db')
    users_df = pd.read_sql_query("SELECT username, email, role FROM users", conn)
    conn.close()

    if not users_df.empty:
        h_col1, h_col2, h_col3, h_col4 = st.columns([1.5, 2, 2, 1.5])
        h_col1.markdown("**Username**")
        h_col2.markdown("**Email**")
        h_col3.markdown("**Ρόλος**")
        h_col4.markdown("**Ενέργειες**")
        st.divider()

        for idx, row in users_df.iterrows():
            r_col1, r_col2, r_col3, r_col4 = st.columns([1.5, 2, 2, 1.5])
            
            r_col1.write(f"👤 `{row['username']}`")
            r_col2.write(clean_val(row['email'], default="-"))
            r_col3.write(f"**{row['role']}**")
            
            btn1, btn2 = r_col4.columns(2)
            if btn1.button("✏️", key=f"edit_{row['username']}", help=f"Επεξεργασία {row['username']}"):
                edit_user_dialog(row['username'])
                
            if row['username'] != st.session_state['username']:
                if btn2.button("❌", key=f"del_{row['username']}", help=f"Διαγραφή {row['username']}"):
                    delete_user_dialog(row['username'])
            else:
                btn2.write("")
            
            st.markdown("<hr style='margin: 8px 0; border-color: #e2e8f0;'>", unsafe_allow_html=True)
    else:
        st.info("Δεν βρέθηκαν χρήστες.")