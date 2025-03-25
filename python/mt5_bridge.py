# Importamos las librerías necesarias
import MetaTrader5 as mt5
import json
import os
import csv
from datetime import datetime

# ----------------------------
# Configuraciones y constantes
# ----------------------------
CONFIG_FILE = "config.json"
EQUITY_LOG_FILE = "equity_log.csv"
BALANCE_LOG_FILE = "balance_log.csv"
symbols_to_trade = ["BTCUSDm", "XAUUSDm"]
default_lot = 0.05
max_open_positions = 4

# ----------------------------
# Obtener o inicializar el capital inicial
# ----------------------------
def get_initial_capital():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        return config.get("initial_capital")
    else:
        if not mt5.initialize():
            print(f"❌ Error inicializando MT5 para leer capital inicial: {mt5.last_error()}")
            return 1000.0
        account_info = mt5.account_info()
        if account_info is None:
            print("❌ No se pudo obtener información de la cuenta para capital inicial.")
            return 1000.0
        initial_capital = account_info.balance
        with open(CONFIG_FILE, "w") as f:
            json.dump({"initial_capital": initial_capital}, f)
        mt5.shutdown()
        return initial_capital

# ----------------------------
# Registrar equity en CSV
# ----------------------------
def log_equity(equity):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(EQUITY_LOG_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, equity])

# ----------------------------
# Registrar balance en CSV
# ----------------------------
def log_balance(balance):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(BALANCE_LOG_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, balance])

# ----------------------------
# Enviar orden para los símbolos definidos
# ----------------------------
def send_order_for_symbols(signal, entry, sl, tp, tf=None, symbol=None):
    results = []

    if not mt5.initialize():
        error_msg = f"❌ Error inicializando MT5: {mt5.last_error()}"
        print(error_msg)
        return [error_msg]

    account_info = mt5.account_info()
    if account_info is None:
        mt5.shutdown()
        error_msg = "❌ No se pudo obtener la información de la cuenta."
        print(error_msg)
        return [error_msg]

    equity = account_info.equity
    balance = account_info.balance

    log_equity(equity)
    log_balance(balance)

    initial_capital = get_initial_capital()
    equity_threshold = initial_capital * 0.4

    # if equity <= equity_threshold:
    #     mt5.shutdown()
    #     msg = f"🛑 Equity actual (${equity:.2f}) ha bajado más del 60% del capital inicial (${initial_capital:.2f}). No se abrirán más operaciones."
    #     print(msg)
    #     return [msg]

    positions = mt5.positions_get()
    current_open_lots = sum(pos.volume for pos in positions if pos.volume == default_lot) if positions else 0
    if current_open_lots >= (max_open_positions * default_lot):
        mt5.shutdown()
        msg = f"🚫 Ya hay {int(current_open_lots / default_lot)} operaciones de {default_lot} lotes abiertas. Máximo permitido: {max_open_positions}."
        print(msg)
        return [msg]

    signal = signal.strip().upper()
    tf = str(tf or "").lower()
    usar_validacion_manual = tf in ["1", "5"]

    # Lista de símbolos a usar: uno solo si se especifica, o todos por defecto
    symbols = [symbol] if symbol else symbols_to_trade

    for symbol in symbols:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            msg = f"❌ Símbolo '{symbol}' no encontrado."
            print(msg)
            results.append(msg)
            continue

        if not symbol_info.visible:
            if not mt5.symbol_select(symbol, True):
                msg = f"❌ No se pudo activar el símbolo '{symbol}'."
                print(msg)
                results.append(msg)
                continue

        order_type = mt5.ORDER_TYPE_BUY if signal == "BUY" else mt5.ORDER_TYPE_SELL
        current_price = symbol_info.ask if signal == "BUY" else symbol_info.bid

        sl_diff = abs(current_price - sl)
        tp_diff = abs(tp - current_price)
        new_sl = current_price - sl_diff if signal == "BUY" else current_price + sl_diff
        new_tp = current_price + tp_diff if signal == "BUY" else current_price - tp_diff

        if usar_validacion_manual:
            min_distance_points = 100
            min_distance_price = min_distance_points * symbol_info.point
            print(f"⏱️ TF: {tf} | {symbol} → Validación manual activa")

            if signal == "BUY":
                if (current_price - new_sl) < min_distance_price or (new_tp - current_price) < min_distance_price:
                    msg = f"❌ SL o TP muy cercanos para {symbol} en BUY."
                    print(msg)
                    results.append(msg)
                    continue
            else:
                if (new_sl - current_price) < min_distance_price or (current_price - new_tp) < min_distance_price:
                    msg = f"❌ SL o TP muy cercanos para {symbol} en SELL."
                    print(msg)
                    results.append(msg)
                    continue
        else:
            print(f"⏱️ TF: {tf} | {symbol} → Sin validación manual")

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": default_lot,
            "type": order_type,
            "price": current_price,
            "sl": new_sl,
            "tp": new_tp,
            "deviation": 20,
            "magic": 123456,
            "comment": f"{signal} auto",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)

        if result is None:
            error_code = mt5.last_error()
            msg = f"❌ {symbol}: error al enviar la orden. Sin respuesta de MT5. Último error: {error_code}"
        else:
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                msg = f"✅ {symbol}: orden {signal} enviada correctamente. Precio: {current_price:.2f}, SL: {new_sl:.2f}, TP: {new_tp:.2f}"
            else:
                msg = f"❌ {symbol}: error al enviar la orden. Código: {result.retcode}"

        print(f"📤 Orden enviada: {signal} | {symbol} | Precio: {current_price:.2f} | SL: {new_sl:.2f} | TP: {new_tp:.2f}")
        print(f"🧾 Resultado: {msg}")
        results.append(msg)

    mt5.shutdown()
    return results
