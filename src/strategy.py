import pandas as pd
import sys
import os
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import CONFIG

def apply_strategy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica la lógica de la estrategia y crea una columna 'Signal' con valores (Buy, Sell, Hold).
    - Buy: RSI cruza sobre mid_level Y el precio (Close) > SMA50.
    - Sell: RSI cruza bajo mid_level.
    """
    if df.empty or 'RSI' not in df.columns or 'SMA_50' not in df.columns or 'Close' not in df.columns:
        return df

    mid_level = CONFIG.RSI_PARAMS['mid_level']

    # Inicializamos todas las señales en Hold
    df['Signal'] = 'Hold'

    # Condiciones de cruce
    # RSI cruza hacia arriba el mid_level: RSI actual > mid y RSI anterior <= mid
    rsi_cross_up = (df['RSI'] > mid_level) & (df['RSI'].shift(1) <= mid_level)
    
    # RSI cruza hacia abajo el mid_level: RSI actual < mid y RSI anterior >= mid
    rsi_cross_down = (df['RSI'] < mid_level) & (df['RSI'].shift(1) >= mid_level)

    # Condición de Precio sobre SMA_50
    price_above_sma50 = df['Close'] > df['SMA_50']

    # Asignamos señales
    buy_condition = rsi_cross_up & price_above_sma50
    sell_condition = rsi_cross_down

    # Numpy where para aplicar condiciones de forma vectorizada (Aunque iterar es posible, np.where es más rápido)
    df.loc[buy_condition, 'Signal'] = 'Buy'
    df.loc[sell_condition, 'Signal'] = 'Sell'

    return df
