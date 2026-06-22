"""
db.py — Lapisan akses database MySQL (Railway) untuk CryptoAI v2.

Menyimpan tiga hal:
  1. users          -> akun (username, password yang sudah di-hash)
  2. jurnal_trading -> catatan transaksi trading, terikat ke user_id dan koin
  3. preferensi     -> setting per-user, termasuk koin yang sedang dipilih (BTC/ETH)

Data harga (data/btc_harian.csv, data/eth_harian.csv) TETAP berupa file
CSV — bukan data milik user, jadi tidak perlu di MySQL.

KONEKSI:
Kredensial dibaca dari environment variables yang di-inject Railway
otomatis saat MySQL addon dihubungkan ke service ini (lewat
"Add Variable Reference" di Railway dashboard). TIDAK ADA password
yang di-hardcode di file ini.

Jika nama variable di project Railway berbeda, sesuaikan di bagian
"BACA ENV VARIABLES" di bawah — tidak ada bagian lain yang perlu diubah.
"""

import os
import mysql.connector
from mysql.connector import pooling
from datetime import datetime
from contextlib import contextmanager

# ===== BACA ENV VARIABLES (sesuaikan nama di sini jika perlu) =====
DB_HOST = os.environ.get("MYSQLHOST", "localhost")
DB_USER = os.environ.get("MYSQLUSER", "root")
DB_PASSWORD = os.environ.get("MYSQLPASSWORD", "")
DB_NAME = os.environ.get("MYSQLDATABASE", "railway")
DB_PORT = int(os.environ.get("MYSQLPORT", 3306))

_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="cryptoai_pool",
            pool_size=5,
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT,
        )
    return _pool


@contextmanager
def get_conn():
    conn = _get_pool().get_connection()
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Buat tabel jika belum ada. Aman dipanggil berkali-kali (idempotent)."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at DATETIME NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS jurnal_trading (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                koin VARCHAR(10) NOT NULL DEFAULT 'BTC',
                tanggal DATE NOT NULL,
                jenis VARCHAR(10) NOT NULL,
                harga_beli DOUBLE NOT NULL,
                harga_jual DOUBLE NOT NULL,
                jumlah_koin DOUBLE NOT NULL,
                profit_loss DOUBLE NOT NULL,
                catatan TEXT,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS preferensi (
                user_id INT NOT NULL,
                pref_key VARCHAR(50) NOT NULL,
                pref_value VARCHAR(255),
                PRIMARY KEY (user_id, pref_key),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        conn.commit()
        cur.close()


# ===================== USERS =====================

def get_user_by_username(username):
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        cur.close()
        return row


def create_user(username, password_hash):
    """Return True jika berhasil, False jika username sudah dipakai."""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (%s, %s, %s)",
                (username, password_hash, datetime.now())
            )
            conn.commit()
            cur.close()
        return True
    except mysql.connector.IntegrityError:
        return False


# ===================== JURNAL TRADING =====================

def get_jurnal(user_id, koin=None):
    """Jika koin diisi, hanya kembalikan jurnal untuk koin tersebut."""
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        if koin:
            cur.execute(
                "SELECT * FROM jurnal_trading WHERE user_id = %s AND koin = %s ORDER BY tanggal DESC",
                (user_id, koin)
            )
        else:
            cur.execute(
                "SELECT * FROM jurnal_trading WHERE user_id = %s ORDER BY tanggal DESC",
                (user_id,)
            )
        rows = cur.fetchall()
        cur.close()
        return rows


def tambah_jurnal(user_id, koin, tanggal, jenis, harga_beli, harga_jual, jumlah_koin, profit_loss, catatan):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO jurnal_trading
            (user_id, koin, tanggal, jenis, harga_beli, harga_jual, jumlah_koin, profit_loss, catatan, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, koin, tanggal, jenis, harga_beli, harga_jual, jumlah_koin, profit_loss, catatan,
              datetime.now()))
        conn.commit()
        cur.close()


def hapus_semua_jurnal(user_id, koin=None):
    with get_conn() as conn:
        cur = conn.cursor()
        if koin:
            cur.execute("DELETE FROM jurnal_trading WHERE user_id = %s AND koin = %s", (user_id, koin))
        else:
            cur.execute("DELETE FROM jurnal_trading WHERE user_id = %s", (user_id,))
        conn.commit()
        cur.close()


# ===================== PREFERENSI =====================

def get_preferensi(user_id, key, default=None):
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT pref_value FROM preferensi WHERE user_id = %s AND pref_key = %s",
            (user_id, key)
        )
        row = cur.fetchone()
        cur.close()
        return row["pref_value"] if row else default


def set_preferensi(user_id, key, value):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO preferensi (user_id, pref_key, pref_value) VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE pref_value = VALUES(pref_value)
        """, (user_id, key, value))
        conn.commit()
        cur.close()