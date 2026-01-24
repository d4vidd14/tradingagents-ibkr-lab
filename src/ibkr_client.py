"""
ibkr_client.py

Wrapper sencillo sobre ib_insync para conectar con IBKR paper
y enviar órdenes básicas.
"""

from ib_insync import IB, Stock, MarketOrder


class IBKRClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 1):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = IB()

    def connect(self):
        print(f"Conectando a IBKR en {self.host}:{self.port} (clientId={self.client_id})...")
        self.ib.connect(self.host, self.port, clientId=self.client_id)
        print("Conectado.")

    def disconnect(self):
        self.ib.disconnect()
        print("Desconectado de IBKR.")

    def get_stock_contract(self, symbol: str, exchange: str = "SMART", currency: str = "USD") -> Stock:
        contract = Stock(symbol, exchange, currency)
        self.ib.qualifyContracts(contract)
        return contract

    def get_position(self, symbol: str) -> int:
        """
        Devuelve cuántas acciones del símbolo tienes en la cuenta.
        """
        positions = self.ib.positions()
        for p in positions:
            if p.contract.symbol == symbol and p.contract.secType == "STK":
                return p.position
        return 0

    def send_market_order(self, symbol: str, action: str, quantity: int):
        """
        Envía una orden de mercado simple BUY/SELL para acciones.
        """
        contract = self.get_stock_contract(symbol)
        order = MarketOrder(action, quantity)
        trade = self.ib.placeOrder(contract, order)
        return trade
