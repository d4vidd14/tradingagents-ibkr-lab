from datetime import date as dt_date

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG


def main():
    # Config base (luego se puede tunear para que gaste menos tokens)
    config = DEFAULT_CONFIG.copy()

    ta = TradingAgentsGraph(debug=True, config=config)

    symbol = "AAPL"
    today = dt_date.today().strftime("%Y-%m-%d")

    print(f"Obteniendo decisión para {symbol} en {today}...")
    state, decision = ta.propagate(symbol, today)

    print("=== DECISIÓN RAW ===")
    print(decision)
    print("====================")


if __name__ == "__main__":
    main()
