"""
ibkr_client.py

Wrapper sencillo alrededor de ib_insync para trabajar con IBKR (TWS / Gateway)
en modo paper.

Funciones principales:
- Conectar / desconectar.
- Leer equity de la cuenta.
- Leer posiciones (todas o de un símbolo).
- Obtener último precio de un símbolo.
- Enviar órdenes de mercado.
"""

import os
from typing import List, Dict, Optional

from dotenv import load_dotenv
from ib_insync import IB, Stock, MarketOrder


load_dotenv()


class IBKRClient:
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        client_id: Optional[int] = None,
    ) -> None:
        # Config por defecto (puedes cambiarlos en .env)
        self.host = host or os.getenv("IBKR_HOST", "127.0.0.1")
        self.port = int(port or os.getenv("IBKR_PORT", "7497"))
        self.client_id = int(client_id or os.getenv("IBKR_CLIENT_ID", "1"))

        self.ib = IB()

    # ------------------------
    # Conexión
    # ------------------------
    def connect(self) -> None:
        if self.ib.isConnected():
            return
        print(f"Conectando a IBKR en {self.host}:{self.port} (clientId={self.client_id})...")
        self.ib.connect(self.host, self.port, clientId=self.client_id)
        if self.ib.isConnected():
            print("Conectado.")
        else:
            raise RuntimeError("No se ha podido conectar a IBKR.")

    def disconnect(self) -> None:
        if self.ib.isConnected():
            self.ib.disconnect()
            print("Desconectado de IBKR.")

    # ------------------------
    # Info de cuenta / equity
    # ------------------------
    def get_equity(self) -> float:
        """
        Devuelve el NetLiquidation (equity) de la cuenta como float.
        Si hay varias cuentas/divisas, coge la primera que encuentre.
        """
        if not self.ib.isConnected():
            raise RuntimeError("IBKR no está conectado.")

        summary = self.ib.accountSummary()  # lista de AccountValue
        equity = None

        # Buscamos NetLiquidation en moneda base o principal
        for item in summary:
            if item.tag == "NetLiquidation":
                # item.value es str
                try:
                    equity = float(item.value)
                    # Priorizamos la primera que encontremos
                    break
                except ValueError:
                    continue

        if equity is None:
            raise RuntimeError("No se ha podido obtener NetLiquidation de la cuenta.")

        return equity

    # ------------------------
    # Posiciones
    # ------------------------
    def get_all_positions(self) -> List[Dict]:
        """
        Devuelve una lista de dicts con las posiciones abiertas.
        Cada dict tiene: symbol, qty, avg_cost, account.
        """
        if not self.ib.isConnected():
            raise RuntimeError("IBKR no está conectado.")

        positions = self.ib.positions()
        result = []
        for p in positions:
            try:
                symbol = p.contract.symbol
                qty = float(p.position)
                avg_cost = float(p.avgCost)
                account = p.account
                result.append(
                    {
                        "symbol": symbol,
                        "qty": qty,
                        "avg_cost": avg_cost,
                        "account": account,
                    }
                )
            except Exception as e:
                print(f"[WARN] Error parseando posición {p}: {e}")

        return result

    def get_position(self, symbol: str) -> int:
        """
        Devuelve la cantidad (nº de acciones) del símbolo dado.
        Si no hay posición, devuelve 0.
        """
        if not self.ib.isConnected():
            raise RuntimeError("IBKR no está conectado.")

        positions = self.ib.positions()
        total_qty = 0
        for p in positions:
            if p.contract.symbol.upper() == symbol.upper():
                total_qty += int(p.position)

        return total_qty

    # ------------------------
    # Datos de mercado
    # ------------------------
    def _make_stock_contract(self, symbol: str):
        """
        Crea un contrato de acción USA estándar (SMART / USD).
        Ajusta esto si quieres operar otros mercados.
        """
        from ib_insync import Stock

        return Stock(symbol, "SMART", "USD")

    def get_last_price(self, symbol: str) -> Optional[float]:
        """
        Devuelve un precio razonable para dimensionar la posición.
        Intenta usar market data; si no hay, devuelve None.

        OJO: si no tienes datos en tiempo real habilitados en IBKR,
        puede que solo tengas el 'close' del día anterior.
        """
        if not self.ib.isConnected():
            raise RuntimeError("IBKR no está conectado.")

        contract = self._make_stock_contract(symbol)
        ticker = self.ib.reqMktData(contract, "", False, False)
        # Espera un poco a que llegue el dato
        self.ib.sleep(2.0)

        price_candidates = [
            ticker.last,
            ticker.close,
            ticker.marketPrice(),
        ]

        price_candidates = [p for p in price_candidates if p is not None and p > 0]

        if not price_candidates:
            print(f"[WARN] No he podido obtener precio para {symbol}.")
            return None

        return float(price_candidates[0])
    
    def get_last_price_ibkr_only(self, symbol: str) -> float | None:
        """
        Devuelve un precio usando SOLO datos de mercado de IBKR.
        Si no hay suscripción / datos, devuelve None.

        Úsalo cuando quieras comportamiento tipo 'real':
        no tomar decisiones si el broker no da precio.
        """
        if not self.ib.isConnected():
            raise RuntimeError("IBKR no está conectado.")

        try:
            contract = self._make_stock_contract(symbol)
            ticker = self.ib.reqMktData(contract, "", False, False)
            self.ib.sleep(2.0)

            candidates = [
                ticker.last,
                ticker.close,
                ticker.marketPrice(),
            ]
            candidates = [p for p in candidates if p is not None and p > 0]

            if not candidates:
                print(f"[WARN] IBKR no ha dado precio válido para {symbol}.")
                return None

            return float(candidates[0])
        except Exception as e:
            print(f"[WARN] Error obteniendo precio IBKR para {symbol}: {e}")
            return None


    # ------------------------
    # Órdenes
    # ------------------------
    def send_market_order(self, symbol: str, side: str, quantity: int):
        """
        Envía una orden de mercado BUY/SELL para 'quantity' acciones del símbolo dado.
        """
        if not self.ib.isConnected():
            raise RuntimeError("IBKR no está conectado.")

        if quantity <= 0:
            print("[INFO] Cantidad <= 0, no envío orden.")
            return

        side = side.upper()
        if side not in ("BUY", "SELL"):
            raise ValueError("side debe ser 'BUY' o 'SELL'.")

        contract = self._make_stock_contract(symbol)
        order = MarketOrder(side, quantity)

        print(f"Enviando orden {side} {quantity}x {symbol} (Market)...")
        trade = self.ib.placeOrder(contract, order)

        # Esperamos un poco a que se procese
        self.ib.sleep(1.0)

        print(f"Orden enviada. Estado actual: {trade.orderStatus.status}")
        return trade
