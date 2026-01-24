"""
orchestrator.py

Une TradingAgentsClient + IBKRClient para:
1. Obtener una señal de TA.
2. Ver qué orden se enviaría a IBKR (de momento solo print, sin ejecutar).
"""

from datetime import date as dt_date

from src.ta_client import TradingAgentsClient
from src.ibkr_client import IBKRClient


def main():
    symbol = "AAPL"
    today = dt_date.today().strftime("%Y-%m-%d")

    # 1) Inicializar clientes
    ta_client = TradingAgentsClient(debug=False)
    ib_client = IBKRClient()

    # 2) Conectar a IBKR paper
    ib_client.connect()

    # 3) Obtener decisión de TradingAgents
    decision = ta_client.get_decision(symbol, today)
    action = decision.get("action", "HOLD")
    confidence = decision.get("confidence", 0)
    risk = decision.get("risk_level", "unknown")

    print("=== DECISIÓN TRADINGAGENTS ===")
    print(f"Símbolo:    {symbol}")
    print(f"Fecha:      {today}")
    print(f"Acción:     {action}")
    print(f"Confianza:  {confidence}")
    print(f"Riesgo TA:  {risk}")
    print("================================")

    # 4) Leer posición actual en IBKR
    current_pos = ib_client.get_position(symbol)
    TARGET_POSITION = 10  # hardcoded de ejemplo

    print(f"Posición actual en {symbol}: {current_pos} acciones")

    # 5) Solo imprimir lo que haríamos, sin ejecutar órdenes aún
    if action == "BUY":
        diff = TARGET_POSITION - current_pos
        if diff > 0:
            print(f"[SIMULACIÓN] Enviaría una orden BUY de {diff} acciones de {symbol}.")
        else:
            print("[SIMULACIÓN] Ya estás en o por encima de la posición objetivo, no compraría más.")
    elif action == "SELL":
        if current_pos > 0:
            print(f"[SIMULACIÓN] Enviaría una orden SELL de {current_pos} acciones de {symbol}.")
        else:
            print("[SIMULACIÓN] No tienes posición que vender.")
    else:
        print("[SIMULACIÓN] HOLD → No haría nada.")

    ib_client.disconnect()


if __name__ == "__main__":
    main()
