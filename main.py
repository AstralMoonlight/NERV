import os
import datetime
import logging
import time
import json
from typing import List, Dict

import CONFIG
from src.data_loader import load_data
from src.indicators import apply_indicators
from src.strategy import run_backtest # Now using the backtest engine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_markdown_report(results: List[Dict], report_path: str):
    """Generates a detailed Markdown report with global aggregates and per-ticker logs."""
    try:
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        # Cálculos Globales
        total_tickers = len(results)
        total_invertido = total_tickers * CONFIG.BACKTEST_CAPITAL_INICIAL
        capital_final_total = sum(res.get('Capital Final', 0.0) for res in results)
        capital_heldeado_total = sum(res.get('Capital en Posición', 0.0) for res in results)
        rendimiento_global = ((capital_final_total - total_invertido) / total_invertido) * 100 if total_invertido > 0 else 0
        
        tickers_ganadores = sum(1 for res in results if res.get('Rendimiento (%)', 0) > 0)
        tickers_perdedores = sum(1 for res in results if res.get('Rendimiento (%)', 0) < 0)
        win_rate = (tickers_ganadores / total_tickers * 100) if total_tickers > 0 else 0
        
        with open(report_path, "w") as f:
            f.write("# Proyecto NERV - Informe de Backtesting Global\n\n")
            f.write(f"**Fecha de generación:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## 📊 Resumen Ejecutivo Global\n")
            f.write("| Métrica | Valor |\n")
            f.write("|---------|-------|\n")
            f.write(f"| **Total Activos Analizados** | {total_tickers} |\n")
            f.write(f"| **Inversión Inicial Total** | ${total_invertido:,.2f} |\n")
            f.write(f"| **Valor Final de Cartera** | ${capital_final_total:,.2f} |\n")
            f.write(f"| **Capital Actual Heldeado** | **${capital_heldeado_total:,.2f}** |\n")
            
            rend_global_str = f"{rendimiento_global:+.2f}%"
            if rendimiento_global > 0: rend_global_str = f"🟢 **{rend_global_str}**"
            elif rendimiento_global < 0: rend_global_str = f"🔴 **{rend_global_str}**"
            
            f.write(f"| **Rendimiento Global** | {rend_global_str} |\n")
            f.write(f"| **Win Rate (Activos)** | {win_rate:.1f}% ({tickers_ganadores} ✅ / {tickers_perdedores} ❌) |\n\n")

            f.write("--- \n\n")
            
            f.write("## 📈 Tabla Comparativa de Activos\n")
            f.write("| Ticker | Ops | Capital Final | Rendimiento | Estado |\n")
            f.write("|--------|-----|---------------|-------------|--------|\n")
            
            for res in results:
                ticker = res.get('Ticker', 'N/A')
                ops = res.get('Operaciones Creadas', 0)
                cap = res.get('Capital Final', 0.0)
                rend = res.get('Rendimiento (%)', 0.0)
                estado = res.get('Estado', 'N/A')
                
                rend_str = f"{rend:+.2f}%"
                if rend > 0: rend_str = f"🟢 {rend_str}"
                elif rend < 0: rend_str = f"🔴 {rend_str}"
                
                f.write(f"| **{ticker}** | {ops} | ${cap:,.2f} | {rend_str} | *{estado}* |\n")
            
            f.write("\n---\n\n")
            f.write("## 📝 Detalle de Operaciones\n\n")
            
            for res in results:
                ticker = res.get('Ticker', 'N/A')
                history = res.get('History', [])
                
                if not history:
                    continue
                    
                f.write(f"### 🔍 {ticker}\n")
                f.write("| Fecha | Acción | Monto | Precio | Motivo |\n")
                f.write("|-------|---------|-------|--------|--------|\n")
                for event in history:
                    monto_str = f"${event['amount']:,.2f}"
                    precio_str = f"${event['price']:,.2f}"
                    f.write(f"| {event['date']} | **{event['action']}** | {monto_str} | {precio_str} | {event['reason']} |\n")
                f.write("\n")
                
            f.write("\n\n*Proyecto NERV - Motor de Backtesting Detallado.*\n")
            
        logging.info(f"Informe generado exitosamente en {report_path}")
    except Exception as e:
        logging.error(f"Error al generar el informe: {e}")


def generate_signals_report(results: List[Dict], report_path: str) -> List[Dict]:
    """Generates a concise report with only today's BUY/SELL signals and returns them."""
    try:
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        # Obtener la fecha más reciente de los resultados
        last_dates = []
        for res in results:
            if res.get('History'):
                last_dates.append(res['History'][-1]['date'])
        
        if not last_dates:
            logging.warning("No hay historial operativo para generar señales.")
            return []

        reference_date = max(last_dates)
        signals = []
        
        for res in results:
            history = res.get('History', [])
            if history:
                last_event = history[-1]
                if last_event['date'] == reference_date:
                    signals.append({
                        'Ticker': res['Ticker'],
                        'Acción': last_event['action'],
                        'Precio': last_event['price'],
                        'Motivo': last_event['reason'],
                        'Fecha': last_event['date']
                    })

        with open(report_path, "w") as f:
            f.write(f"# 🎯 Recomendaciones NERV - {reference_date}\n\n")
            
            if not signals:
                f.write("No hay señales de COMPRA o VENTA detectadas para la jornada más reciente.\n")
            else:
                f.write("### 📢 Acciones Sugeridas\n")
                f.write("| Ticker | Operación | Precio Ref. | Motivo Técnico |\n")
                f.write("|--------|-----------|-------------|----------------|\n")
                for s in signals:
                    emoji = "🚀" if s['Acción'] == 'Compra' else "💰"
                    f.write(f"| **{s['Ticker']}** | {emoji} **{s['Acción']}** | ${s['Precio']:,.2f} | {s['Motivo']} |\n")
            
            f.write("\n\n*Nota: Estas señales corresponden al estado más reciente detectado en el backtest.*")
            
        logging.info(f"Reporte de señales generado exitosamente en {report_path}")
        return signals

    except Exception as e:
        logging.error(f"Error generando reporte de señales: {e}")
        return []

def append_signals_to_json(signals: List[Dict], log_path: str):
    """Appends current signals to a historical JSON log file."""
    if not signals:
        return
        
    try:
        history = []
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                try:
                    history = json.load(f)
                except json.JSONDecodeError:
                    history = []
        
        # Agregar nuevas señales con timestamp de procesamiento
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for s in signals:
            entry = s.copy()
            entry['processed_at'] = now_str
            # Evitar duplicados exactos si el cron corre varias veces el mismo día
            if not any(h['Ticker'] == entry['Ticker'] and h['Fecha'] == entry['Fecha'] and h['Acción'] == entry['Acción'] for h in history):
                history.append(entry)
            
        # Mantener solo las últimas 1000 entradas
        history = history[-1000:]
        
        with open(log_path, 'w') as f:
            json.dump(history, f, indent=4)
            
        logging.info(f"Señales históricas guardadas en {log_path}")
    except Exception as e:
        logging.error(f"Error guardando señales en JSON: {e}")


def main():
    while True:
        logging.info("--- Iniciando ciclo de escaneo NERV ---")
        
        results = []
        
        for ticker in CONFIG.TICKERS:
            df = load_data(ticker, period="3y", interval="1d")
            
            if df.empty:
                logging.warning(f"Omitiendo {ticker} por falta de datos.")
                continue
                
            # 1. Agregar Indicadores (RSI y SMAs)
            df = apply_indicators(df)
            
            # 2. Correr Backtest sobre los históricos
            try:
                 resultado_ticker = run_backtest(df, ticker)
                 if resultado_ticker:
                      results.append(resultado_ticker)
            except Exception as e:
                 logging.error(f"Error procesando backtest para {ticker}: {e}")
        
        if results:
            # Generar nombres con fecha para el historial
            today_str = datetime.datetime.now().strftime('%Y-%m-%d')
            
            # Informe de Backtest con fecha (Auditoría visual)
            base_report, ext_report = os.path.splitext(CONFIG.REPORT_PATH)
            dated_report_path = f"{base_report}_{today_str}{ext_report}"
            generate_markdown_report(results, dated_report_path)
            
            # Informe de Señales con fecha (Acción diaria)
            base_signal, ext_signal = os.path.splitext(CONFIG.SIGNAL_REPORT_PATH)
            dated_signal_path = f"{base_signal}_{today_str}{ext_signal}"
            signals_today = generate_signals_report(results, dated_signal_path)
            
            # Log Histórico JSON (Para integración Web)
            append_signals_to_json(signals_today, CONFIG.SIGNALS_JSON_LOG)
            
            logging.info("Simulación y reporteo terminados exitosamente.")
            logging.info(f"Reportes guardados: {os.path.basename(dated_report_path)} y {os.path.basename(dated_signal_path)}")
        else:
            logging.warning("No se generaron resultados de backtest.")

        # EL ESCUDO ANTI-BANEO (Sentinel Mode)
        logging.info("Modo centinela activado. Próximo escaneo en 1 hora...")
        time.sleep(3600)

if __name__ == "__main__":
    main()
