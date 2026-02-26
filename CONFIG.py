# Proyecto NERV Configuration

# Lista de tickers a analizar (Optimizada para NERV 2.0)
TICKERS = [
    "AAPL", "ABBV", "ABNB", "AMAT", "AMD", "AMGN", "AMZN", "APP", "ARKK", "ARM",
    "AVGO", "AXP", "BABA", "BAC", "BCH", "BIDU", "BRK-B", "BSAC", "CAT", "CCU",
    "CEG", "COP", "COST", "CPER", "CRM", "CRWD", "CVX", "DE", "DIA", "DLO",
    "ENIC", "FTNT", "GE", "GILD", "GLD", "GOOGL", "GRAB", "GS", "HD", "IBIT",
    "ISRG", "IWM", "JNJ", "JPM", "KO", "LIT", "LLY", "LMT", "LOW", "LTM",
    "LULU", "MA", "MCD", "MELI", "META", "MRK", "MS", "MSFT", "MU", "NEE",
    "NFLX", "NOW", "NU", "NVDA", "NVO", "ORCL", "PANW", "PEP", "PG", "PLTR",
    "QCOM", "QQQ", "RTX", "SBUX", "SE", "SHEL", "SHOP", "SLV", "SMH", "SNOW",
    "SPOT", "SPY", "SQM", "STNE", "TGT", "TLT", "TMO", "TSLA", "TSM", "TXN",
    "UBER", "UNH", "URA", "USO", "V", "VRT", "VRTX", "VTI", "WFC", "WMT", "XOM"
]

# Configuración del Motor de Backtest
BACKTEST_CAPITAL_INICIAL = 1000.0
BACKTEST_TAMANO_POSICION_PCT = 0.5

# Parámetros para el RSI
RSI_PARAMS = {
    "period": 14,
    "alcista_compra_1": 35,
    "alcista_compra_2": 30,
    "alcista_compra_step": 3,
    "alcista_venta": 73,
    "alcista_pullback_compra": 50,
    "bajista_compra_cruce": 30,
    "bajista_venta": 70,
}

# Restricciones
RENTABILIDAD_MINIMA_VENTA_PCT = 0.30

# Parámetros para las Medias Móviles Simples (SMA)
SMA_PERIODS = {
    "short": 10,
    "medium": 50,
    "long": 200
}

# Ruta donde se guardará el informe final
REPORT_PATH = "./data/informe_nerv_backtest.md"

# Directorio para cachear datos históricos
CACHE_DIR = "./data/cache"

# Ruta para el reporte de señales diarias
SIGNAL_REPORT_PATH = "./data/senales_nerv_hoy.md"

# Log histórico de señales en formato JSON (para integración web)
SIGNALS_JSON_LOG = "./data/nerv_signals_log.json"