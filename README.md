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
```

Además, el repo asume que el código de TradingAgents está clonado en una carpeta hermana:

C:\Users\Usuario\Documents\GitHub\
  ├─ TradingAgents\
  └─ tradingagents-ibkr-lab\

test_ta_client.py y ta_client.py añaden dinámicamente esta ruta al PYTHONPATH para poder importar tradingagents.

--------------------------------------------------
## Requisitos
--------------------------------------------------

- Windows + PowerShell o CMD
- Python 3.x
- Cuenta de Interactive Brokers con acceso a:
  - TWS o IB Gateway en modo paper
  - API activada
- (Opcional, pero necesario para usar IA):
  - Cuenta en OpenAI Platform
  - Una OPENAI_API_KEY válida

--------------------------------------------------
## Instalación
--------------------------------------------------

1) Clonar este repositorio

    cd C:\Users\Usuario\Documents\GitHub
    git clone https://github.com/d4vidd14/tradingagents-ibkr-lab.git
    cd tradingagents-ibkr-lab

2) Clonar TradingAgents al lado

    cd C:\Users\Usuario\Documents\GitHub
    git clone https://github.com/d4vidd14/TradingAgents.git

Quedará así:

GitHub/
  ├─ TradingAgents/
  └─ tradingagents-ibkr-lab/

3) Crear y activar entorno virtual

En PowerShell:

    cd C:\Users\Usuario\Documents\GitHub\tradingagents-ibkr-lab
    py -3 -m venv venv
    .\venv\Scripts\Activate.ps1

(En CMD sería: venv\Scripts\activate.bat)

4) Instalar dependencias

    pip install --upgrade pip
    pip install -r requirements.txt

--------------------------------------------------
## Configuración
--------------------------------------------------

### 1. IBKR (Trader Workstation / IB Gateway)

1. Abrir TWS o IB Gateway en modo paper.
2. Ir a: File → Global Configuration... → API → Settings.
3. Marcar:
   - Enable ActiveX and Socket Clients
   - Permitir conexiones desde 127.0.0.1 (localhost)
   - Desmarcar Read-Only API (para poder enviar órdenes más adelante).
4. Confirmar que el puerto de socket es 7497 para paper (ajustar si es necesario).

### 2. Variables de entorno (.env)

Crear un archivo .env en la raíz del proyecto (tradingagents-ibkr-lab/.env) para no hardcodear credenciales:

    OPENAI_API_KEY=tu_clave_aqui

    IBKR_HOST=127.0.0.1
    IBKR_PORT=7497
    IBKR_CLIENT_ID=1

Nota: .env está incluido en .gitignore, así que no se sube a GitHub.

--------------------------------------------------
## Scripts principales
--------------------------------------------------

### 1. Test de conexión a IBKR

Con el venv activado:

    python src\test_ibkr_connection.py

Este script:
- Conecta a IBKR paper usando ib_insync
- Lista las posiciones actuales en la cuenta
- Se desconecta

Sirve para comprobar que la API de IBKR está accesible desde Python.

--------------------------------------------------

### 2. Test de TradingAgents (decisión de IA)

    python src\test_ta_client.py

Este script:
- Añade el repo TradingAgents al PYTHONPATH
- Crea un TradingAgentsGraph con DEFAULT_CONFIG
- Pide una decisión para un símbolo (ej. AAPL) y la fecha actual
- Imprime el diccionario decision con campos como:
  - action  ("BUY" | "SELL" | "HOLD")
  - confidence
  - risk_level
  - reasoning (según la versión)

Requiere tener OPENAI_API_KEY configurada.

--------------------------------------------------

### 3. Orquestador (TA + IBKR, de momento en modo simulación)

    python src\orchestrator.py

El orquestador hace:

1. Conecta a IBKR paper.
2. Obtiene una decisión de TradingAgents para un símbolo (AAPL) y la fecha actual.
3. Consulta la posición actual en la cuenta (get_position).
4. Simula qué orden se enviaría:
   - [SIMULACIÓN] Enviaría BUY de X acciones...
   - [SIMULACIÓN] HOLD → no haría nada
   - etc.
5. Se desconecta.

Por ahora, no envía órdenes reales: sólo imprime lo que haría.  
El siguiente paso será descomentar o añadir las llamadas a ib_client.send_market_order(...) para empezar a operar en paper.

--------------------------------------------------
## Roadmap / Próximos pasos
--------------------------------------------------

- Añadir mapping robusto de decision → tamaño de posición (gestión de riesgo)
- Activar ejecución real en paper desde orchestrator.py (en lugar de solo imprimir)
- Registrar todas las decisiones y operaciones en CSV/SQLite para análisis posterior
- Crear notebooks en notebooks/ para:
  - equity curve
  - drawdown
  - comparación con benchmarks
- Afinar DEFAULT_CONFIG de TradingAgents para usar modelos más baratos y limitar llamadas
- (Opcional) Probar backends LLM alternativos (OpenAI-compatible, modelos locales, etc.)

--------------------------------------------------
## Aviso importante
--------------------------------------------------

Este proyecto es:

- Un laboratorio personal de trading algorítmico con IA
- No es una recomendación de inversión ni un sistema listo para producción
- Se ejecuta inicialmente solo en cuentas paper / demo

El código está pensado únicamente para fines educativos y experimentales.  
Cualquier uso en cuentas reales es responsabilidad exclusiva del usuario.
