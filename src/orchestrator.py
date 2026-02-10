"""
orchestrator.py

Gestor de cartera swing con:
- 1% de riesgo por trade.
- 15% de riesgo total máximo (con 5 trades estamos por debajo).
- Máximo 5 operaciones abiertas.
- No invertir en acciones con market cap < 2B.
- Máximo 8% de la cartera por acción.
- Stops y tamaño ajustados según volatilidad y tipo de setup:
    * Breakout de máximos -> stop algo más ceñido -> más tamaño.
    * Cambio de tendencia / pullback -> stop base.
"""

from datetime import date as dt_date
import sys
from pathlib import Path
from math import floor
from typing import Tuple, Optional

import yfinance as yf  # asegúrate de tenerlo en el venv: pip install yfinance

# --- Añadir raíz del proyecto al sys.path ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
# --------------------------------------------

from src.ta_client import TradingAgentsClient
from src.ibkr_client import IBKRClient


# Parámetros de cartera swing
RISK_PER_TRADE = 0.01        # 1% del equity por operación
MAX_TOTAL_RISK = 0.15        # 15% de riesgo total máximo (de momento sobre papel)
MAX_OPEN_TRADES = 5          # máximo 5 trades abiertos
MAX_POSITION_EXPOSURE = 0.08 # máximo 8% de la cartera en una acción
MIN_MARKET_CAP = 2_000_000_000  # 2B

EXECUTE_ORDERS = True        # True = manda órdenes en paper, False = solo simula

SYMBOLS = [
    # Big Tech / growth grandes
    "AMZN",   # Amazon

    # Financiero / energía / defensivas
    "JPM",    # JP Morgan
    "XOM",    # Exxon Mobil
    "JNJ",    # Johnson & Johnson
    "PG",     # Procter & Gamble

    # ETFs grandes (sirven bien para swing)
    "SPY",    # S&P 500
    "QQQ",    # Nasdaq 100
    "IWM",    # Russell 2000
]



# ---------- Helpers de datos (market cap, volatilidad, setup) ----------

def get_market_cap_and_history(symbol: str) -> Tuple[Optional[float], Optional["yf.pandas.DataFrame"]]:
    """
    Devuelve (market_cap, histórico precios 6m) para un símbolo.
    market_cap en dólares (aprox).
    """
    ticker = yf.Ticker(symbol)
    try:
        info = getattr(ticker, "fast_info", None)
        mcap = None
        if info is not None and hasattr(info, "market_cap"):
            mcap = info.market_cap
        else:
            full_info = ticker.info
            mcap = full_info.get("marketCap")
    except Exception as e:
        print(f"[WARN] No se pudo obtener market cap de {symbol}: {e}")
        mcap = None

    try:
        hist = ticker.history(period="6mo", interval="1d")
        if hist is None or hist.empty:
            hist = None
    except Exception as e:
        print(f"[WARN] No se pudo obtener histórico de {symbol}: {e}")
        hist = None

    return mcap, hist


def compute_volatility(hist) -> Optional[float]:
    """
    Calcula una volatilidad anualizada aproximada a partir de retornos diarios.
    Devuelve un valor en tanto por uno (0.3 = 30% anual).
    """
    if hist is None or len(hist) < 20:
        return None
    try:
        returns = hist["Close"].pct_change().dropna()
        vol_annual = returns.std() * (252 ** 0.5)
        return float(vol_annual)
    except Exception as e:
        print(f"[WARN] Error calculando volatilidad: {e}")
        return None


def classify_setup(hist) -> str:
    """
    Clasifica el tipo de setup para el símbolo dado:
    - 'breakout': último cierre rompe máximos recientes.
    - 'trend_change': por encima de MA50 pero no rompe máximos.
    - 'other': resto.
    """
    if hist is None or len(hist) < 60:
        return "other"

    closes = hist["Close"]
    last_close = closes.iloc[-1]

    # Máximos últimos ~6 meses (o 252 sesiones si tuvieras)
    recent_max = closes.max()

    # Media móvil 50
    ma50 = closes.rolling(window=50).mean().iloc[-1]

    # Breakout: cierre más de 1% por encima del máximo anterior
    if last_close >= recent_max * 1.01:
        return "breakout"

    # Cambio de tendencia / pullback: por encima de MA50 pero sin romper máximos
    if last_close > ma50:
        return "trend_change"

    return "other"


def choose_stop_pct(vol_annual: Optional[float], setup: str) -> float:
    """
    Elige un porcentaje de stop (en tanto por uno) según volatilidad y tipo de setup.
    """
    # Base según volatilidad
    if vol_annual is None:
        base = 0.04  # 4% por defecto
    elif vol_annual < 0.25:
        base = 0.03  # baja vol
    elif vol_annual < 0.40:
        base = 0.045 # vol media
    else:
        base = 0.06  # vol alta

    # Ajuste según setup
    if setup == "breakout":
        stop_pct = base * 0.8   # más ceñido -> más tamaño
    elif setup == "trend_change":
        stop_pct = base         # base
    else:
        stop_pct = base * 1.2   # algo más holgado

    return stop_pct


# ------------------------ Orquestador principal ------------------------

def main():
    today = dt_date.today().strftime("%Y-%m-%d")
    print(f"=== ORCHESTRATOR SWING {today} ===")

    ta_client = TradingAgentsClient(debug=False)
    ib_client = IBKRClient()

    ib_client.connect()

    # 1) Equity y posiciones para tener visión global
    equity = ib_client.get_equity()
    positions = ib_client.get_all_positions()

    # Solo contamos como "trade swing" las posiciones en los símbolos que está gestionando el bot
    symbols_set = set(SYMBOLS)
    open_trades = [
        p for p in positions
        if p.get("qty", 0) != 0 and p.get("symbol") in symbols_set
    ]
    num_open_trades = len(open_trades)

    # A día de hoy, dimensionamos cada trade a 1%,
    # así que riesgo total ≈ nº_trades * 1% * equity
    risk_total = num_open_trades * (RISK_PER_TRADE * equity)

    print(f"Equity actual:           {equity:.2f}")
    print(f"Trades abiertos:         {num_open_trades}")
    print(f"Riesgo total aprox.:     {risk_total / equity * 100:.2f}%")
    print(f"Riesgo máximo permitido: {MAX_TOTAL_RISK * 100:.2f}%")
    print("========================================================")

    for symbol in SYMBOLS:
        print(f"\n--- Gestionando {symbol} ---")

        # 2) Señal de TradingAgents
        decision = ta_client.get_decision(symbol, today)
        action = decision.get("action", "HOLD")
        print(f"Señal TA para {symbol}: {action}")

        current_pos = ib_client.get_position(symbol)
        print(f"Posición actual en {symbol}: {current_pos} acciones")

        # 3) Salidas primero (SELL)
        if action == "SELL":
            if current_pos <= 0:
                print("No hay posición que cerrar en este símbolo.")
            else:
                print(f"TA indica SELL y tienes {current_pos} acciones: cierro swing.")
                if EXECUTE_ORDERS:
                    print(f"[EJECUTANDO] SELL {current_pos} {symbol}")
                    ib_client.send_market_order(symbol, "SELL", current_pos)
                    num_open_trades = max(0, num_open_trades - 1)
                else:
                    print(f"[SIMULACIÓN] SELL {current_pos} {symbol}")
            continue

        # 4) Entrada (BUY)
        if action == "BUY":
            # Swing: no piramidar, solo una posición por símbolo
            if current_pos > 0:
                print("Ya hay posición abierta en este símbolo, no abro otra (swing).")
                continue

            # Límite de nº de trades
            if num_open_trades >= MAX_OPEN_TRADES:
                print("Límite de trades abiertos alcanzado (5), no abro nueva posición.")
                continue

            # Límite de riesgo total (aunque con 5*1% no se llega al 15%)
            projected_risk_total = risk_total + (RISK_PER_TRADE * equity)
            if projected_risk_total > MAX_TOTAL_RISK * equity:
                print("Abrir este trade superaría el 15% de riesgo total, no entro.")
                continue

            # Datos fundamentales / técnicos: market cap, histórico, volatilidad, setup
            market_cap, hist = get_market_cap_and_history(symbol)
            if market_cap is None:
                print("No puedo obtener market cap, no opero este símbolo.")
                continue

            print(f"Market cap {symbol}: {market_cap / 1e9:.2f} B")

            if market_cap < MIN_MARKET_CAP:
                print("Market cap < 2B, descartado por criterio de cartera swing.")
                continue

            vol_annual = compute_volatility(hist)
            setup = classify_setup(hist)

            print(f"Volatilidad anual aprox: {vol_annual * 100:.1f}%"
                  if vol_annual is not None else "No se pudo estimar volatilidad.")
            print(f"Tipo de setup: {setup}")

            stop_pct = choose_stop_pct(vol_annual, setup)
            print(f"Stop porcentual estimado: {stop_pct * 100:.2f}%")

            # Precio actual aproximado (por si los datos de IB están limitados)
            last_price = ib_client.get_last_price_ibkr_only(symbol)

            if last_price is None or last_price <= 0:
                print("No tengo un precio válido para dimensionar, no opero.")
                continue

            # Riesgo y tamaño
            risk_amount = equity * RISK_PER_TRADE        # € de riesgo por trade
            risk_per_share = last_price * stop_pct       # € de riesgo por acción
            qty = floor(risk_amount / risk_per_share)    # nº acciones

            if qty <= 0:
                print("Qty calculada <= 0, no opero.")
                continue

            capital_pos = qty * last_price
            max_capital_for_symbol = equity * MAX_POSITION_EXPOSURE

            if capital_pos > max_capital_for_symbol:
                # Recortar tamaño para respetar el 8% de la cartera
                qty_cap_limit = floor(max_capital_for_symbol / last_price)
                print(f"Capital para posición ({capital_pos:.2f}) supera 8% cartera.")
                print(f"Ajusto qty de {qty} -> {qty_cap_limit} para respetar el 8%.")
                qty = qty_cap_limit

            if qty <= 0:
                print("Tras aplicar límite de exposición (8%), qty <= 0. No entro.")
                continue

            print(f"Precio {symbol}:                 {last_price:.2f}")
            print(f"Riesgo por trade (1%):          {risk_amount:.2f}")
            print(f"Riesgo por acción:              {risk_per_share:.2f}")
            print(f"Capital posición estimado:      {qty * last_price:.2f}")
            print(f"Cantidad final a comprar:       {qty} acciones")

            if EXECUTE_ORDERS:
                print(f"[EJECUTANDO] BUY {qty} {symbol}")
                ib_client.send_market_order(symbol, "BUY", qty)
                num_open_trades += 1
                risk_total += risk_amount
            else:
                print(f"[SIMULACIÓN] BUY {qty} {symbol}")

        else:
            # HOLD
            print("TA indica HOLD → mantengo, no abro ni cierro nada.")

    ib_client.disconnect()
    print("\n=== Fin de pasada diaria swing ===")


if __name__ == "__main__":
    main()
