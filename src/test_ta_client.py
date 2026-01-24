from datetime import date as dt_date
import sys
from pathlib import Path

# --- HACK: añadir repo TradingAgents al PYTHONPATH ----
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # ...\tradingagents-ibkr-lab
TA_REPO = PROJECT_ROOT.parent / "TradingAgents"      # ...\TradingAgents

if TA_REPO.exists():
    sys.path.insert(0, str(TA_REPO))
else:
    raise RuntimeError(f"No encuentro el repo TradingAgents en {TA_REPO}")

# Ahora ya debería funcionar el import:
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
# ------------------------------------------------------


def main():
    symbol = "AAPL"
    today = dt_date.today().strftime("%Y-%m-%d")

    config = DEFAULT_CONFIG.copy()
    ta = TradingAgentsGraph(debug=False, config=config)

    print(f"Obteniendo decisión para {symbol} en {today}...")
    state, decision = ta.propagate(symbol, today)

    print("=== DECISIÓN TradingAgents ===")
    print(decision)
    print("================================")


if __name__ == "__main__":
    main()
