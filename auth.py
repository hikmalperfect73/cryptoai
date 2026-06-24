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

def tampilkan_form_auth():
    # ── Base CSS + background + card ──────────────────────────────────────────
    st.markdown("""
    <style>
    /* ---- reset & fullscreen background ---- */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
        background: transparent !important;
    }
    [data-testid="stAppViewContainer"] > .main {
        background: linear-gradient(160deg, #040d1a 0%, #071428 40%, #0a1f3d 100%);
        min-height: 100vh;
        position: relative;
        overflow: hidden;
    }
    [data-testid="stHeader"], [data-testid="stDecoration"],
    [data-testid="stToolbar"] { display: none !important; }

    .block-container {
        padding-top: 0 !important;
        max-width: 700px !important;
        position: relative;
        z-index: 10;
    }

    /* ---- stars ---- */
    .stars-layer {
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
    }
    @keyframes twinkle {
        0%   { opacity: .7; }
        100% { opacity: 1; }
    }

    /* ---- candlestick decorations (pure CSS, no mask) ---- */
    .candle-wrap {
        position: fixed; top: 60px; z-index: 1; pointer-events: none;
        display: flex; align-items: flex-end; gap: 6px;
    }
    .candle-wrap.left  { left: 20px; }
    .candle-wrap.right { right: 20px; }
    .candle { display: flex; flex-direction: column; align-items: center; }
    .wick   { width: 2px; background: rgba(255,255,255,.5); }
    .body   { width: 10px; border-radius: 2px; }
    .bull .body { background: #00d97e; }
    .bear .body { background: #ff4560; }

    /* ---- floating crypto coins ---- */
    .coin {
        position: fixed; z-index: 2; pointer-events: none;
        font-weight: 900; user-select: none;
        animation: float 6s ease-in-out infinite;
    }
    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50%       { transform: translateY(-18px); }
    }
    .coin-btc { color: #f7931a; text-shadow: 0 0 20px #f7931a99; }
    .coin-eth { color: #627eea; text-shadow: 0 0 20px #627eea99; }

    /* ---- title ---- */
    .crypto-title {
        text-align: center;
        font-size: 2.4rem;
        font-weight: 800;
        color: #fff;
        margin: 2.5rem 0 0.3rem;
        letter-spacing: 1px;
    }
    .crypto-sub {
        text-align: center;
        color: #8ab4d4;
        font-size: 0.95rem;
        margin-bottom: 1.8rem;
    }

    /* ---- tab buttons (custom, replaces st.tabs) ---- */
    .tab-row {
        display: flex; gap: 12px; margin-bottom: 1.2rem;
    }
    .tab-btn {
        flex: 1; padding: 12px 0; border: none; border-radius: 10px;
        font-size: 1rem; font-weight: 600; cursor: pointer;
        transition: all .2s;
    }
    .tab-btn.active {
        background: linear-gradient(90deg, #1a4fc4, #2563eb);
        color: #fff;
        box-shadow: 0 0 18px #2563eb66;
    }
    .tab-btn.inactive {
        background: rgba(255,255,255,.07);
        color: #8ab4d4;
    }
    .tab-btn.inactive:hover { background: rgba(255,255,255,.12); }

    /* ---- glassmorphism card ---- */
    .glass-card {
        background: rgba(10, 25, 60, 0.72);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border: 1px solid rgba(100,160,255,.18);
        border-radius: 18px;
        padding: 2rem 2.2rem 2rem;
        box-shadow: 0 8px 40px rgba(0,0,0,.5), inset 0 1px 0 rgba(255,255,255,.07);
        margin-bottom: 2rem;
    }

    /* ---- form fields inside card ---- */
    .glass-card label { color: #ccdeff !important; font-weight: 600 !important; }
    .glass-card [data-testid="stTextInput"] input {
        background: rgba(255,255,255,.07) !important;
        border: 1px solid rgba(100,160,255,.25) !important;
        border-radius: 10px !important;
        color: #fff !important;
        padding: 10px 14px !important;
    }
    .glass-card [data-testid="stTextInput"] input:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 3px rgba(37,99,235,.25) !important;
    }

    /* ---- submit button ---- */
    .glass-card .stButton > button,
    .glass-card .stFormSubmitButton > button,
    .glass-card button[kind="formSubmit"],
    .glass-card button[kind="primary"] {
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
        transition: opacity .2s !important;
    }
    .glass-card .stButton > button:hover,
    .glass-card .stFormSubmitButton > button:hover {
        opacity: .88 !important;
    }

    /* ---- skyline canvas ---- */
    #skyline-canvas {
        position: fixed; bottom: 0; left: 0; width: 100%; z-index: 1;
        pointer-events: none;
    }
    </style>

    <!-- stars -->
    <div class="stars-layer"></div>

    <!-- skyline canvas (JS drawn — no mask-image needed) -->
    <canvas id="skyline-canvas" height="160"></canvas>

    <!-- candlestick left -->
    <div class="candle-wrap left">
        <div class="candle bull"><div class="wick" style="height:24px"></div><div class="body" style="height:36px"></div><div class="wick" style="height:10px"></div></div>
        <div class="candle bear"><div class="wick" style="height:18px"></div><div class="body" style="height:28px"></div><div class="wick" style="height:14px"></div></div>
        <div class="candle bull"><div class="wick" style="height:12px"></div><div class="body" style="height:44px"></div><div class="wick" style="height:8px"></div></div>
        <div class="candle bull"><div class="wick" style="height:20px"></div><div class="body" style="height:32px"></div><div class="wick" style="height:12px"></div></div>
    </div>

    <!-- candlestick right -->
    <div class="candle-wrap right">
        <div class="candle bear"><div class="wick" style="height:20px"></div><div class="body" style="height:30px"></div><div class="wick" style="height:16px"></div></div>
        <div class="candle bull"><div class="wick" style="height:14px"></div><div class="body" style="height:42px"></div><div class="wick" style="height:10px"></div></div>
        <div class="candle bear"><div class="wick" style="height:22px"></div><div class="body" style="height:26px"></div><div class="wick" style="height:18px"></div></div>
        <div class="candle bull"><div class="wick" style="height:16px"></div><div class="body" style="height:38px"></div><div class="wick" style="height:12px"></div></div>
    </div>

    <!-- floating coins -->
    <div class="coin coin-btc" style="font-size:2.8rem;left:3%;top:38%;animation-delay:0s">₿</div>
    <div class="coin coin-btc" style="font-size:1.6rem;left:0.5%;top:58%;animation-delay:1.2s">₿</div>
    <div class="coin coin-eth" style="font-size:2.2rem;right:3%;top:42%;animation-delay:0.7s">Ξ</div>
    <div class="coin coin-btc" style="font-size:1.2rem;right:0.3%;top:64%;animation-delay:2s">₿</div>
    <div class="coin coin-eth" style="font-size:1.4rem;left:5%;top:72%;animation-delay:1.8s">Ξ</div>
    <div class="coin coin-btc" style="font-size:3.2rem;right:1%;top:22%;animation-delay:0.4s">₿</div>

    <!-- title -->
    <div class="crypto-title">CryptoAI</div>
    <div class="crypto-sub">Dashboard Prediksi BTC &amp; ETH</div>

    <script>
    // ── Skyline canvas (cross-browser, no mask-image) ─────────────────────
    (function() {
        function drawSkyline() {
            var canvas = document.getElementById('skyline-canvas');
            if (!canvas) { setTimeout(drawSkyline, 200); return; }
            var W = window.innerWidth, H = 160;
            canvas.width = W; canvas.height = H;
            var ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, W, H);

            // silhouette fill gradient
            var grad = ctx.createLinearGradient(0, 0, 0, H);
            grad.addColorStop(0, '#0d2244');
            grad.addColorStop(1, '#071428');
            ctx.fillStyle = grad;

            ctx.beginPath();
            ctx.moveTo(0, H);
            var x = 0;
            var seed = 42;
            function rng() { seed = (seed * 1664525 + 1013904223) & 0xffffffff; return (seed >>> 0) / 4294967296; }
            while (x < W) {
                var bw = 18 + Math.floor(rng() * 36);
                var bh = 30 + Math.floor(rng() * 100);
                ctx.lineTo(x, H - bh);
                // add 1-3 step-ups (floors)
                var floors = Math.floor(rng() * 3);
                for (var f = 0; f < floors; f++) {
                    var fw = Math.floor(bw * (0.3 + rng() * 0.4));
                    var fh = 10 + Math.floor(rng() * 20);
                    var fx = x + Math.floor((bw - fw) / 2);
                    ctx.lineTo(fx, H - bh);
                    ctx.lineTo(fx, H - bh - fh);
                    ctx.lineTo(fx + fw, H - bh - fh);
                    ctx.lineTo(fx + fw, H - bh);
                }
                ctx.lineTo(x + bw, H - bh);
                ctx.lineTo(x + bw, H);
                x += bw + Math.floor(rng() * 6);
            }
            ctx.lineTo(W, H);
            ctx.closePath();
            ctx.fill();

            // yellow window lights
            seed = 42; x = 0;
            while (x < W) {
                var bw2 = 18 + Math.floor(rng() * 36);
                var bh2 = 30 + Math.floor(rng() * 100);
                var floors2 = Math.floor(rng() * 3);
                for (var r = 0; r < Math.floor(bh2 / 14); r++) {
                    for (var c = 0; c < Math.floor(bw2 / 8); c++) {
                        if (rng() > 0.55) {
                            ctx.fillStyle = 'rgba(255,230,100,' + (0.5 + rng() * 0.5) + ')';
                            ctx.fillRect(x + 3 + c * 8, H - bh2 + 6 + r * 14, 4, 6);
                        }
                    }
                }
                // consume same rng calls for floors
                for (var f2 = 0; f2 < floors2; f2++) { rng(); rng(); rng(); rng(); }
                x += bw2 + Math.floor(rng() * 6);
            }
        }
        drawSkyline();
        window.addEventListener('resize', drawSkyline);
    })();
    </script>
    """, unsafe_allow_html=True)

    # ── Tab state ─────────────────────────────────────────────────────────────
    if "auth_tab" not in st.session_state:
        st.session_state["auth_tab"] = "masuk"

    col1, col2 = st.columns(2)
    with col1:
        cls1 = "active" if st.session_state["auth_tab"] == "masuk" else "inactive"
        if st.button("Masuk", key="tab_masuk", use_container_width=True):
            st.session_state["auth_tab"] = "masuk"
            st.rerun()
    with col2:
        cls2 = "active" if st.session_state["auth_tab"] == "daftar" else "inactive"
        if st.button("Daftar", key="tab_daftar", use_container_width=True):
            st.session_state["auth_tab"] = "daftar"
            st.rerun()

    # Style the two tab buttons based on active state via JS targeting key attribute
    st.markdown(f"""
    <script>
    (function applyTabStyle() {{
        var btns = document.querySelectorAll('button[data-testid="baseButton-secondary"]');
        var found = 0;
        btns.forEach(function(b) {{
            var key = b.closest('[data-testid]') ? b.innerText.trim() : '';
            if (b.innerText.trim() === 'Masuk') {{
                b.style.cssText = '{"background:linear-gradient(90deg,#1a4fc4,#2563eb);color:#fff;border:none;border-radius:10px;width:100%;padding:12px;font-size:1rem;font-weight:700;box-shadow:0 0 18px #2563eb66;" if st.session_state["auth_tab"]=="masuk" else "background:rgba(255,255,255,.07);color:#8ab4d4;border:none;border-radius:10px;width:100%;padding:12px;font-size:1rem;font-weight:600;"}';
            }}
            if (b.innerText.trim() === 'Daftar') {{
                b.style.cssText = '{"background:linear-gradient(90deg,#1a4fc4,#2563eb);color:#fff;border:none;border-radius:10px;width:100%;padding:12px;font-size:1rem;font-weight:700;box-shadow:0 0 18px #2563eb66;" if st.session_state["auth_tab"]=="daftar" else "background:rgba(255,255,255,.07);color:#8ab4d4;border:none;border-radius:10px;width:100%;padding:12px;font-size:1rem;font-weight:600;"}';
            }}
        }});
        // retry until buttons are in DOM
        if (document.querySelectorAll('button[data-testid="baseButton-secondary"]').length < 2) {{
            setTimeout(applyTabStyle, 100);
        }}
    }})();
    </script>
    """, unsafe_allow_html=True)

    # ── Forms inside glass card ───────────────────────────────────────────────
    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)

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

        st.markdown('</div>', unsafe_allow_html=True)
