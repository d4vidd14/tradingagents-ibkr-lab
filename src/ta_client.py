"""
ta_client.py

Wrapper sencillo para interactuar con TradingAgents.
"""

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG


class TradingAgentsClient:
    def __init__(self, config=None, debug=False):
        if config is None:
            config = DEFAULT_CONFIG.copy()
        self.ta = TradingAgentsGraph(debug=debug, config=config)

    def get_decision(self, symbol: str, date_str: str) -> dict:
        """
        Llama a TradingAgents y devuelve solo el dict de decisión.
        """
        state, decision = self.ta.propagate(symbol, date_str)
        return decision
