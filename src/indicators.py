import pandas as pd
import pandas_ta as ta
import sys
import os

# Agregamos el directorio raíz para poder importar CONFIG sin problemas
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import CONFIG

def apply_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega los indicadores RSI, RSI-MA, SMA10, SMA50 y SMA200 al dataframe.
    Asume que el DataFrame ya contiene Volume, Close, Open, High, Low.
    """
    if df.empty or len(df) < CONFIG.SMA_PERIODS['long']:
        # Consideramos si hay pocos datos. Idealmente deberíamos poder retornar igual.
        # Pero es bueno tener cuidado si hay < 200 filas.
        pass

    try:
        # RSI
        rsi_period = CONFIG.RSI_PARAMS['period']
        df['RSI'] = ta.rsi(df['Close'], length=rsi_period)

        # RSI-MA
        rsi_ma_period = CONFIG.RSI_PARAMS['ma_period']
        # Calculamos la media móvil simple del RSI calculado anteriormente
        if 'RSI' in df.columns and df['RSI'].notna().sum() > rsi_ma_period:
             df['RSI_MA'] = ta.sma(df['RSI'], length=rsi_ma_period)
        else:
             df['RSI_MA'] = None

        # SMAs
        df['SMA_10'] = ta.sma(df['Close'], length=CONFIG.SMA_PERIODS['short'])
        df['SMA_50'] = ta.sma(df['Close'], length=CONFIG.SMA_PERIODS['medium'])
        df['SMA_200'] = ta.sma(df['Close'], length=CONFIG.SMA_PERIODS['long'])
        
        # Opcional (Limpieza básica), removemos eventuales filas extras si no nos importan mucho los NaNs muy antiguos, 
        # pero es mejor dejarlos para que la serie de tiempo esté completa y el usuario vea cómo fue la evolución.
        
    except Exception as e:
         print(f"Error applying indicators: {e}")

    return df
