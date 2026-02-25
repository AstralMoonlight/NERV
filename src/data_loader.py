import yfinance as yf
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_data(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """
    Descarga 1 año de datos diarios (velas OHLCV) para un ticker dado usando yfinance.
    """
    logging.info(f"Descargando datos históricos para {ticker}...")
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        
        if df.empty:
            logging.warning(f"No se encontraron datos para {ticker}.")
            return pd.DataFrame()
            
        # Asegurarnos de que el índice sea Datetime y capitalizar columnas para pandas_ta si es necesario, 
        # pero yfinance ya devuelve Open, High, Low, Close, Volume.
        df.index = pd.to_datetime(df.index)
        
        # Opcionalmente, podemos quitar el timezone para evitar problemas con pandas_ta
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
            
        return df

    except Exception as e:
        logging.error(f"Error descargando datos para {ticker}: {e}")
        return pd.DataFrame()
