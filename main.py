import os
import datetime
import logging
from typing import List, Dict
import pandas as pd

import CONFIG
from src.data_loader import load_data
from src.indicators import apply_indicators
from src.strategy import apply_strategy

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_markdown_report(results: List[Dict], report_path: str):
    """Generates a Markdown report with a summary table."""
    try:
        # Check if directory exists, if not, create it
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, "w") as f:
            f.write("# Proyecto NERV - Informe de Rendimiento y Señales\n\n")
            f.write(f"**Fecha de generación:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Resumen de Activos\n\n")
            
            # Markdown Table Header
            f.write("| Ticker | Último Precio (USD) | RSI (14) | SMA (50) | SMA (200) | Señal Actual |\n")
            f.write("|--------|---------------------|----------|----------|-----------|--------------|\n")
            
            for res in results:
                # Formatting values safely
                ticker = res.get('Ticker', 'N/A')
                price = f"{res.get('Price', 0.0):.2f}" if res.get('Price') is not None else "N/A"
                rsi = f"{res.get('RSI', 0.0):.2f}" if pd.notna(res.get('RSI')) else "N/A"
                sma50 = f"{res.get('SMA_50', 0.0):.2f}" if pd.notna(res.get('SMA_50')) else "N/A"
                sma200 = f"{res.get('SMA_200', 0.0):.2f}" if pd.notna(res.get('SMA_200')) else "N/A"
                signal = res.get('Signal', 'Hold')
                
                # Colorize signal slightly via HTML tags or just text
                if signal == 'Buy':
                     signal_text = "**🟢 COMPRA**"
                elif signal == 'Sell':
                     signal_text = "**🔴 VENTA**"
                else:
                     signal_text = "⚪ MANTENER"
                     
                f.write(f"| **{ticker}** | ${price} | {rsi} | {sma50} | {sma200} | {signal_text} |\n")
                
            f.write("\n\n---\n*Proyecto NERV - Análisis automatizado.*\n")
            
        logging.info(f"Informe generado exitosamente en {report_path}")
    except Exception as e:
        logging.error(f"Error al generar el informe: {e}")


def main():
    logging.info("Iniciando análisis del Proyecto NERV...")
    
    results = []
    
    for ticker in CONFIG.TICKERS:
        df = load_data(ticker, period="1y", interval="1d")
        
        if df.empty:
            logging.warning(f"Omitiendo {ticker} por falta de datos.")
            continue
            
        df = apply_indicators(df)
        df = apply_strategy(df)
        
        # Obtenemos la última fila válida para el resumen
        try:
            last_row = df.iloc[-1]
            last_signal = 'Hold'
            
            # Revisamos si la señal se activó recientemente (últimos 3 días, o solo el último día)
            # El requerimiento dice: "la última señal disponible". Tomaremos la de la última fila.
            if 'Signal' in df.columns:
                 # It might be more robust to find the last Non-Hold signal or just take the very last row.
                 # Taking strictly the last row:
                 last_signal = last_row['Signal']
            
            results.append({
                'Ticker': ticker,
                'Price': last_row['Close'] if 'Close' in df.columns else None,
                'RSI': last_row['RSI'] if 'RSI' in df.columns else None,
                'SMA_50': last_row['SMA_50'] if 'SMA_50' in df.columns else None,
                'SMA_200': last_row['SMA_200'] if 'SMA_200' in df.columns else None,
                'Signal': last_signal
            })
        except Exception as e:
             logging.error(f"Error extrayendo resultados finales para {ticker}: {e}")
             
    generate_markdown_report(results, CONFIG.REPORT_PATH)
    logging.info("Proyecto NERV ejecutado de manera exitosa.")

if __name__ == "__main__":
    import pandas as pd # Ensure pandas is imported if not globally available, needed for generate_header validation.
    main()
