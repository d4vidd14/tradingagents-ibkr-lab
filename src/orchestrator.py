"""
orchestrator.py

Une TradingAgentsClient + IBKRClient para:
1. Obtener una señal de TA.
2. Ajustar posición en IBKR paper.
"""

from datetime import date as dt_date
import sys
from pathlib import Path

# --- AÑADIR RAÍZ DEL PROYECTO AL PYTHONPATH ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # ...\tradingagents-ibkr-lab
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
# ----------------------------------------------

from src.ta_client import TradingAgentsClient
from src.ibkr_client import IBKRClient


# Si esto está en True -> ENVÍA ÓRDENES REALES en la cuenta PAPER
# Si lo pones en False -> solo imprime lo que haría (modo simulación)
EXECUTE_ORDERS = True


def main():
    symbol = "AAPL"
    today = dt_date.today().strftime("%Y-%m-%d")

    ta_client = TradingAgentsClient(debug=False)
    ib_client = IBKRClient()

    ib_client.connect()

    # 1) Obtener decisión de TradingAgents para HOY
    decision = ta_client.get_decision(symbol, today)
    action = decision.get("action", "HOLD")
    confidence = decision.get("confidence", 0)
    risk = decision.get("risk_level", "unknown")

    print("=== DECISIÓN TRADINGAgents ===")
    print(f"Símbolo:    {symbol}")
    print(f"Fecha:      {today}")
    print(f"Acción:     {action}")
    print(f"Confianza:  {confidence}")
    print(f"Riesgo TA:  {risk}")
    print("================================")

    # 2) Leer posición actual en IBKR
    current_pos = ib_client.get_position(symbol)
    TARGET_POSITION = 10  # objetivo de ejemplo

    print(f"Posición actual en {symbol}: {current_pos} acciones")

    # 3) Lógica simple de órdenes
    if action == "BUY":
        diff = TARGET_POSITION - current_pos
        if diff > 0:
            if EXECUTE_ORDERS:
                print(f"[EJECUTANDO] BUY de {diff} acciones de {symbol}...")
                ib_client.send_market_order(symbol, "BUY", diff)
            else:
                print(f"[SIMULACIÓN] Enviaría BUY de {diff} acciones de {symbol}.")
        else:
            print("Ya estás en o por encima de la posición objetivo, no compro más.")

    elif action == "SELL":
        if current_pos > 0:
            if EXECUTE_ORDERS:
                print(f"[EJECUTANDO] SELL de {current_pos} acciones de {symbol}...")
                ib_client.send_market_order(symbol, "SELL", current_pos)
            else:
                print(f"[SIMULACIÓN] Enviaría SELL de {current_pos} acciones de {symbol}.")
        else:
            print("No tienes posición que vender.")

    else:
        print("HOLD → No hago nada.")

    ib_client.disconnect()


if __name__ == "__main__":
    main()
