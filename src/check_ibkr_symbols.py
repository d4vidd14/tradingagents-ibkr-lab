"""
check_ibkr_symbols.py

Comprueba qué símbolos tienen datos de mercado disponibles vía IBKR.
Úsalo para decidir qué SYMBOLS puede gestionar el bot.
"""

import sys
from pathlib import Path

# Añadimos la raíz del proyecto al sys.path para que 'src' se pueda importar
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ibkr_client import IBKRClient

CANDIDATE_SYMBOLS = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "META",
    "NVDA",
    "JPM",
    "XOM",
    "JNJ",
    "PG",
    "SPY",
    "QQQ",
    "IWM",
]

def main():
    ib = IBKRClient()
    ib.connect()

    ok_symbols = []
    bad_symbols = []

    for sym in CANDIDATE_SYMBOLS:
        print(f"\nProbando {sym}...")
        price = ib.get_last_price(sym)
        if price is not None:
            print(f"  ✅ IBKR da precio: {price:.2f}")
            ok_symbols.append(sym)
        else:
            print("  ❌ Sin datos IBKR (no usar este símbolo en el bot).")
            bad_symbols.append(sym)

    ib.disconnect()

    print("\n=== RESUMEN ===")
    print("Símbolos APTOS para el bot (tienen datos IBKR):")
    for s in ok_symbols:
        print("  -", s)

    print("\nSímbolos SIN datos IBKR (mejor no usarlos):")
    for s in bad_symbols:
        print("  -", s)

if __name__ == "__main__":
    main()
