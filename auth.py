"""
auth.py — Logika autentikasi: daftar, login, keluar, dan form UI-nya.
"""

import bcrypt
import streamlit as st
import db

"""
auth.py — Logika autentikasi: daftar, login, keluar, dan form UI-nya.
"""

import bcrypt
import streamlit as st
import db


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def cek_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def is_logged_in() -> bool:
    return st.session_state.get('user_id') is not None


def login(username: str, password: str) -> tuple[bool, str]:
    user = db.get_user_by_username(username)
    if not user:
        return False, "Username belum terdaftar."
    if not cek_password(password, user['password_hash']):
        return False, "Password salah."
    st.session_state['user_id'] = user['id']
    st.session_state['username'] = user['username']
    return True, "Login berhasil."


def daftar(username: str, password: str, konfirmasi: str) -> tuple[bool, str]:
    username = username.strip()
    if len(username) < 3:
        return False, "Username minimal 3 karakter."
    if len(password) < 6:
        return False, "Password minimal 6 karakter."
    if password != konfirmasi:
        return False, "Konfirmasi password tidak cocok."
    if db.get_user_by_username(username):
        return False, "Username sudah dipakai, pilih yang lain."
    berhasil = db.create_user(username, hash_password(password))
    if not berhasil:
        return False, "Username sudah dipakai, pilih yang lain."
    return True, "Akun berhasil dibuat! Silakan login."


def logout():
    for key in ('user_id', 'username'):
        st.session_state.pop(key, None)


def tampilkan_form_auth():
    if 'auth_tab' not in st.session_state:
        st.session_state['auth_tab'] = 'Masuk'

    st.markdown("""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700;800&family=Inter:wght@400;500&family=Geist:wght@500;600&display=swap');

      :root {
        --c-primary: #b5c4ff;
        --c-primary-container: #2f69ff;
        --c-on-primary-container: #fffeff;
        --c-secondary: #ffb874;
        --c-secondary-container: #e78603;
        --c-tertiary: #4cd6ff;
        --c-tertiary-container: #00809d;
        --c-surface-lowest: #070e1d;
        --c-on-surface: #dce2f8;
        --c-outline: #8d90a1;
      }

      [data-testid="stAppViewContainer"] > .main {
        background:
          radial-gradient(ellipse 620px 420px at 8% 10%, rgba(181,196,255,0.07), transparent 55%),
          radial-gradient(ellipse 520px 380px at 95% 90%, rgba(255,184,116,0.06), transparent 55%),
          linear-gradient(180deg, #05080f 0%, #0c1322 100%) !important;
        background-attachment: fixed !important;
      }
      [data-testid="stHeader"] {
        background: linear-gradient(180deg, #05080f 0%, #0c1322 100%) !important;
        border-bottom: 1px solid rgba(181,196,255,0.06);
      }
      [data-testid="stDecoration"] { display: none !important; }

      .auth-koin {
        position: fixed; z-index: 0; pointer-events: none;
        display: flex; align-items: center; justify-content: center;
        border-radius: 50%; font-weight: 800; font-family: 'Plus Jakarta Sans', sans-serif;
      }
      .auth-koin-btc {
        width: 72px; height: 72px; left: 7%; top: 14%; font-size: 30px;
        color: #2d1600;
        background: radial-gradient(circle at 35% 30%, var(--c-secondary), var(--c-secondary-container) 70%);
        box-shadow: 0 0 50px 10px rgba(255,184,116,0.30);
        opacity: 0.85;
        animation: auth-float-a 6.5s ease-in-out infinite;
      }
      .auth-koin-eth {
        width: 54px; height: 54px; right: 9%; bottom: 18%; font-size: 22px;
        color: #001f28;
        background: radial-gradient(circle at 35% 30%, var(--c-tertiary), var(--c-tertiary-container) 70%);
        box-shadow: 0 0 40px 8px rgba(76,214,255,0.28);
        opacity: 0.75;
        animation: auth-float-b 8s ease-in-out infinite;
      }
      @keyframes auth-float-a { 0%,100%{transform:translateY(0) rotate(0deg);}50%{transform:translateY(-18px) rotate(5deg);} }
      @keyframes auth-float-b { 0%,100%{transform:translateY(0) rotate(0deg);}50%{transform:translateY(16px) rotate(-5deg);} }

      .auth-brand { text-align: center; padding: 36px 0 6px; position: relative; z-index: 2; }
      .auth-brand-badge {
        width: 60px; height: 60px; margin: 0 auto 14px;
        display: flex; align-items: center; justify-content: center;
        border-radius: 18px; transform: rotate(12deg);
        font-size: 26px; color: var(--c-on-primary-container);
        background: var(--c-primary-container);
        box-shadow: 0 0 24px rgba(47,105,255,0.45);
      }
      .auth-brand-title {
        font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 800;
        font-size: 24px; color: var(--c-on-surface); letter-spacing: -0.01em;
      }
      .auth-brand-sub {
        font-family: 'Inter', sans-serif; font-size: 13px; color: var(--c-outline);
        margin-top: 4px; opacity: 0.85;
      }

      /* ===== st.radio dijadikan tab bar ===== */
      div[data-testid="stRadio"] > label { display: none !important; }
      div[data-testid="stRadio"] > div {
        display: flex !important;
        gap: 6px !important;
        background: rgba(181,196,255,0.06) !important;
        border-radius: 14px !important;
        padding: 6px !important;
        margin-bottom: 16px !important;
        flex-direction: row !important;
      }
      div[data-testid="stRadio"] > div > label {
        display: flex !important;
        flex: 1 !important;
        align-items: center !important;
        justify-content: center !important;
        border-radius: 10px !important;
        padding: 13px 0 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 17px !important;
        font-weight: 700 !important;
        color: var(--c-outline) !important;
        cursor: pointer !important;
        transition: all 0.18s ease !important;
        margin: 0 !important;
      }
      div[data-testid="stRadio"] > div > label:has(input:checked) {
        background: var(--c-primary-container) !important;
        color: var(--c-on-primary-container) !important;
        box-shadow: 0 6px 16px rgba(47,105,255,0.35) !important;
      }
      /* sembunyikan radio circle asli */
      div[data-testid="stRadio"] > div > label > div:first-child { display: none !important; }
      div[data-testid="stRadio"] > div > label > div:last-child {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 17px !important;
        font-weight: 700 !important;
      }

      /* ===== Kartu form: glass panel ===== */
      .auth-card-wrap [data-testid="stVerticalBlockBorderWrapper"],
      .auth-card-wrap [data-testid="stForm"] {
        background: rgba(25,31,47,0.55) !important;
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 20px !important;
        box-shadow: 0 0 36px 6px rgba(47,105,255,0.10), 0 20px 60px rgba(0,0,0,0.45);
      }
      .auth-card-wrap [data-testid="stForm"] label {
        color: var(--c-outline) !important;
        font-family: 'Geist', sans-serif !important;
        font-weight: 600 !important;
        font-size: 11.5px !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
      }
      .auth-card-wrap [data-testid="stForm"] input {
        background: var(--c-surface-lowest) !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
        border-radius: 12px !important;
        color: var(--c-on-surface) !important;
        padding: 12px 14px !important;
      }
      .auth-card-wrap [data-testid="stForm"] input:focus {
        border-color: var(--c-primary) !important;
        box-shadow: 0 0 0 3px rgba(181,196,255,0.18) !important;
      }
      .auth-card-wrap [data-testid="stFormSubmitButton"] button,
      .auth-card-wrap .stFormSubmitButton button {
        background: var(--c-primary-container) !important;
        color: var(--c-on-primary-container) !important;
        border: none !important;
        border-radius: 14px !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        padding: 14px 0 !important;
        height: auto !important;
        box-shadow: 0 8px 22px rgba(47,105,255,0.28) !important;
      }

      .auth-footer-note {
        text-align: center; font-family: 'Inter', sans-serif; font-size: 12.5px;
        color: var(--c-outline); margin-top: 14px;
      }
      .auth-footer-note b { color: var(--c-primary); }

      .auth-bars {
        display: flex; align-items: flex-end; justify-content: center; gap: 6px;
        height: 56px; max-width: 240px; margin: 28px auto 0; opacity: 0.22;
      }
      .auth-bars div { width: 8px; border-radius: 3px 3px 0 0; background: var(--c-primary); }
    </style>

    <div class="auth-koin auth-koin-btc">&#x20BF;</div>
    <div class="auth-koin auth-koin-eth">&#x39E;</div>

    <div class="auth-brand">
      <div class="auth-brand-badge">&#x20BF;</div>
      <div class="auth-brand-title">Masuk ke CryptoAI</div>
      <div class="auth-brand-sub">Dashboard prediksi BTC &amp; ETH dengan LSTM</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="auth-card-wrap">', unsafe_allow_html=True)
    col_kiri, col_tengah, col_kanan = st.columns([0.7, 1.4, 0.7])
    with col_tengah:
        # st.radio sebagai tab — native Streamlit, pasti bisa diklik
        tab = st.radio(
            "tab",
            ["Masuk", "Daftar"],
            index=0 if st.session_state['auth_tab'] == 'Masuk' else 1,
            horizontal=True,
            key="auth_radio"
        )
        st.session_state['auth_tab'] = tab

        if tab == "Masuk":
            with st.form("form_login"):
                u = st.text_input("Email", key="login_user", placeholder="nama@email.com")
                p = st.text_input("Password", type="password", key="login_pass", placeholder="••••••••")
                submit = st.form_submit_button("Masuk", type="primary", use_container_width=True)
            if submit:
                ok, pesan = login(u, p)
                if ok:
                    st.success(pesan)
                    st.rerun()
                else:
                    st.error(pesan)
            st.markdown(
                "<div class='auth-footer-note'>Belum punya akun? Klik tab <b>Daftar</b> di atas.</div>",
                unsafe_allow_html=True
            )
        else:
            with st.form("form_daftar"):
                u  = st.text_input("Email", key="daftar_user", placeholder="nama@email.com")
                p  = st.text_input("Password", type="password", key="daftar_pass", placeholder="Minimal 6 karakter")
                p2 = st.text_input("Konfirmasi Password", type="password", key="daftar_pass2", placeholder="Ulangi password")
                submit = st.form_submit_button("Buat Akun", type="primary", use_container_width=True)
            if submit:
                ok, pesan = daftar(u, p, p2)
                if ok:
                    st.success(pesan + " Silakan pindah ke tab Masuk.")
                else:
                    st.error(pesan)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="auth-bars">
      <div style="height:40%"></div><div style="height:65%"></div><div style="height:35%"></div>
      <div style="height:85%"></div><div style="height:55%"></div><div style="height:95%"></div>
      <div style="height:45%"></div><div style="height:70%"></div>
    </div>
    """, unsafe_allow_html=True)
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def cek_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def is_logged_in() -> bool:
    return st.session_state.get('user_id') is not None


def login(username: str, password: str) -> tuple[bool, str]:
    user = db.get_user_by_username(username)
    if not user:
        return False, "Username belum terdaftar."
    if not cek_password(password, user['password_hash']):
        return False, "Password salah."
    st.session_state['user_id'] = user['id']
    st.session_state['username'] = user['username']
    return True, "Login berhasil."


def daftar(username: str, password: str, konfirmasi: str) -> tuple[bool, str]:
    username = username.strip()
    if len(username) < 3:
        return False, "Username minimal 3 karakter."
    if len(password) < 6:
        return False, "Password minimal 6 karakter."
    if password != konfirmasi:
        return False, "Konfirmasi password tidak cocok."
    if db.get_user_by_username(username):
        return False, "Username sudah dipakai, pilih yang lain."
    berhasil = db.create_user(username, hash_password(password))
    if not berhasil:
        return False, "Username sudah dipakai, pilih yang lain."
    return True, "Akun berhasil dibuat! Silakan login."


def logout():
    for key in ('user_id', 'username'):
        st.session_state.pop(key, None)


def tampilkan_form_auth():
    if 'auth_tab' not in st.session_state:
        st.session_state['auth_tab'] = 'Masuk'

    st.markdown("""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700;800&family=Inter:wght@400;500&family=Geist:wght@500;600&display=swap');

      :root {
        --c-primary: #b5c4ff;
        --c-primary-container: #2f69ff;
        --c-on-primary-container: #fffeff;
        --c-secondary: #ffb874;
        --c-secondary-container: #e78603;
        --c-tertiary: #4cd6ff;
        --c-tertiary-container: #00809d;
        --c-surface-lowest: #070e1d;
        --c-on-surface: #dce2f8;
        --c-outline: #8d90a1;
      }

      [data-testid="stAppViewContainer"] > .main {
        background:
          radial-gradient(ellipse 620px 420px at 8% 10%, rgba(181,196,255,0.07), transparent 55%),
          radial-gradient(ellipse 520px 380px at 95% 90%, rgba(255,184,116,0.06), transparent 55%),
          linear-gradient(180deg, #05080f 0%, #0c1322 100%) !important;
        background-attachment: fixed !important;
      }
      [data-testid="stHeader"] {
        background: linear-gradient(180deg, #05080f 0%, #0c1322 100%) !important;
        border-bottom: 1px solid rgba(181,196,255,0.06);
      }
      [data-testid="stDecoration"] { display: none !important; }

      .auth-koin {
        position: fixed; z-index: 0; pointer-events: none;
        display: flex; align-items: center; justify-content: center;
        border-radius: 50%; font-weight: 800; font-family: 'Plus Jakarta Sans', sans-serif;
      }
      .auth-koin-btc {
        width: 72px; height: 72px; left: 7%; top: 14%; font-size: 30px;
        color: #2d1600;
        background: radial-gradient(circle at 35% 30%, var(--c-secondary), var(--c-secondary-container) 70%);
        box-shadow: 0 0 50px 10px rgba(255,184,116,0.30);
        opacity: 0.85;
        animation: auth-float-a 6.5s ease-in-out infinite;
      }
      .auth-koin-eth {
        width: 54px; height: 54px; right: 9%; bottom: 18%; font-size: 22px;
        color: #001f28;
        background: radial-gradient(circle at 35% 30%, var(--c-tertiary), var(--c-tertiary-container) 70%);
        box-shadow: 0 0 40px 8px rgba(76,214,255,0.28);
        opacity: 0.75;
        animation: auth-float-b 8s ease-in-out infinite;
      }
      @keyframes auth-float-a { 0%,100%{transform:translateY(0) rotate(0deg);}50%{transform:translateY(-18px) rotate(5deg);} }
      @keyframes auth-float-b { 0%,100%{transform:translateY(0) rotate(0deg);}50%{transform:translateY(16px) rotate(-5deg);} }

      .auth-brand { text-align: center; padding: 36px 0 6px; position: relative; z-index: 2; }
      .auth-brand-badge {
        width: 60px; height: 60px; margin: 0 auto 14px;
        display: flex; align-items: center; justify-content: center;
        border-radius: 18px; transform: rotate(12deg);
        font-size: 26px; color: var(--c-on-primary-container);
        background: var(--c-primary-container);
        box-shadow: 0 0 24px rgba(47,105,255,0.45);
      }
      .auth-brand-title {
        font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 800;
        font-size: 24px; color: var(--c-on-surface); letter-spacing: -0.01em;
      }
      .auth-brand-sub {
        font-family: 'Inter', sans-serif; font-size: 13px; color: var(--c-outline);
        margin-top: 4px; opacity: 0.85;
      }

      /* ===== st.radio dijadikan tab bar ===== */
      div[data-testid="stRadio"] > label { display: none !important; }
      div[data-testid="stRadio"] > div {
        display: flex !important;
        gap: 6px !important;
        background: rgba(181,196,255,0.06) !important;
        border-radius: 14px !important;
        padding: 6px !important;
        margin-bottom: 16px !important;
        flex-direction: row !important;
      }
      div[data-testid="stRadio"] > div > label {
        display: flex !important;
        flex: 1 !important;
        align-items: center !important;
        justify-content: center !important;
        border-radius: 10px !important;
        padding: 13px 0 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 17px !important;
        font-weight: 700 !important;
        color: var(--c-outline) !important;
        cursor: pointer !important;
        transition: all 0.18s ease !important;
        margin: 0 !important;
      }
      div[data-testid="stRadio"] > div > label:has(input:checked) {
        background: var(--c-primary-container) !important;
        color: var(--c-on-primary-container) !important;
        box-shadow: 0 6px 16px rgba(47,105,255,0.35) !important;
      }
      /* sembunyikan radio circle asli */
      div[data-testid="stRadio"] > div > label > div:first-child { display: none !important; }
      div[data-testid="stRadio"] > div > label > div:last-child {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 17px !important;
        font-weight: 700 !important;
      }

      /* ===== Kartu form: glass panel ===== */
      .auth-card-wrap [data-testid="stVerticalBlockBorderWrapper"],
      .auth-card-wrap [data-testid="stForm"] {
        background: rgba(25,31,47,0.55) !important;
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 20px !important;
        box-shadow: 0 0 36px 6px rgba(47,105,255,0.10), 0 20px 60px rgba(0,0,0,0.45);
      }
      .auth-card-wrap [data-testid="stForm"] label {
        color: var(--c-outline) !important;
        font-family: 'Geist', sans-serif !important;
        font-weight: 600 !important;
        font-size: 11.5px !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
      }
      .auth-card-wrap [data-testid="stForm"] input {
        background: var(--c-surface-lowest) !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
        border-radius: 12px !important;
        color: var(--c-on-surface) !important;
        padding: 12px 14px !important;
      }
      .auth-card-wrap [data-testid="stForm"] input:focus {
        border-color: var(--c-primary) !important;
        box-shadow: 0 0 0 3px rgba(181,196,255,0.18) !important;
      }
      .auth-card-wrap [data-testid="stFormSubmitButton"] button,
      .auth-card-wrap .stFormSubmitButton button {
        background: var(--c-primary-container) !important;
        color: var(--c-on-primary-container) !important;
        border: none !important;
        border-radius: 14px !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        padding: 14px 0 !important;
        height: auto !important;
        box-shadow: 0 8px 22px rgba(47,105,255,0.28) !important;
      }

      .auth-footer-note {
        text-align: center; font-family: 'Inter', sans-serif; font-size: 12.5px;
        color: var(--c-outline); margin-top: 14px;
      }
      .auth-footer-note b { color: var(--c-primary); }

      .auth-bars {
        display: flex; align-items: flex-end; justify-content: center; gap: 6px;
        height: 56px; max-width: 240px; margin: 28px auto 0; opacity: 0.22;
      }
      .auth-bars div { width: 8px; border-radius: 3px 3px 0 0; background: var(--c-primary); }
    </style>

    <div class="auth-koin auth-koin-btc">&#x20BF;</div>
    <div class="auth-koin auth-koin-eth">&#x39E;</div>

    <div class="auth-brand">
      <div class="auth-brand-badge">&#x20BF;</div>
      <div class="auth-brand-title">Masuk ke CryptoAI</div>
      <div class="auth-brand-sub">Dashboard prediksi BTC &amp; ETH dengan LSTM</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="auth-card-wrap">', unsafe_allow_html=True)
    col_kiri, col_tengah, col_kanan = st.columns([0.7, 1.4, 0.7])
    with col_tengah:
        # st.radio sebagai tab — native Streamlit, pasti bisa diklik
        tab = st.radio(
            "tab",
            ["Masuk", "Daftar"],
            index=0 if st.session_state['auth_tab'] == 'Masuk' else 1,
            horizontal=True,
            key="auth_radio"
        )
        st.session_state['auth_tab'] = tab

        if tab == "Masuk":
            with st.form("form_login"):
                u = st.text_input("Email", key="login_user", placeholder="nama@email.com")
                p = st.text_input("Password", type="password", key="login_pass", placeholder="••••••••")
                submit = st.form_submit_button("Masuk", type="primary", use_container_width=True)
            if submit:
                ok, pesan = login(u, p)
                if ok:
                    st.success(pesan)
                    st.rerun()
                else:
                    st.error(pesan)
            st.markdown(
                "<div class='auth-footer-note'>Belum punya akun? Klik tab <b>Daftar</b> di atas.</div>",
                unsafe_allow_html=True
            )
        else:
            with st.form("form_daftar"):
                u  = st.text_input("Email", key="daftar_user", placeholder="nama@email.com")
                p  = st.text_input("Password", type="password", key="daftar_pass", placeholder="Minimal 6 karakter")
                p2 = st.text_input("Konfirmasi Password", type="password", key="daftar_pass2", placeholder="Ulangi password")
                submit = st.form_submit_button("Buat Akun", type="primary", use_container_width=True)
            if submit:
                ok, pesan = daftar(u, p, p2)
                if ok:
                    st.success(pesan + " Silakan pindah ke tab Masuk.")
                else:
                    st.error(pesan)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="auth-bars">
      <div style="height:40%"></div><div style="height:65%"></div><div style="height:35%"></div>
      <div style="height:85%"></div><div style="height:55%"></div><div style="height:95%"></div>
      <div style="height:45%"></div><div style="height:70%"></div>
    </div>
    """, unsafe_allow_html=True)
