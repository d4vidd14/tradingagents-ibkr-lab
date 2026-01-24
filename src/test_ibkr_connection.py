from src.ibkr_client import IBKRClient


def main():
    ib_client = IBKRClient()
    ib_client.connect()

    print("Conexión correcta. Posiciones actuales en la cuenta:")
    positions = ib_client.ib.positions()
    for p in positions:
        print(p)

    ib_client.disconnect()


if __name__ == "__main__":
    main()
