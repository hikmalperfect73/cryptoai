import streamlit as st
import bcrypt
import db

# ─── Password hashing ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def cek_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

# ─── Session helpers ───────────────────────────────────────────────────────────

def is_logged_in() -> bool:
    return st.session_state.get("user_id") is not None

def login(username: str, password: str) -> bool:
    user = db.get_user_by_username(username)
    if user and cek_password(password, user["password_hash"]):
        st.session_state["user_id"] = user["id"]
        st.session_state["username"] = user["username"]
        return True
    return False

def daftar(username: str, password: str) -> tuple[bool, str]:
    if db.get_user_by_username(username):
        return False, "Username sudah dipakai."
    if len(password) < 6:
        return False, "Password minimal 6 karakter."
    hashed = hash_password(password)
    db.create_user(username, hashed)
    return True, "Akun berhasil dibuat."

def logout():
    for key in ["user_id", "username"]:
        st.session_state.pop(key, None)

# ─── Login page UI ─────────────────────────────────────────────────────────────

def tampilkan_form_auth():
    """Render halaman login bertema night-city dengan tab Masuk/Daftar."""

    # ── Init session state ──────────────────────────────────────────────────
    if "auth_tab" not in st.session_state:
        st.session_state["auth_tab"] = "masuk"

    # ── Global CSS + dekorasi ───────────────────────────────────────────────
    st.markdown("""
    <style>
    /* ── Reset Streamlit chrome ── */
    [data-testid="stHeader"]      { background: transparent !important; border-bottom: none !important; }
    [data-testid="stDecoration"]  { display: none !important; }
    [data-testid="stToolbar"]     { display: none !important; }
    .block-container              { padding-top: 0 !important; max-width: 100% !important; }

    /* ── Full-page background ── */
    .stApp {
        background: linear-gradient(180deg, #020818 0%, #050d2a 40%, #0a1a3e 70%, #0d1f4a 100%);
        min-height: 100vh;
        overflow: hidden;
    }

    /* ── Bintang ── */
    .stars-layer {
        position: fixed; inset: 0; pointer-events: none; z-index: 0;
        background-image:
            radial-gradient(1px 1px at 10% 15%, rgba(255,255,255,0.9) 0%, transparent 100%),
            radial-gradient(1px 1px at 25% 8%,  rgba(255,255,255,0.7) 0%, transparent 100%),
            radial-gradient(1.5px 1.5px at 40% 22%, rgba(255,255,255,0.8) 0%, transparent 100%),
            radial-gradient(1px 1px at 55% 5%,  rgba(255,255,255,0.6) 0%, transparent 100%),
            radial-gradient(1px 1px at 70% 18%, rgba(255,255,255,0.9) 0%, transparent 100%),
            radial-gradient(1.5px 1.5px at 85% 10%, rgba(255,255,255,0.7) 0%, transparent 100%),
            radial-gradient(1px 1px at 92% 25%, rgba(255,255,255,0.8) 0%, transparent 100%),
            radial-gradient(1px 1px at 15% 35%, rgba(255,255,255,0.5) 0%, transparent 100%),
            radial-gradient(1px 1px at 30% 42%, rgba(255,255,255,0.6) 0%, transparent 100%),
            radial-gradient(1px 1px at 60% 38%, rgba(255,255,255,0.7) 0%, transparent 100%),
            radial-gradient(1px 1px at 78% 30%, rgba(255,255,255,0.5) 0%, transparent 100%),
            radial-gradient(1px 1px at 5%  50%, rgba(255,255,255,0.4) 0%, transparent 100%),
            radial-gradient(1px 1px at 48% 12%, rgba(255,255,255,0.8) 0%, transparent 100%),
            radial-gradient(1px 1px at 95% 40%, rgba(255,255,255,0.6) 0%, transparent 100%);
    }
    @keyframes twinkle {
        0%, 100% { opacity: 0.4; } 50% { opacity: 1; }
    }
    .stars-layer { animation: twinkle 4s ease-in-out infinite alternate; }

    /* ── Skyline ── */
    .skyline-layer {
        position: fixed; bottom: 0; left: 0; right: 0;
        height: 180px; pointer-events: none; z-index: 1;
        background-color: #060e22;
        -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1440 180'%3E%3Cpolygon points='0,180 0,120 30,120 30,80 50,80 50,100 70,100 70,60 90,60 90,100 110,100 110,40 130,40 130,100 150,100 150,120 170,120 170,70 190,70 190,50 210,50 210,70 230,70 230,120 260,120 260,90 280,90 280,110 300,110 300,70 320,70 320,110 340,110 340,80 360,80 360,50 380,50 380,80 400,80 400,110 420,110 420,90 440,90 440,120 460,120 460,100 480,100 480,60 500,60 500,100 520,100 520,120 540,120 540,80 560,80 560,50 580,50 580,80 600,80 600,100 620,100 620,130 650,130 650,100 670,100 670,70 690,70 690,90 710,90 710,120 730,120 730,80 750,80 750,55 770,55 770,80 790,80 790,100 810,100 810,120 840,120 840,90 860,90 860,60 880,60 880,90 900,90 900,110 920,110 920,80 940,80 940,110 960,110 960,130 980,130 980,100 1000,100 1000,70 1020,70 1020,50 1040,50 1040,70 1060,70 1060,100 1080,100 1080,120 1100,120 1100,90 1120,90 1120,110 1140,110 1140,80 1160,80 1160,120 1180,120 1180,100 1200,100 1200,60 1220,60 1220,100 1240,100 1240,120 1260,120 1260,90 1280,90 1280,70 1300,70 1300,100 1320,100 1320,120 1350,120 1350,80 1370,80 1370,50 1390,50 1390,80 1410,80 1410,120 1440,120 1440,180' fill='%23060e22'/%3E%3C/svg%3E");
        mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1440 180'%3E%3Cpolygon points='0,180 0,120 30,120 30,80 50,80 50,100 70,100 70,60 90,60 90,100 110,100 110,40 130,40 130,100 150,100 150,120 170,120 170,70 190,70 190,50 210,50 210,70 230,70 230,120 260,120 260,90 280,90 280,110 300,110 300,70 320,70 320,110 340,110 340,80 360,80 360,50 380,50 380,80 400,80 400,110 420,110 420,90 440,90 440,120 460,120 460,100 480,100 480,60 500,60 500,100 520,100 520,120 540,120 540,80 560,80 560,50 580,50 580,80 600,80 600,100 620,100 620,130 650,130 650,100 670,100 670,70 690,70 690,90 710,90 710,120 730,120 730,80 750,80 750,55 770,55 770,80 790,80 790,100 810,100 810,120 840,120 840,90 860,90 860,60 880,60 880,90 900,90 900,110 920,110 920,80 940,80 940,110 960,110 960,130 980,130 980,100 1000,100 1000,70 1020,70 1020,50 1040,50 1040,70 1060,70 1060,100 1080,100 1080,120 1100,120 1100,90 1120,90 1120,110 1140,110 1140,80 1160,80 1160,120 1180,120 1180,100 1200,100 1200,60 1220,60 1220,100 1240,100 1240,120 1260,120 1260,90 1280,90 1280,70 1300,70 1300,100 1320,100 1320,120 1350,120 1350,80 1370,80 1370,50 1390,50 1390,80 1410,80 1410,120 1440,120 1440,180' fill='%23060e22'/%3E%3C/svg%3E");
        -webkit-mask-size: 100% 100%; mask-size: 100% 100%;
    }
    .skyline-lights {
        position: fixed; bottom: 0; left: 0; right: 0; height: 180px;
        pointer-events: none; z-index: 2;
        background-image:
            repeating-linear-gradient(
                90deg,
                transparent 0px, transparent 28px,
                rgba(255,220,80,0.5) 28px, rgba(255,220,80,0.5) 30px,
                transparent 30px, transparent 58px,
                rgba(255,220,80,0.4) 58px, rgba(255,220,80,0.4) 60px
            );
        background-size: 120px 8px;
        background-position: 0 60px;
        mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1440 180'%3E%3Cpolygon points='0,180 0,120 30,120 30,80 50,80 50,100 70,100 70,60 90,60 90,100 110,100 110,40 130,40 130,100 150,100 150,120 170,120 170,70 190,70 190,50 210,50 210,70 230,70 230,120 260,120 260,90 280,90 280,110 300,110 300,70 320,70 320,110 340,110 340,80 360,80 360,50 380,50 380,80 400,80 400,110 420,110 420,90 440,90 440,120 460,120 460,100 480,100 480,60 500,60 500,100 520,100 520,120 540,120 540,80 560,80 560,50 580,50 580,80 600,80 600,100 620,100 620,130 650,130 650,100 670,100 670,70 690,70 690,90 710,90 710,120 730,120 730,80 750,80 750,55 770,55 770,80 790,80 790,100 810,100 810,120 840,120 840,90 860,90 860,60 880,60 880,90 900,90 900,110 920,110 920,80 940,80 940,110 960,110 960,130 980,130 980,100 1000,100 1000,70 1020,70 1020,50 1040,50 1040,70 1060,70 1060,100 1080,100 1080,120 1100,120 1100,90 1120,90 1120,110 1140,110 1140,80 1160,80 1160,120 1180,120 1180,100 1200,100 1200,60 1220,60 1220,100 1240,100 1240,120 1260,120 1260,90 1280,90 1280,70 1300,70 1300,100 1320,100 1320,120 1350,120 1350,80 1370,80 1370,50 1390,50 1390,80 1410,80 1410,120 1440,120 1440,180' fill='white'/%3E%3C/svg%3E");
        -webkit-mask-size: 100% 100%; mask-size: 100% 100%;
    }

    /* ── Koin crypto ── */
    @keyframes float-a { 0%, 100% { transform: translateY(0px) rotate(0deg); } 50% { transform: translateY(-18px) rotate(5deg); } }
    @keyframes float-b { 0%, 100% { transform: translateY(0px) rotate(0deg); } 50% { transform: translateY(-12px) rotate(-4deg); } }
    @keyframes float-c { 0%, 100% { transform: translateY(0px) rotate(0deg); } 50% { transform: translateY(-22px) rotate(6deg); } }
    .coin { position: fixed; pointer-events: none; z-index: 3; user-select: none; line-height: 1; }
    .coin-btc-1 { font-size: 70px; top: 12%; left: 4%;  animation: float-a 5.5s ease-in-out infinite; filter: drop-shadow(0 0 16px rgba(247,147,26,0.7)); }
    .coin-btc-2 { font-size: 38px; top: 55%; left: 1%;  animation: float-b 4.2s ease-in-out infinite; filter: drop-shadow(0 0 10px rgba(247,147,26,0.5)); }
    .coin-btc-3 { font-size: 48px; top: 28%; right: 6%; animation: float-c 6.1s ease-in-out infinite; filter: drop-shadow(0 0 12px rgba(247,147,26,0.6)); }
    .coin-eth-1 { font-size: 65px; top: 18%; right: 2%; animation: float-b 5.0s ease-in-out infinite; filter: drop-shadow(0 0 16px rgba(114,137,218,0.7)); }
    .coin-eth-2 { font-size: 34px; top: 60%; right: 1%; animation: float-a 4.7s ease-in-out infinite; filter: drop-shadow(0 0 10px rgba(114,137,218,0.5)); }
    .coin-eth-3 { font-size: 44px; top: 40%; left: 3%;  animation: float-c 5.8s ease-in-out infinite; filter: drop-shadow(0 0 12px rgba(114,137,218,0.6)); }

    /* ── Candlestick chart ornamen ── */
    .chart-ornament { position: fixed; top: 5%; pointer-events: none; z-index: 3; opacity: 0.6; }
    .chart-left  { left: 2%; }
    .chart-right { right: 2%; }

    /* ── Tab wrapper trick ──────────────────────────────────────────────────
       Kita bungkus tiap kolom button dalam div.tab-wrap-active / tab-wrap-inactive
       lewat st.markdown SEBELUM st.button. CSS kita target:
         .tab-wrap-active  + div button
         .tab-wrap-inactive + div button
       "Adjacent sibling" tidak works karena Streamlit tambah wrapper.
       Trik yang WORKS: div kita dan div Streamlit ada dalam parent yang sama
       (kolom), jadi kita pakai ~ (general sibling).
    ────────────────────────────────────────────────────────────────────── */

    /* Base style untuk semua tab button */
    div[data-testid="column"] .stButton > button {
        width: 100% !important;
        border-radius: 12px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        padding: 14px 20px !important;
        border: none !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        letter-spacing: 0.3px !important;
    }

    /* Tab NONAKTIF — abu gelap */
    .tab-wrap-inactive ~ div .stButton > button,
    .tab-wrap-inactive ~ div .stButton > button:hover {
        background: rgba(255,255,255,0.06) !important;
        color: rgba(200,210,240,0.6) !important;
        box-shadow: none !important;
    }

    /* Tab AKTIF — biru gradient */
    .tab-wrap-active ~ div .stButton > button,
    .tab-wrap-active ~ div .stButton > button:hover {
        background: linear-gradient(135deg, #1a6fe8 0%, #0d4fbf 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 20px rgba(26,111,232,0.45) !important;
    }

    /* ── Form card glassmorphism ── */
    .form-card {
        background: rgba(10, 22, 55, 0.75);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border: 1px solid rgba(100,140,255,0.18);
        border-radius: 20px;
        padding: 36px 32px 28px;
        box-shadow: 0 8px 40px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.05);
        position: relative; z-index: 10;
    }

    /* ── Form input fields ── */
    .form-card .stTextInput > div > div > input {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(100,140,255,0.25) !important;
        border-radius: 10px !important;
        color: #e8edf8 !important;
        font-size: 15px !important;
        padding: 12px 16px !important;
    }
    .form-card .stTextInput > div > div > input:focus {
        border-color: rgba(100,160,255,0.6) !important;
        box-shadow: 0 0 0 3px rgba(26,111,232,0.15) !important;
    }
    .form-card .stTextInput label {
        color: #7eb3ff !important;
        font-size: 14px !important;
        font-weight: 500 !important;
    }

    /* ── Submit button (form) ── */
    .form-card .stFormSubmitButton > button,
    .form-card button[kind="formSubmit"] {
        width: 100% !important;
        background: linear-gradient(135deg, #1a6fe8 0%, #0d4fbf 100%) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 12px !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        padding: 14px !important;
        margin-top: 8px !important;
        letter-spacing: 0.5px !important;
        box-shadow: 0 4px 20px rgba(26,111,232,0.4) !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }
    .form-card .stFormSubmitButton > button:hover,
    .form-card button[kind="formSubmit"]:hover {
        box-shadow: 0 6px 28px rgba(26,111,232,0.6) !important;
        transform: translateY(-1px) !important;
    }

    /* ── Alert messages ── */
    .stAlert { border-radius: 10px !important; }
    </style>

    <!-- Dekorasi fixed layer -->
    <div class="stars-layer"></div>
    <div class="skyline-layer"></div>
    <div class="skyline-lights"></div>

    <div class="coin coin-btc-1">₿</div>
    <div class="coin coin-btc-2">₿</div>
    <div class="coin coin-btc-3">₿</div>
    <div class="coin coin-eth-1">Ξ</div>
    <div class="coin coin-eth-2">Ξ</div>
    <div class="coin coin-eth-3">Ξ</div>

    <!-- Candlestick ornamen kiri -->
    <svg class="chart-ornament chart-left" width="140" height="200" viewBox="0 0 140 200">
        <line x1="20" y1="10" x2="20" y2="190" stroke="rgba(100,180,255,0.15)" stroke-width="1" stroke-dasharray="4,4"/>
        <line x1="50" y1="10" x2="50" y2="190" stroke="rgba(100,180,255,0.1)"  stroke-width="1" stroke-dasharray="4,4"/>
        <line x1="80" y1="10" x2="80" y2="190" stroke="rgba(100,180,255,0.15)" stroke-width="1" stroke-dasharray="4,4"/>
        <line x1="110"y1="10" x2="110"y2="190" stroke="rgba(100,180,255,0.1)"  stroke-width="1" stroke-dasharray="4,4"/>
        <!-- candles -->
        <line x1="20" y1="30" x2="20" y2="80" stroke="#26c95b" stroke-width="1.5"/>
        <rect x="14" y="40" width="12" height="30" fill="#26c95b" rx="1"/>
        <line x1="50" y1="50" x2="50" y2="110" stroke="#ef4444" stroke-width="1.5"/>
        <rect x="44" y="60" width="12" height="35" fill="#ef4444" rx="1"/>
        <line x1="80" y1="25" x2="80" y2="90" stroke="#26c95b" stroke-width="1.5"/>
        <rect x="74" y="35" width="12" height="40" fill="#26c95b" rx="1"/>
        <line x1="110"y1="45" x2="110"y2="105" stroke="#26c95b" stroke-width="1.5"/>
        <rect x="104"y1="55" width="12" height="30" fill="#26c95b" rx="1"/>
        <!-- trend line -->
        <polyline points="20,70 50,90 80,60 110,55" stroke="rgba(255,255,100,0.6)" stroke-width="1.5" fill="none" stroke-dasharray="5,3"/>
    </svg>

    <!-- Candlestick ornamen kanan -->
    <svg class="chart-ornament chart-right" width="140" height="200" viewBox="0 0 140 200">
        <line x1="20" y1="10" x2="20" y2="190" stroke="rgba(100,180,255,0.15)" stroke-width="1" stroke-dasharray="4,4"/>
        <line x1="50" y1="10" x2="50" y2="190" stroke="rgba(100,180,255,0.1)"  stroke-width="1" stroke-dasharray="4,4"/>
        <line x1="80" y1="10" x2="80" y2="190" stroke="rgba(100,180,255,0.15)" stroke-width="1" stroke-dasharray="4,4"/>
        <line x1="110"y1="10" x2="110"y2="190" stroke="rgba(100,180,255,0.1)"  stroke-width="1" stroke-dasharray="4,4"/>
        <line x1="20" y1="80" x2="20" y2="130" stroke="#ef4444" stroke-width="1.5"/>
        <rect x="14" y="90" width="12" height="28" fill="#ef4444" rx="1"/>
        <line x1="50" y1="55" x2="50" y2="100" stroke="#26c95b" stroke-width="1.5"/>
        <rect x="44" y="62" width="12" height="28" fill="#26c95b" rx="1"/>
        <line x1="80" y1="70" x2="80" y2="120" stroke="#ef4444" stroke-width="1.5"/>
        <rect x="74" y="78" width="12" height="30" fill="#ef4444" rx="1"/>
        <line x1="110"y1="40" x2="110"y2="90" stroke="#26c95b" stroke-width="1.5"/>
        <rect x="104"y1="48" width="12" height="32" fill="#26c95b" rx="1"/>
        <polyline points="20,110 50,80 80,98 110,62" stroke="rgba(255,255,100,0.6)" stroke-width="1.5" fill="none" stroke-dasharray="5,3"/>
    </svg>
    """, unsafe_allow_html=True)

    # ── Layout utama ────────────────────────────────────────────────────────
    _, center_col, _ = st.columns([0.7, 1.4, 0.7])

    with center_col:
        st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)

        # ── Logo / judul ─────────────────────────────────────────────────
        st.markdown("""
        <div style="text-align:center; margin-bottom:28px; position:relative; z-index:10;">
            <div style="font-size:48px; margin-bottom:8px;">₿</div>
            <h1 style="
                font-size:28px; font-weight:800; margin:0 0 6px;
                background: linear-gradient(135deg, #7eb3ff, #ffffff);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                letter-spacing: -0.5px;
            ">CryptoAI</h1>
            <p style="color:rgba(150,180,240,0.7); font-size:14px; margin:0;">
                Dashboard Prediksi BTC &amp; ETH
            </p>
        </div>
        """, unsafe_allow_html=True)

        # ── Tab selector ─────────────────────────────────────────────────
        # TRICK RELIABLE:
        # Sebelum render button Streamlit, inject div marker dengan class berbeda
        # tergantung state aktif. CSS pakai general sibling selector (~) untuk
        # menarget button yang muncul setelah marker ini dalam kolom yang sama.

        tab_col1, tab_col2 = st.columns(2)

        with tab_col1:
            is_masuk = st.session_state["auth_tab"] == "masuk"
            st.markdown(
                f'<div class="{"tab-wrap-active" if is_masuk else "tab-wrap-inactive"}"></div>',
                unsafe_allow_html=True
            )
            if st.button("Masuk", key="tab_masuk", use_container_width=True):
                st.session_state["auth_tab"] = "masuk"
                st.rerun()

        with tab_col2:
            is_daftar = st.session_state["auth_tab"] == "daftar"
            st.markdown(
                f'<div class="{"tab-wrap-active" if is_daftar else "tab-wrap-inactive"}"></div>',
                unsafe_allow_html=True
            )
            if st.button("Daftar", key="tab_daftar", use_container_width=True):
                st.session_state["auth_tab"] = "daftar"
                st.rerun()

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # ── Form card ────────────────────────────────────────────────────
        st.markdown('<div class="form-card">', unsafe_allow_html=True)

        if st.session_state["auth_tab"] == "masuk":
            _render_form_masuk()
        else:
            _render_form_daftar()

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<div style='height:200px'></div>", unsafe_allow_html=True)


def _render_form_masuk():
    with st.form("form_masuk", clear_on_submit=False):
        st.text_input("Email", placeholder="nama@email.com", key="masuk_user")
        st.text_input("Password", type="password", placeholder="••••••••", key="masuk_pass")
        submitted = st.form_submit_button("Masuk", use_container_width=True)

    if submitted:
        username = st.session_state.get("masuk_user", "").strip()
        password = st.session_state.get("masuk_pass", "")
        if not username or not password:
            st.error("Isi email dan password.")
        elif login(username, password):
            st.rerun()
        else:
            st.error("Email atau password salah.")


def _render_form_daftar():
    with st.form("form_daftar", clear_on_submit=False):
        st.text_input("Email", placeholder="nama@email.com", key="daftar_user")
        st.text_input("Password", type="password", placeholder="Minimal 6 karakter", key="daftar_pass")
        st.text_input("Konfirmasi Password", type="password", placeholder="Ulangi password", key="daftar_pass2")
        submitted = st.form_submit_button("Buat Akun", use_container_width=True)

    if submitted:
        username = st.session_state.get("daftar_user", "").strip()
        password = st.session_state.get("daftar_pass", "")
        konfirmasi = st.session_state.get("daftar_pass2", "")
        if not username or not password:
            st.error("Isi semua field.")
        elif password != konfirmasi:
            st.error("Password tidak cocok.")
        else:
            ok, pesan = daftar(username, password)
            if ok:
                st.success(pesan + " Silakan masuk.")
                st.session_state["auth_tab"] = "masuk"
                st.rerun()
            else:
                st.error(pesan)
