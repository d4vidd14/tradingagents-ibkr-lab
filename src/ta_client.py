"""
ta_client.py

Wrapper sencillo para interactuar con TradingAgents.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

# Cargar variables desde .env (OPENAI_API_KEY, etc.)
load_dotenv()

# --- Añadir repo TradingAgents al PYTHONPATH ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
TA_REPO = PROJECT_ROOT.parent / "TradingAgents"

if TA_REPO.exists():
    sys.path.insert(0, str(TA_REPO))
else:
    raise RuntimeError(f"No encuentro el repo TradingAgents en {TA_REPO}")
# ------------------------------------------------

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG


class TradingAgentsClient:
    def __init__(self, config=None, debug=False):
        if config is None:
            config = DEFAULT_CONFIG.copy()
        self.ta = TradingAgentsGraph(debug=debug, config=config)

    def get_decision(self, symbol: str, date_str: str) -> dict:
        """
        Llama a TradingAgents y devuelve SIEMPRE un dict con al menos 'action'.
        """
        state, raw_decision = self.ta.propagate(symbol, date_str)

        # Normalizar el tipo de decisión
        if isinstance(raw_decision, dict):
            decision = raw_decision
        elif isinstance(raw_decision, str):
            # Si devuelve solo "BUY"/"SELL"/"HOLD", lo envolvemos
            decision = {"action": raw_decision}
        else:
            # Caso raro: no sé qué ha devuelto, forzamos HOLD
            decision = {"action": "HOLD"}

        # Debug opcional:
        print(">>> RAW_DECISION TradingAgents:", raw_decision)
        print(">>> DECISION normalizada:", decision)

        return decision
