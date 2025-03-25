from flask import Flask, request, jsonify
from mt5_bridge import send_order_for_symbols

app = Flask(__name__)

# Lista oficial de símbolos válidos
valid_symbols = {
    "XAUUSD": "XAUUSDm",
    "XAUUSDM": "XAUUSDm",
    "BTCUSD": "BTCUSDm",
    "BTCUSDM": "BTCUSDm"
}

@app.route('/webhook', methods=['POST'])
def webhook():
    # Validar que la solicitud venga desde TradingView
    user_agent = request.headers.get("User-Agent", "").lower()
    if "tradingview" not in user_agent:
        return jsonify({'error': '❌ Acceso denegado. Solo se aceptan alertas desde TradingView.'}), 403

    data = request.json
    if not data:
        return jsonify({'error': 'No JSON received'}), 400

    print("📩 Alerta recibida:", data)

    try:
        symbol_raw = data.get("symbol", "").upper().strip()
        mapped_symbol = valid_symbols.get(symbol_raw)

        if not mapped_symbol:
            return jsonify({'error': f"❌ Símbolo '{symbol_raw}' no es válido."}), 400

        signal = data.get("signal")
        entry = float(data.get("entry", 0))
        sl = float(data.get("sl"))
        tp = float(data.get("tp3"))
        tf = data.get("tf", "")

        # Solo enviar orden al símbolo mapeado
        result = send_order_for_symbols(signal, entry, sl, tp, tf, symbol=mapped_symbol)

        return jsonify({'status': 'ok', 'result': str(result)})

    except Exception as e:
        return jsonify({'error': f'Error al procesar la orden: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(port=5000)
