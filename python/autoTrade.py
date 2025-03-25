import MetaTrader5 as mt5
import csv
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator
import xgboost as xgb
from colorama import init, Fore
import schedule
import time
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize colorama
init(autoreset=True)

# Configuration
SYMBOL_CONFIG = {
    "BTCUSDm": "M5",
    "XAUUSDm": "M5"
}

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

RISK_PER_TRADE = 0.01  # 1% of account balance
MIN_CONFIDENCE = 0.75
INITIAL_BALANCE = None

# Ensure models folder exists
Path(MODEL_FOLDER).mkdir(exist_ok=True)


def calculate_indicators(df):
    """Calculate technical indicators."""
    df['sma_14'] = SMAIndicator(close=df['close'], window=14).sma_indicator()
    df['rsi_14'] = RSIIndicator(close=df['close'], window=14).rsi()
    df['ema_fast'] = df['close'].ewm(span=5).mean()
    df['ema_slow'] = df['close'].ewm(span=13).mean()
    df.dropna(inplace=True)
    return df


def detect_zone(price, support, resistance):
    """Detect price zone."""
    if price <= support * 1.005:
        return "Cerca de soporte"
    elif price >= resistance * 0.995:
        return "Cerca de resistencia"
    return "Zona media"


def strategy_scalping(df, latest):
    """Scalping strategy logic."""
    direction = None
    if latest['rsi_14'] < 35:
        direction = "BUY"
    elif latest['rsi_14'] > 65:
        direction = "SELL"

    ema_condition = (direction == "BUY" and df['ema_fast'].iloc[-1] > df['ema_slow'].iloc[-1]) or \
                    (direction == "SELL" and df['ema_fast'].iloc[-1] < df['ema_slow'].iloc[-1])

    prev = df.iloc[-2]
    curr = df.iloc[-1]
    engulfing = (direction == "BUY" and prev['close'] < prev['open'] and curr['close'] > curr['open']) or \
                (direction == "SELL" and prev['close'] > prev['open'] and curr['close'] < curr['open'])

    vol_avg = df['tick_volume'][:-1].tail(10).mean()
    vol_condition = latest['tick_volume'] > 0.9 * vol_avg

    if direction and ema_condition and engulfing and vol_condition:
        return direction, True
    return None, False


def strategy_trend(df, latest):
    """Trend-following strategy logic."""
    body = abs(latest['close'] - latest['open'])
    avg_body = np.mean(abs(df['close'][:-1] - df['open'][:-1]).tail(10))
    avg_volume = df['tick_volume'][:-1].tail(10).mean()
    is_impulse = body > 1.5 * avg_body and latest['tick_volume'] > avg_volume

    direction = None
    if latest['close'] > latest['sma_14'] and latest['rsi_14'] > 55:
        direction = "BUY"
    elif latest['close'] < latest['sma_14'] and latest['rsi_14'] < 45:
        direction = "SELL"

    return direction, is_impulse


def run_prediction(symbol, tf_name):
    """Run prediction and execute trades."""
    global INITIAL_BALANCE
    timeframe = TIMEFRAME_MAP[tf_name]
    now = datetime.now()

    if not mt5.initialize():
        logger.error(f"Failed to initialize MT5 for {symbol}")
        return

    account_info = mt5.account_info()
    if account_info is None:
        logger.error("Failed to fetch account info")
        mt5.shutdown()
        return

    balance = account_info.balance
    if INITIAL_BALANCE is None:
        INITIAL_BALANCE = balance

    logger.info(f"Analyzing {symbol} ({tf_name}) | Balance: {balance:.2f} USD")

    if balance < INITIAL_BALANCE * 0.25:
        logger.error("Account balance below 25% of initial balance. Stopping trading.")
        mt5.shutdown()
        return

    # Load model
    model_path = Path(f"{MODEL_FOLDER}/{symbol}_{tf_name}.json")
    if not model_path.exists():
        logger.error(f"Model not found: {model_path}")
        mt5.shutdown()
        return

    model = xgb.XGBClassifier()
    model.load_model(model_path)

    # Fetch historical data
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)
    if rates is None or len(rates) < 20:
        logger.error(f"Insufficient data for {symbol}")
        mt5.shutdown()
        return

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df = calculate_indicators(df)

    latest = df.iloc[-1]
    X_live = pd.DataFrame([{col: latest[col] for col in ['open', 'high', 'low', 'close', 'tick_volume']}])
    X_live['sma_14'] = latest['sma_14']
    X_live['rsi_14'] = latest['rsi_14']

    prediction = model.predict(X_live)[0]
    confidence = model.predict_proba(X_live)[0][prediction]
    model_direction = "BUY" if prediction == 1 else "SELL"

    support = df['low'].tail(30).min()
    resistance = df['high'].tail(30).max()
    price = latest['close']

    if timeframe < mt5.TIMEFRAME_M15:
        direction, is_impulse = strategy_scalping(df, latest)
    else:
        direction, is_impulse = strategy_trend(df, latest)

    zone = detect_zone(price, support, resistance)

    logger.info(f"ML Signal: {model_direction} | Confidence: {confidence:.2%} | Strategy Direction: {direction} | Impulse: {is_impulse}")
    logger.info(f"Zone: {zone} | Price: {price:.2f} | Support: {support:.2f} | Resistance: {resistance:.2f}")

    # Log analysis
    Path("logs").mkdir(exist_ok=True)
    filename = Path(f"logs/{now.strftime('%Y-%m-%d')}_{symbol}_analysis.csv")
    with open(filename, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not filename.exists():
            writer.writerow(["datetime", "price", "support", "resistance", "rsi", "sma", "impulse", "zone", "prediction", "confidence"])
        writer.writerow([
            now.strftime('%Y-%m-%d %H:%M:%S'), price, support, resistance,
            round(latest['rsi_14'], 2), round(latest['sma_14'], 2),
            is_impulse, zone, model_direction, round(confidence, 4)
        ])

    # Execute trade if conditions are met
    if direction and (timeframe < mt5.TIMEFRAME_M15 or is_impulse) and confidence > MIN_CONFIDENCE:
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            logger.error(f"Failed to fetch tick data for {symbol}")
            mt5.shutdown()
            return

        order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
        price = tick.ask if direction == "BUY" else tick.bid
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            logger.error(f"Failed to fetch symbol info for {symbol}")
            mt5.shutdown()
            return

        point = symbol_info.point
        stops_level = symbol_info.stops_level or 50
        min_stop_distance = stops_level * point

        if timeframe >= mt5.TIMEFRAME_M15:
            tp = resistance if direction == "BUY" else support
            sl = support if direction == "BUY" else resistance

            # Adjust SL/TP if too close
            if abs(tp - price) < min_stop_distance:
                tp = price + min_stop_distance if direction == "BUY" else price - min_stop_distance
            if abs(price - sl) < min_stop_distance:
                sl = price - min_stop_distance if direction == "BUY" else price + min_stop_distance
        else:
            tp = price + max(300 * point, min_stop_distance) if direction == "BUY" else price - max(300 * point, min_stop_distance)
            sl = price - max(150 * point, min_stop_distance) if direction == "BUY" else price + max(150 * point, min_stop_distance)

        # Calculate position size based on risk
        risk_amount = balance * RISK_PER_TRADE
        position_size = risk_amount / abs(price - sl)

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": round(position_size, 2),
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 123456,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"Order executed: {direction} @ {price:.2f} | SL: {sl:.2f} | TP: {tp:.2f}")
        else:
            logger.error(f"Order failed: {result.retcode} - {result.comment}")

    mt5.shutdown()


def start_loop():
    """Start the trading loop."""
    for symbol, tf_name in SYMBOL_CONFIG.items():
        schedule.every(5).minutes.do(lambda s=symbol, tf=tf_name: run_prediction(s, tf))
    logger.info("Auto-analysis started for all symbols and timeframes every 5 minutes.")
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    start_loop()