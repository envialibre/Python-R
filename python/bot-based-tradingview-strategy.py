import MetaTrader5 as mt5
import pandas as pd
import datetime
import time
import os

# Configuración
symbols = ["XAUUSDm"]
signal_timeframe = mt5.TIMEFRAME_M15
execution_interval = 60
lot_size = 0.05
magic_number = 10001
max_total_trades = 4
max_drawdown_pct = 60
check_drawdown = False

capital_log_file = "capital_log.csv"

# Indicadores
ema_short_length = 11
ema_long_length = 21
rsi_length = 14
rsi_overbought = 70
rsi_oversold = 30
atr_length = 14

# Iniciar MetaTrader 5
if not mt5.initialize():
    print("❌ Error al conectar con MetaTrader 5.")
    quit()

account_info = mt5.account_info()
initial_balance = account_info.balance
print(f"✅ Balance inicial: {initial_balance:.2f} USD")

if not os.path.exists(capital_log_file):
    with open(capital_log_file, 'w') as f:
        f.write("datetime,balance,equity,drawdown_percent\n")

def get_data(symbol, timeframe, bars=100):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def calculate_indicators(df):
    df['ema_short'] = df['close'].ewm(span=ema_short_length).mean()
    df['ema_long'] = df['close'].ewm(span=ema_long_length).mean()

    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=rsi_length).mean()
    avg_loss = loss.rolling(window=rsi_length).mean()
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))

    df['tr'] = df[['high', 'low', 'close']].apply(
        lambda x: max(x['high'] - x['low'],
                      abs(x['high'] - x['close']),
                      abs(x['low'] - x['close'])), axis=1)
    df['atr'] = df['tr'].rolling(window=atr_length).mean()
    return df

def generate_signal(df):
    last = df.iloc[-1]
    long_cond = last['ema_short'] > last['ema_long'] and last['rsi'] < rsi_overbought
    short_cond = last['ema_short'] < last['ema_long'] and last['rsi'] > rsi_oversold
    return long_cond, short_cond, last

def send_order(symbol, signal_type, sl, tp):
    tick = mt5.symbol_info_tick(symbol)
    order_type = mt5.ORDER_TYPE_BUY if signal_type == 'buy' else mt5.ORDER_TYPE_SELL
    price = tick.ask if signal_type == 'buy' else tick.bid

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": magic_number,
        "comment": f"AutoTrade {signal_type}",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"✅ [{symbol}] Orden {signal_type.upper()} enviada.")
    else:
        print(f"❌ [{symbol}] Error al enviar orden: {result.retcode}")

def close_position(position):
    symbol = position.symbol
    volume = position.volume
    ticket = position.ticket
    order_type = mt5.ORDER_TYPE_SELL if position.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
    price = mt5.symbol_info_tick(symbol).bid if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).ask

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "position": ticket,
        "price": price,
        "deviation": 20,
        "magic": magic_number,
        "comment": "Cerrar por señal inversa",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"🔁 [{symbol}] Posición cerrada por señal inversa.")
    else:
        print(f"❌ [{symbol}] Error al cerrar posición: {result.retcode}")

def count_open_trades():
    return len(mt5.positions_get())

def log_capital():
    info = mt5.account_info()
    drawdown = 100 * (initial_balance - info.equity) / initial_balance
    with open(capital_log_file, 'a') as f:
        f.write(f"{datetime.datetime.now()},{info.balance:.2f},{info.equity:.2f},{drawdown:.2f}\n")
    return drawdown

# Bucle de ejecución
while True:
    print(f"\n🕒 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Analizando...")

    drawdown = log_capital()

    if check_drawdown and drawdown >= max_drawdown_pct:
        print(f"🚨 Drawdown crítico ({drawdown:.2f}%) - No se abrirán nuevas operaciones.")
    else:
        open_positions = mt5.positions_get()
        positions_by_symbol = {sym: None for sym in symbols}
        for pos in open_positions:
            if pos.symbol in symbols:
                positions_by_symbol[pos.symbol] = pos

        for symbol in symbols:
            df = get_data(symbol, signal_timeframe)
            if df is None or df.empty:
                print(f"⚠️ No hay datos para {symbol}")
                continue

            df = calculate_indicators(df)
            long_signal, short_signal, last = generate_signal(df)
            atr = last['atr']
            price = last['close']
            sl_mult = 1.5
            tp_mult = 3.0

            # Cierre por señal inversa
            position = positions_by_symbol[symbol]
            if position:
                if position.type == mt5.POSITION_TYPE_BUY and short_signal:
                    close_position(position)
                elif position.type == mt5.POSITION_TYPE_SELL and long_signal:
                    close_position(position)
                else:
                    print(f"[{symbol}] Operación existente mantiene dirección.")
                continue  # No abrir nueva si ya hay una

            # Verificar límite de operaciones
            if count_open_trades() >= max_total_trades:
                print("⚠️ Límite de operaciones activas alcanzado.")
                break

            # Abrir nueva operación si hay señal
            if long_signal:
                sl = price - atr * sl_mult
                tp = price + atr * tp_mult
                send_order(symbol, 'buy', sl, tp)
            elif short_signal:
                sl = price + atr * sl_mult
                tp = price - atr * tp_mult
                send_order(symbol, 'sell', sl, tp)
            else:
                print(f"[{symbol}] No hay señal clara.")

    print("⏳ Esperando 60 segundos...\n")
    time.sleep(execution_interval)

# Cierre al salir (nunca se ejecuta si es loop infinito)
mt5.shutdown()
