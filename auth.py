"""
auth.py — Logika autentikasi: daftar, login, keluar, dan form UI-nya.

Password TIDAK PERNAH disimpan dalam bentuk asli. Saat daftar, password
diubah jadi hash satu arah dengan bcrypt. Saat login, password yang
diketik diuji terhadap hash tersimpan — bukan dibandingkan langsung.
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
    """Return (berhasil, pesan)."""
    user = db.get_user_by_username(username)
    if not user:
        return False, "Username belum terdaftar."
    if not cek_password(password, user['password_hash']):
        return False, "Password salah."

    st.session_state['user_id'] = user['id']
    st.session_state['username'] = user['username']
    return True, "Login berhasil."


def daftar(username: str, password: str, konfirmasi: str) -> tuple[bool, str]:
    """Return (berhasil, pesan)."""
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
    """
    Render form Login & Daftar dalam dua tab. Dipanggil HANYA ketika
    belum ada user yang login (is_logged_in() == False).
    """
    st.markdown("""
    <div style='text-align:center; padding:32px 0 8px'>
      <div style='width:64px; height:64px;
           background:linear-gradient(135deg,#1d4ed8,#0ea5e9);
           border-radius:18px; display:flex; align-items:center;
           justify-content:center; font-size:32px; margin:0 auto 14px;
           box-shadow:0 4px 24px rgba(59,130,246,0.4)'>₿</div>
      <div style='font-size:22px; font-weight:800; color:#e0f2fe'>CryptoAI</div>
      <div style='font-size:13px; color:#475569; margin-top:2px'>
        Masuk atau daftar untuk mengakses dashboard prediksi BTC & ETH
      </div>
    </div>
    """, unsafe_allow_html=True)

    col_kiri, col_tengah, col_kanan = st.columns([1, 1.4, 1])
    with col_tengah:
        tab_login, tab_daftar = st.tabs(["🔑 Login", "📝 Daftar"])

        with tab_login:
            with st.form("form_login"):
                u = st.text_input("Username", key="login_user")
                p = st.text_input("Password", type="password", key="login_pass")
                submit = st.form_submit_button("Masuk", type="primary", use_container_width=True)
            if submit:
                ok, pesan = login(u, p)
                if ok:
                    st.success(pesan)
                    st.rerun()
                else:
                    st.error(pesan)

        with tab_daftar:
            with st.form("form_daftar"):
                u = st.text_input("Username baru", key="daftar_user")
                p = st.text_input("Password", type="password", key="daftar_pass")
                p2 = st.text_input("Konfirmasi Password", type="password", key="daftar_pass2")
                submit = st.form_submit_button("Buat Akun", type="primary", use_container_width=True)
            if submit:
                ok, pesan = daftar(u, p, p2)
                if ok:
                    st.success(pesan + " Silakan pindah ke tab Login.")
                else:
                    st.error(pesan)