# TradingAgents + IBKR Lab

Proyecto personal para experimentar con la integración de:

- [TradingAgents](https://github.com/TauricResearch/TradingAgents) como **motor de decisiones (IA multi-agente)**  
- [Interactive Brokers (IBKR)](https://www.interactivebrokers.com/) en modo **paper trading** como **bróker de ejecución**  
- [`ib_insync`](https://github.com/erdewit/ib_insync) como **cliente Python** para hablar con TWS/IB Gateway  

👉 Objetivo: construir un pequeño **orquestador** que pida una señal de compra/venta a TradingAgents y la traduzca en órdenes hacia una cuenta *paper* de IBKR, primero en modo simulación y luego con ejecución real.

---

## Estado actual del proyecto

- ✅ Repo estructurado en modo “laboratorio” (`lab`)  
- ✅ Entorno virtual configurado  
- ✅ Conexión a IBKR paper a través de `ib_insync`  
- ✅ Integración de código fuente de TradingAgents dentro del proyecto  
- 🔄 Pendiente: configurar `OPENAI_API_KEY` para usar LLMs de OpenAI  
- 🔜 Siguiente paso: usar la decisión de TradingAgents en `orchestrator.py` para mandar órdenes reales (en paper)

---

## Arquitectura

Estructura básica del repo:

```text
tradingagents-ibkr-lab/
├─ README.md
├─ requirements.txt
├─ .gitignore
├─ .env                 # (no se sube a git) API keys y configuración sensible
├─ config/
│  └─ config_example.yml
├─ src/
│  ├─ __init__.py
│  ├─ ibkr_client.py        # Wrapper sencillo para IBKR (conexión, posiciones, órdenes)
│  ├─ ta_client.py          # Wrapper para TradingAgents
│  ├─ orchestrator.py       # Une TA + IBKR (cerebro + manos)
│  ├─ test_ibkr_connection.py  # Test de conexión a IBKR paper
│  └─ test_ta_client.py        # Test de decisión de TradingAgents
└─ notebooks/
   └─ (futuro: análisis de resultados, backtests, etc.)
