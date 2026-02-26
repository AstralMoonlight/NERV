import yfinance as yf
import pandas as pd
import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import CONFIG

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_data(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """
    Carga datos históricos para un ticker. Implementa caché local incremental para evitar 
    descargas redundantes y bloqueos.
    """
    os.makedirs(CONFIG.CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CONFIG.CACHE_DIR, f"{ticker}.csv")
    
    df_local = pd.DataFrame()
    if os.path.exists(cache_path):
        try:
            df_local = pd.read_csv(cache_path, index_col=0, parse_dates=True)
            logging.info(f"Cargados datos locales para {ticker} ({len(df_local)} filas).")
        except Exception as e:
            logging.error(f"Error cargando cache para {ticker}: {e}")

    # Determinar rango de descarga
    last_date = None
    if not df_local.empty:
        last_date = df_local.index.max()
        start_date = (last_date + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        # Descarga inicial (2 años hacia atrás para calentamiento de SMA200)
        start_date = (pd.Timestamp.now() - pd.Timedelta(days=730)).strftime('%Y-%m-%d')

    today = pd.Timestamp.now().strftime('%Y-%m-%d')
    
    if (last_date and last_date.strftime('%Y-%m-%d') >= today) or (start_date >= today):
        logging.info(f"Datos de {ticker} ya están actualizados o no hay datos para descargar aún (es hoy).")
        return df_local

    logging.info(f"Descargando nuevos datos para {ticker} desde {start_date}...")
    try:
        # Usar yf.download y asegurar que no traiga MultiIndex si es posible, 
        # o aplanarlo manualmente.
        new_data = yf.download(ticker, start=start_date, interval=interval, progress=False)
        
        if new_data.empty:
            logging.info(f"No hay nuevos datos para {ticker}.")
            return df_local

        # Aplanar MultiIndex si existe (pasa en versiones nuevas de yfinance)
        if isinstance(new_data.columns, pd.MultiIndex):
            new_data.columns = new_data.columns.get_level_values(0)

        # Limpiar índice y timezone como antes
        new_data.index = pd.to_datetime(new_data.index)
        if new_data.index.tz is not None:
            new_data.index = new_data.index.tz_localize(None)

        # Combinar
        if df_local.empty:
            df_final = new_data
        else:
            df_final = pd.concat([df_local, new_data])
            # Eliminar duplicados por índice por si acaso solapan
            df_final = df_final[~df_final.index.duplicated(keep='last')]
            df_final.sort_index(inplace=True)

        # Guardar en cache
        df_final.to_csv(cache_path)
        logging.info(f"Cache actualizado para {ticker}. Total filas: {len(df_final)}")
        return df_final

    except Exception as e:
        logging.error(f"Error descargando datos para {ticker}: {e}")
        return df_local
