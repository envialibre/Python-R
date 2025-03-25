import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import os
from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import time
import schedule

# Configuración de símbolos y temporalidades
SYMBOL_CONFIG = {
    "BTCUSDm": "M5",
    "XAUUSDm": "M5"
}

DATA_FOLDER = "market_data"
MODEL_FOLDER = "models"

TIMEFRAME_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
}

# ===============================
# Actualizar datos y reentrenar
# ===============================
def actualizar_datos_y_modelo(symbol, tf_name):
    timeframe = TIMEFRAME_MAP[tf_name]
    file_path = f"{DATA_FOLDER}/{symbol}_{tf_name}_2024-2025.csv"

    if not mt5.initialize():
        print(f"❌ MT5 no conectado para {symbol}")
        return

    if not mt5.symbol_select(symbol, True):
        print(f"❌ No se pudo seleccionar el símbolo {symbol}")
        mt5.shutdown()
        return

    if os.path.exists(file_path):
        df_old = pd.read_csv(file_path)
        last_time = pd.to_datetime(df_old['time']).max()
    else:
        df_old = pd.DataFrame()
        last_time = datetime(2024, 1, 1)

    now = datetime.now()
    rates = mt5.copy_rates_range(symbol, timeframe, last_time + timedelta(seconds=1), now)

    if rates is None or len(rates) == 0:
        print(f"⏳ No hay nuevas velas para {symbol} ({tf_name})")
        mt5.shutdown()
        return

    df_new = pd.DataFrame(rates)
    df_new['time'] = pd.to_datetime(df_new['time'], unit='s')

    df_combined = pd.concat([df_old, df_new], ignore_index=True).drop_duplicates(subset='time')
    os.makedirs(DATA_FOLDER, exist_ok=True)
    df_combined.to_csv(file_path, index=False)
    print(f"✅ Datos actualizados: {symbol} ({tf_name}) | Nuevas velas: {len(df_new)}")

    # Reentrenar modelo
    df = df_combined.copy()
    df['sma_14'] = SMAIndicator(close=df['close'], window=14).sma_indicator()
    df['rsi_14'] = RSIIndicator(close=df['close'], window=14).rsi()
    df['future_close'] = df['close'].shift(-1)
    df['target'] = (df['future_close'] > df['close']).astype(int)
    df.dropna(inplace=True)

    features = ['open', 'high', 'low', 'close', 'tick_volume', 'sma_14', 'rsi_14']
    X = df[features]
    y = df['target']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss')
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"🎯 Modelo reentrenado {symbol} ({tf_name}) - Precisión: {acc:.2%}")

    os.makedirs(MODEL_FOLDER, exist_ok=True)
    model.save_model(f"{MODEL_FOLDER}/{symbol}_{tf_name}.json")
    print(f"💾 Modelo guardado: {MODEL_FOLDER}/{symbol}_{tf_name}.json")

    mt5.shutdown()

# ===============================
# Ejecutar cada 5 minutos
# ===============================
def programar_actualizaciones():
    for symbol, tf in SYMBOL_CONFIG.items():
        schedule.every(60).minutes.do(lambda s=symbol, t=tf: actualizar_datos_y_modelo(s, t))
    print("📅 Programación iniciada. Actualización cada hora...")
    while True:
        schedule.run_pending()
        time.sleep(5)

if __name__ == "__main__":
    for symbol, tf in SYMBOL_CONFIG.items():
        actualizar_datos_y_modelo(symbol, tf)  # ← Ejecuta inmediatamente
    programar_actualizaciones()

