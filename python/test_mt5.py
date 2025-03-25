import MetaTrader5 as mt5

# Inicializa la conexión
if not mt5.initialize():
    print("❌ No se pudo conectar a MetaTrader 5")
    print("Error:", mt5.last_error())
else:
    print("✅ Conexión exitosa a MetaTrader 5")

    # Ver info de la cuenta
    account_info = mt5.account_info()
    if account_info is not None:
        print("🧾 Info de la cuenta:")
        print(f"  Login: {account_info.login}")
        print(f"  Nombre: {account_info.name}")
        print(f"  Balance: {account_info.balance}")
    else:
        print("⚠️ No se pudo obtener la información de la cuenta")

    mt5.shutdown()
