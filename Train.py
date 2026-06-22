"""
train.py — Pipeline training model LSTM untuk prediksi harga cryptocurrency.

Melatih DUA model terpisah: satu untuk BTC-USD, satu untuk ETH-USD.
Model dipisah (bukan digabung) karena skala harga dan volatilitas kedua
koin sangat berbeda — menggabungkan keduanya dalam satu model akan
membutuhkan normalisasi tambahan yang rumit tanpa manfaat akurasi yang
jelas untuk skala skripsi ini.

CARA PAKAI:
    python train.py

OUTPUT yang dihasilkan:
    data/btc_harian.csv      -> data historis harga BTC
    data/eth_harian.csv      -> data historis harga ETH
    model_btc.keras          -> model LSTM untuk BTC
    model_eth.keras          -> model LSTM untuk ETH
    scaler_btc.pkl           -> MinMaxScaler untuk BTC
    scaler_eth.pkl           -> MinMaxScaler untuk ETH

ARSITEKTUR MODEL (sama untuk kedua koin):
    LSTM(64, return_sequences=True) -> Dropout(0.2)
    LSTM(64)                        -> Dropout(0.2)
    Dense(1)

    Lookback: 60 hari   |   Split data: 80% train, 20% test
"""

import os
import pickle
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, r2_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
from tensorflow.keras.callbacks import EarlyStopping

# ===================== KONFIGURASI =====================
LOOKBACK = 60
SPLIT_RATIO = 0.8
EPOCHS = 50
BATCH_SIZE = 32
TANGGAL_MULAI = "2017-01-01"

KOIN_LIST = [
    {"ticker": "BTC-USD", "nama": "BTC", "csv": "data/btc_harian.csv",
     "model_file": "model_btc.keras", "scaler_file": "scaler_btc.pkl"},
    {"ticker": "ETH-USD", "nama": "ETH", "csv": "data/eth_harian.csv",
     "model_file": "model_eth.keras", "scaler_file": "scaler_eth.pkl"},
]


# ===================== LANGKAH 1: AMBIL DATA =====================
def unduh_data(ticker, tanggal_mulai):
    """Unduh data harga harian dari Yahoo Finance lewat yfinance."""
    print(f"📥 Mengunduh data {ticker} dari {tanggal_mulai} sampai sekarang...")
    df = yf.download(ticker, start=tanggal_mulai, progress=False, auto_adjust=True)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    df.index.name = 'Date'
    df = df.reset_index()
    df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
    df = df.dropna(subset=['Close'])

    print(f"✅ Data dimuat: {len(df)} hari ({df['Date'].iloc[0]} s.d. {df['Date'].iloc[-1]})")
    return df


# ===================== LANGKAH 2: SIAPKAN DATASET UNTUK LSTM =====================
def siapkan_dataset(df, lookback=LOOKBACK):
    """
    Ubah deret harga harian menjadi pasangan (X, y) yang dipahami LSTM:
    X = 60 hari harga sebelumnya, y = harga hari ke-61 yang harus diprediksi.
    """
    harga = df['Close'].values.reshape(-1, 1)

    scaler = MinMaxScaler(feature_range=(0, 1))
    harga_scaled = scaler.fit_transform(harga)

    X, y = [], []
    for i in range(lookback, len(harga_scaled)):
        X.append(harga_scaled[i - lookback:i, 0])
        y.append(harga_scaled[i, 0])
    X, y = np.array(X), np.array(y)
    X = X.reshape(X.shape[0], X.shape[1], 1)

    return X, y, scaler


# ===================== LANGKAH 3: BANGUN ARSITEKTUR MODEL =====================
def bangun_model(lookback=LOOKBACK):
    model = Sequential([
        Input(shape=(lookback, 1)),
        LSTM(64, return_sequences=True),
        Dropout(0.2),
        LSTM(64),
        Dropout(0.2),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model


# ===================== LANGKAH 4: TRAINING + EVALUASI SATU KOIN =====================
def latih_satu_koin(konfigurasi):
    nama = konfigurasi["nama"]
    print(f"\n{'='*60}")
    print(f"  TRAINING MODEL UNTUK {nama}")
    print(f"{'='*60}")

    # --- Ambil & simpan data ---
    df = unduh_data(konfigurasi["ticker"], TANGGAL_MULAI)
    os.makedirs(os.path.dirname(konfigurasi["csv"]), exist_ok=True)
    df.to_csv(konfigurasi["csv"], index=False)
    print(f"💾 Data tersimpan di {konfigurasi['csv']}")

    # --- Siapkan dataset ---
    X, y, scaler = siapkan_dataset(df)
    split = int(len(X) * SPLIT_RATIO)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    print(f"Training: {len(X_train)} sampel | Testing: {len(X_test)} sampel")

    # --- Bangun & latih model ---
    model = bangun_model()
    early_stop = EarlyStopping(monitor='loss', patience=5, restore_best_weights=True)

    print(f"🧠 Melatih model {nama} ({EPOCHS} epoch maksimal, early stopping aktif)...")
    model.fit(
        X_train, y_train,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=[early_stop],
        verbose=1
    )

    # --- Evaluasi ---
    y_pred_scaled = model.predict(X_test, verbose=0)
    y_pred = scaler.inverse_transform(y_pred_scaled)
    y_actual = scaler.inverse_transform(y_test.reshape(-1, 1))

    mae = mean_absolute_error(y_actual, y_pred)
    r2 = r2_score(y_actual, y_pred)

    print(f"\n📊 Hasil Evaluasi {nama}:")
    print(f"   MAE: ${mae:,.2f}")
    print(f"   R²:  {r2:.4f} ({r2*100:.1f}%)")

    # --- Simpan model & scaler ---
    model.save(konfigurasi["model_file"])
    with open(konfigurasi["scaler_file"], 'wb') as f:
        pickle.dump(scaler, f)

    print(f"✅ Model tersimpan di {konfigurasi['model_file']}")
    print(f"✅ Scaler tersimpan di {konfigurasi['scaler_file']}")

    return {"nama": nama, "mae": mae, "r2": r2, "jumlah_hari": len(df)}


# ===================== MAIN =====================
def main():
    hasil_semua = []
    for konfigurasi in KOIN_LIST:
        hasil = latih_satu_koin(konfigurasi)
        hasil_semua.append(hasil)

    print(f"\n{'='*60}")
    print("  RINGKASAN SEMUA MODEL")
    print(f"{'='*60}")
    for h in hasil_semua:
        print(f"{h['nama']:5s} | Data: {h['jumlah_hari']:5d} hari | "
              f"MAE: ${h['mae']:>10,.2f} | R²: {h['r2']*100:.1f}%")


if __name__ == "__main__":
    main()