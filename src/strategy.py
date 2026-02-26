import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import CONFIG

def run_backtest(df: pd.DataFrame, ticker: str) -> dict:
    """
    Simula la estrategia de inversión día por día calculando compras, ventas, retornos y el estado final.
    """
    if df.empty or 'RSI' not in df.columns or 'SMA_200' not in df.columns or 'Close' not in df.columns:
        return {}

    # Estado de la cuenta
    capital = CONFIG.BACKTEST_CAPITAL_INICIAL
    shares = 0.0
    total_trades = 0
    history = []
    position_cost = 0.0  # Rastrear costo acumulado de la posición abierta actual
    
    # Trackers de estado para la lógica
    last_action = 'HOLD' # Puede ser BUY, SELL, HOLD
    last_buy_rsi = None  # Para rastrear los escaladores en tendencia alcista
    
    # Iniciar simulación
    for i in range(1, len(df)):
        current_row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        date_str = current_row.name.strftime('%Y-%m-%d')
        
        # Extraer valores asegurando que sean escalares (manejo de posibles Series remanentes)
        try:
            price = float(current_row['Close'])
            rsi = float(current_row['RSI'])
            prev_rsi = float(prev_row['RSI'])
            sma50 = float(current_row['SMA_50'])
            sma200 = float(current_row['SMA_200'])
        except (TypeError, ValueError):
            # Si aún así falla por ser Series (MultiIndex no aplanado), extraemos el primer item
            price = current_row['Close'].iloc[0] if isinstance(current_row['Close'], pd.Series) else current_row['Close']
            rsi = current_row['RSI'].iloc[0] if isinstance(current_row['RSI'], pd.Series) else current_row['RSI']
            prev_rsi = prev_row['RSI'].iloc[0] if isinstance(prev_row['RSI'], pd.Series) else prev_row['RSI']
            sma50 = current_row['SMA_50'].iloc[0] if isinstance(current_row['SMA_50'], pd.Series) else current_row['SMA_50']
            sma200 = current_row['SMA_200'].iloc[0] if isinstance(current_row['SMA_200'], pd.Series) else current_row['SMA_200']
        
        # Ignorar si hay nulos iniciales de las medias (los primeros 200 días)
        if pd.isna(rsi) or pd.isna(sma50) or pd.isna(sma200):
            continue
            
        tendencia_alcista = sma50 > sma200
        
        # Calcular porcentaje de utilidad latente sobre el COSTO BASE de la posición actual
        utilidad_latente_pct = 0.0
        if shares > 0 and position_cost > 0:
            utilidad_latente_pct = (shares * price - position_cost) / position_cost
        
        signal = 'HOLD'
        reason = ""
        
        # LÓGICA DE COMPRA Y VENTA SEGÚN TENDENCIA
        if tendencia_alcista:
            # VENTA ALCISTA
            if rsi >= CONFIG.RSI_PARAMS['alcista_venta'] and shares > 0:
                if utilidad_latente_pct >= CONFIG.RENTABILIDAD_MINIMA_VENTA_PCT:
                    signal = 'SELL'
                    reason = f"Venta Tendencia Alcista: RSI {rsi:.2f} >= {CONFIG.RSI_PARAMS['alcista_venta']} con utilidad {utilidad_latente_pct*100:.2f}%"
                else:
                    pass
                
            # COMPRA ALCISTA
            elif rsi <= CONFIG.RSI_PARAMS['alcista_compra_1']:
                comprar = False
                if last_buy_rsi is None:
                    comprar = True
                    reason = f"Compra Tendencia Alcista: RSI {rsi:.2f} <= {CONFIG.RSI_PARAMS['alcista_compra_1']} (Nivel 1)"
                elif last_buy_rsi >= CONFIG.RSI_PARAMS['alcista_compra_1'] and rsi <= CONFIG.RSI_PARAMS['alcista_compra_2']:
                    # Nivel 2: Solo si sigue por encima de la SMA200
                    if price > sma200:
                        comprar = True
                        reason = f"Compra Tendencia Alcista: RSI {rsi:.2f} <= {CONFIG.RSI_PARAMS['alcista_compra_2']} (Nivel 2)"
                    else:
                        pass
                elif last_buy_rsi <= CONFIG.RSI_PARAMS['alcista_compra_2']:
                    # Nivel 3: Solo si sigue por encima de la SMA200
                    if rsi <= (last_buy_rsi - CONFIG.RSI_PARAMS['alcista_compra_step']):
                        if price > sma200:
                            comprar = True
                            reason = f"Compra Tendencia Alcista: RSI {rsi:.2f} bajó {CONFIG.RSI_PARAMS['alcista_compra_step']} puntos desde {last_buy_rsi:.2f}"
                        else:
                            pass

                if comprar:
                    signal = 'BUY'
                    last_buy_rsi = rsi
                    
            # COMPRA PULLBACK ALCISTA
            elif rsi < CONFIG.RSI_PARAMS['alcista_pullback_compra'] and last_action == 'SELL':
                 signal = 'BUY'
                 reason = f"Pullback Tendencia Alcista: RSI {rsi:.2f} < {CONFIG.RSI_PARAMS['alcista_pullback_compra']} tras venta"
                 last_buy_rsi = rsi
                 
        else:
            # TENDENCIA BAJISTA
            # VENTA BAJISTA
            if rsi >= CONFIG.RSI_PARAMS['bajista_venta'] and shares > 0:
                if utilidad_latente_pct >= CONFIG.RENTABILIDAD_MINIMA_VENTA_PCT:
                    signal = 'SELL'
                    reason = f"Venta Tendencia Bajista: RSI {rsi:.2f} >= {CONFIG.RSI_PARAMS['bajista_venta']} con utilidad {utilidad_latente_pct*100:.2f}%"
                
            # COMPRA BAJISTA (Solo una vez si no hay posición)
            elif shares == 0 and prev_rsi <= 35 and rsi > 35:
                signal = 'BUY'
                reason = f"Compra Tendencia Bajista: Cruce RSI {rsi:.2f} > 35"
                
        # EJECUCIÓN DE ÓRDENES
        if signal == 'BUY' and capital > 0:
            monto_inversion = CONFIG.BACKTEST_CAPITAL_INICIAL * CONFIG.BACKTEST_TAMANO_POSICION_PCT
            if monto_inversion > capital:
                monto_inversion = capital
                
            shares_compradas = monto_inversion / price
            shares += shares_compradas
            capital -= monto_inversion
            position_cost += monto_inversion # Incrementar el costo base de la posición
            last_action = 'BUY'
            history.append({
                'date': date_str,
                'action': 'Compra',
                'amount': monto_inversion,
                'price': price,
                'reason': reason
            })
            
        elif signal == 'SELL' and shares > 0:
            monto_venta = shares * price
            capital += monto_venta
            shares = 0.0
            position_cost = 0.0 # Resetear costo base al cerrar la posición
            last_action = 'SELL'
            last_buy_rsi = None
            total_trades += 1
            history.append({
                'date': date_str,
                'action': 'Venta',
                'amount': monto_venta,
                'price': price,
                'reason': reason
            })
            
    # Cierre del loop - Resumen Final
    last_price = float(df.iloc[-1]['Close'])
    pos_value_final = shares * last_price
    valor_final_cartera = capital + pos_value_final
    rendimiento_pct = ((valor_final_cartera - CONFIG.BACKTEST_CAPITAL_INICIAL) / CONFIG.BACKTEST_CAPITAL_INICIAL) * 100
    
    estado_final = "En posición (Holdeando utilidad)" if shares > 0 else "Liquidez (Sin posición)"

    return {
        'Ticker': ticker,
        'Operaciones Creadas': total_trades,
        'Capital Final': valor_final_cartera,
        'Capital en Posición': pos_value_final,
        'Rendimiento (%)': rendimiento_pct,
        'Estado': estado_final,
        'History': history
    }
