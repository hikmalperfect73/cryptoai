import streamlit as st
import bcrypt
from db import get_user_by_username, create_user


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def cek_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def login(username: str, password: str):
    user = get_user_by_username(username)
    if user and cek_password(password, user["password_hash"]):
        st.session_state["user_id"] = user["id"]
        st.session_state["username"] = user["username"]
        return True
    return False


def daftar(username: str, password: str):
    if get_user_by_username(username):
        return False, "Username sudah dipakai."
    hashed = hash_password(password)
    create_user(username, hashed)
    return True, "Akun berhasil dibuat."


def logout():
    st.session_state.pop("user_id", None)
    st.session_state.pop("username", None)


def is_logged_in():
    return "user_id" in st.session_state


def _generate_skyline_svg(width: int = 1600, height: int = 160, seed: int = 42) -> str:
    """SVG skyline deterministik (server-side, tanpa JS, tanpa mask-image)."""
    state = {"s": seed}

    def rng():
        state["s"] = (state["s"] * 1664525 + 1013904223) & 0xFFFFFFFF
        return state["s"] / 4294967296

    buildings = []
    x = 0
    while x < width:
        bw = 18 + int(rng() * 36)
        bh = 30 + int(rng() * 100)
        buildings.append((x, bw, bh))
        x += bw + int(rng() * 6)

    parts = [
        f'<svg viewBox="0 0 {width} {height}" preserveAspectRatio="none" '
        f'xmlns="http://www.w3.org/2000/svg" style="position:absolute;bottom:0;left:0;'
        f'width:100%;height:{height}px;z-index:1;pointer-events:none;">'
    ]
    parts.append(
        '<defs><linearGradient id="bgrad" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#0d2244"/>'
        '<stop offset="100%" stop-color="#071428"/>'
        '</linearGradient></defs>'
    )

    for (bx, bw, bh) in buildings:
        parts.append(
            f'<rect x="{bx}" y="{height - bh}" width="{bw}" height="{bh}" fill="url(#bgrad)"/>'
        )
        # window lights
        rows = max(1, bh // 14)
        cols = max(1, bw // 8)
        for r in range(rows):
            for c in range(cols):
                if rng() > 0.55:
                    wx = bx + 3 + c * 8
                    wy = height - bh + 6 + r * 14
                    if wy + 6 <= height:
                        opacity = 0.5 + rng() * 0.5
                        parts.append(
                            f'<rect x="{wx}" y="{wy}" width="4" height="6" '
                            f'fill="rgba(255,230,100,{opacity:.2f})"/>'
                        )
    parts.append('</svg>')
    return "".join(parts)


def tampilkan_form_auth():
    skyline_svg = _generate_skyline_svg()

    # ── CSS global (selector dengan fallback testid lama & baru) ────────────
    st.markdown(f"""
    <style>
    html, body {{ background: #071428 !important; }}
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    .stApp {{
        background: linear-gradient(160deg, #040d1a 0%, #071428 40%, #0a1f3d 100%) !important;
        min-height: 100vh !important;
        position: relative;
        overflow: hidden;
    }}
    [data-testid="stHeader"], [data-testid="stDecoration"],
    [data-testid="stToolbar"] {{ display: none !important; }}

    .block-container {{
        padding-top: 2rem !important;
        max-width: 700px !important;
        position: relative;
        z-index: 10;
    }}

    /* ---- stars ---- */
    .stars-layer {{
        position: fixed; inset: 0; z-index: 0; pointer-events: none;
        background-image:
            radial-gradient(1px 1px at 12% 18%, rgba(255,255,255,.8) 0%, transparent 100%),
            radial-gradient(1px 1px at 34% 7%,  rgba(255,255,255,.6) 0%, transparent 100%),
            radial-gradient(1px 1px at 56% 22%, rgba(255,255,255,.7) 0%, transparent 100%),
            radial-gradient(1px 1px at 78% 11%, rgba(255,255,255,.5) 0%, transparent 100%),
            radial-gradient(1px 1px at 91% 33%, rgba(255,255,255,.8) 0%, transparent 100%),
            radial-gradient(1px 1px at 7%  45%, rgba(255,255,255,.6) 0%, transparent 100%),
            radial-gradient(1px 1px at 23% 62%, rgba(255,255,255,.4) 0%, transparent 100%),
            radial-gradient(1px 1px at 67% 54%, rgba(255,255,255,.7) 0%, transparent 100%),
            radial-gradient(1px 1px at 45% 78%, rgba(255,255,255,.5) 0%, transparent 100%),
            radial-gradient(1px 1px at 83% 69%, rgba(255,255,255,.6) 0%, transparent 100%);
        animation: twinkle 4s ease-in-out infinite alternate;
    }}
    @keyframes twinkle {{ 0% {{ opacity: .7; }} 100% {{ opacity: 1; }} }}

    .skyline-wrap {{
        position: fixed; bottom: 0; left: 0; width: 100%; height: 160px;
        z-index: 1; pointer-events: none;
    }}

    /* ---- candlestick decorations ---- */
    .candle-wrap {{
        position: fixed; top: 60px; z-index: 1; pointer-events: none;
        display: flex; align-items: flex-end; gap: 6px;
    }}
    .candle-wrap.left  {{ left: 20px; }}
    .candle-wrap.right {{ right: 20px; }}
    .candle {{ display: flex; flex-direction: column; align-items: center; }}
    .wick   {{ width: 2px; background: rgba(255,255,255,.5); }}
    .body   {{ width: 10px; border-radius: 2px; }}
    .bull .body {{ background: #00d97e; }}
    .bear .body {{ background: #ff4560; }}

    /* ---- floating coins ---- */
    .coin {{
        position: fixed; z-index: 2; pointer-events: none;
        font-weight: 900; user-select: none;
        animation: float 6s ease-in-out infinite;
    }}
    @keyframes float {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-18px); }} }}
    .coin-btc {{ color: #f7931a; text-shadow: 0 0 20px #f7931a99; }}
    .coin-eth {{ color: #627eea; text-shadow: 0 0 20px #627eea99; }}

    /* ---- title ---- */
    .crypto-title {{
        text-align: center;
        font-size: 2.4rem;
        font-weight: 800;
        color: #ffffff !important;
        margin: 1.5rem 0 0.3rem;
        letter-spacing: 1px;
        position: relative; z-index: 10;
    }}
    .crypto-sub {{
        text-align: center;
        color: #8ab4d4;
        font-size: 0.95rem;
        margin-bottom: 1.8rem;
        position: relative; z-index: 10;
    }}

    /* ---- tab row (scoped via container key, BUKAN div split) ---- */
    .st-key-auth_tab_row [data-testid="stHorizontalBlock"] {{
        gap: 12px;
        margin-bottom: 1.2rem;
    }}
    .st-key-auth_tab_row button {{
        width: 100% !important;
        border-radius: 10px !important;
        padding: 12px 0 !important;
        font-weight: 600 !important;
        transition: all .2s !important;
    }}
    .st-key-auth_tab_row button[kind="primary"] {{
        background: linear-gradient(90deg, #1a4fc4, #2563eb) !important;
        color: #fff !important;
        border: none !important;
        box-shadow: 0 0 18px #2563eb66 !important;
    }}
    .st-key-auth_tab_row button[kind="secondary"] {{
        background: rgba(255,255,255,.07) !important;
        color: #8ab4d4 !important;
        border: 1px solid rgba(100,160,255,.18) !important;
    }}
    .st-key-auth_tab_row button[kind="secondary"]:hover {{
        background: rgba(255,255,255,.12) !important;
        color: #cfe3ff !important;
    }}

    /* ---- glass card (container key beneran nge-nest semua widget) ---- */
    .st-key-auth_card {{
        background: rgba(10, 25, 60, 0.72) !important;
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border: 1px solid rgba(100,160,255,.18);
        border-radius: 18px;
        padding: 2rem 2.2rem;
        box-shadow: 0 8px 40px rgba(0,0,0,.5), inset 0 1px 0 rgba(255,255,255,.07);
        margin-bottom: 2rem;
    }}
    .st-key-auth_card label {{ color: #ccdeff !important; font-weight: 600 !important; }}
    .st-key-auth_card [data-testid="stTextInput"] input {{
        background: rgba(255,255,255,.07) !important;
        border: 1px solid rgba(100,160,255,.25) !important;
        border-radius: 10px !important;
        color: #fff !important;
        padding: 10px 14px !important;
    }}
    .st-key-auth_card [data-testid="stTextInput"] input:focus {{
        border-color: #2563eb !important;
        box-shadow: 0 0 0 3px rgba(37,99,235,.25) !important;
    }}
    .st-key-auth_card .stButton > button,
    .st-key-auth_card .stFormSubmitButton > button {{
        width: 100% !important;
        background: linear-gradient(90deg, #1a4fc4, #2563eb) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        margin-top: 0.5rem !important;
        box-shadow: 0 4px 18px #2563eb55 !important;
    }}
    .st-key-auth_card .stButton > button:hover,
    .st-key-auth_card .stFormSubmitButton > button:hover {{ opacity: .88 !important; }}
    </style>

    <div class="stars-layer"></div>
    <div class="skyline-wrap">{skyline_svg}</div>

    <div class="candle-wrap left">
        <div class="candle bull"><div class="wick" style="height:24px"></div><div class="body" style="height:36px"></div><div class="wick" style="height:10px"></div></div>
        <div class="candle bear"><div class="wick" style="height:18px"></div><div class="body" style="height:28px"></div><div class="wick" style="height:14px"></div></div>
        <div class="candle bull"><div class="wick" style="height:12px"></div><div class="body" style="height:44px"></div><div class="wick" style="height:8px"></div></div>
        <div class="candle bull"><div class="wick" style="height:20px"></div><div class="body" style="height:32px"></div><div class="wick" style="height:12px"></div></div>
    </div>
    <div class="candle-wrap right">
        <div class="candle bear"><div class="wick" style="height:20px"></div><div class="body" style="height:30px"></div><div class="wick" style="height:16px"></div></div>
        <div class="candle bull"><div class="wick" style="height:14px"></div><div class="body" style="height:42px"></div><div class="wick" style="height:10px"></div></div>
        <div class="candle bear"><div class="wick" style="height:22px"></div><div class="body" style="height:26px"></div><div class="wick" style="height:18px"></div></div>
        <div class="candle bull"><div class="wick" style="height:16px"></div><div class="body" style="height:38px"></div><div class="wick" style="height:12px"></div></div>
    </div>

    <div class="coin coin-btc" style="font-size:2.8rem;left:3%;top:38%;animation-delay:0s">₿</div>
    <div class="coin coin-btc" style="font-size:1.6rem;left:0.5%;top:58%;animation-delay:1.2s">₿</div>
    <div class="coin coin-eth" style="font-size:2.2rem;right:3%;top:42%;animation-delay:0.7s">Ξ</div>
    <div class="coin coin-btc" style="font-size:1.2rem;right:0.3%;top:64%;animation-delay:2s">₿</div>
    <div class="coin coin-eth" style="font-size:1.4rem;left:5%;top:72%;animation-delay:1.8s">Ξ</div>
    <div class="coin coin-btc" style="font-size:3.2rem;right:1%;top:22%;animation-delay:0.4s">₿</div>

    <div class="crypto-title">CryptoAI</div>
    <div class="crypto-sub">Dashboard Prediksi BTC &amp; ETH</div>
    """, unsafe_allow_html=True)

    # ── Tab state ─────────────────────────────────────────────────────────
    if "auth_tab" not in st.session_state:
        st.session_state["auth_tab"] = "masuk"

    with st.container(key="auth_tab_row"):
        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                "Masuk", key="tab_masuk", use_container_width=True,
                type="primary" if st.session_state["auth_tab"] == "masuk" else "secondary",
            ):
                st.session_state["auth_tab"] = "masuk"
                st.rerun()
        with col2:
            if st.button(
                "Daftar", key="tab_daftar", use_container_width=True,
                type="primary" if st.session_state["auth_tab"] == "daftar" else "secondary",
            ):
                st.session_state["auth_tab"] = "daftar"
                st.rerun()

    # ── Form di dalam glass card (beneran ke-nest, bukan div split) ────────
    with st.container(key="auth_card"):
        if st.session_state["auth_tab"] == "masuk":
            with st.form("form_login"):
                username = st.text_input("Email", placeholder="nama@email.com")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Masuk", use_container_width=True)
                if submitted:
                    if login(username, password):
                        st.rerun()
                    else:
                        st.error("Username atau password salah.")
        else:
            with st.form("form_daftar"):
                username = st.text_input("Email", placeholder="nama@email.com")
                password = st.text_input("Password", type="password")
                konfirmasi = st.text_input("Konfirmasi Password", type="password")
                submitted = st.form_submit_button("Daftar", use_container_width=True)
                if submitted:
                    if password != konfirmasi:
                        st.error("Password tidak cocok.")
                    elif len(password) < 6:
                        st.error("Password minimal 6 karakter.")
                    else:
                        ok, msg = daftar(username, password)
                        if ok:
                            st.success(msg + " Silakan masuk.")
                            st.session_state["auth_tab"] = "masuk"
                            st.rerun()
                        else:
                            st.error(msg)
