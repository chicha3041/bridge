import pandas as pd
import xlsxwriter
from pathlib import Path
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

def generate_simulator():
    input_path = Path("data/Bases_Cotizacion.xlsx")
    output_path = Path("data/Calculadora_Pension_Pro.xlsx")

    if not input_path.exists():
        print(f"Error: No se encuentra {input_path}")
        return

    df_gen = pd.read_excel(input_path, sheet_name='Regimen_General')
    df_aut = pd.read_excel(input_path, sheet_name='Autonomos')

    workbook = xlsxwriter.Workbook(str(output_path))
    
    # Formatos
    fmt_header = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1, 'align': 'center'})
    fmt_input = workbook.add_format({'bg_color': '#FFF2CC', 'border': 1, 'align': 'center'})
    fmt_currency = workbook.add_format({'num_format': '#,##0.00 €', 'border': 1, 'align': 'right'})
    fmt_date = workbook.add_format({'num_format': 'dd/mm/yyyy', 'align': 'center', 'border': 1})
    fmt_title = workbook.add_format({'bold': True, 'font_size': 14, 'font_color': '#1F4E78'})
    fmt_bold = workbook.add_format({'bold': True, 'align': 'left'})
    fmt_center = workbook.add_format({'align': 'center', 'border': 1})
    fmt_perc = workbook.add_format({'num_format': '0.00%', 'border': 1, 'align': 'center'})
    fmt_highlight = workbook.add_format({'bold': True, 'bg_color': '#FFFF00', 'border': 1, 'align': 'right', 'num_format': '#,##0.00 €'})
    fmt_pdf = workbook.add_format({'bg_color': '#F2F2F2', 'border': 1, 'align': 'right'})
    fmt_proj = workbook.add_format({'bg_color': '#EBF1DE', 'border': 1, 'align': 'right'}) # Verde
    fmt_delay = workbook.add_format({'bg_color': '#DEEBF7', 'border': 1, 'align': 'right'}) # Azul

    # --- PESTAÑA 1: CONFIGURACIÓN Y PROYECCIÓN ---
    ws1 = workbook.add_worksheet('1. Config y Proyeccion')
    ws1.set_column('A:A', 30)
    ws1.set_column('B:B', 18)
    ws1.set_column('D:E', 12) 
    ws1.set_column('F:G', 20) 

    ws1.write('A1', 'DATOS DE SIMULACIÓN', fmt_title)
    ws1.write('A2', 'Fecha Nacimiento:', fmt_header); ws1.write('B2', '13/08/1962', fmt_input)
    ws1.write('A3', 'Años para 100% (Normativa):', fmt_header); ws1.write('B3', 37, fmt_input)
    ws1.write('A4', 'Meses Demora deseada:', fmt_header); ws1.write('B4', 12, fmt_input) 
    
    ws1.write('A6', 'JUBILACIÓN CALCULADA', fmt_header)
    ws1.write_formula('B6', '=DATE(YEAR(B2)+67, MONTH(B2), DAY(B2))', fmt_date)
    ws1.write('A7', 'ID Mes Jubilación:', fmt_header)
    ws1.write_formula('B7', '=YEAR(B6)*100 + MONTH(B6)')
    ws1.write('A8', 'Fecha Jubilación Final:', fmt_header)
    ws1.write_formula('B8', '=EDATE(B6, B4)', fmt_date)

    ws1.write('D1', 'TABLA CRONOLÓGICA COMPLETA', fmt_title)
    ws1.write_row('D2', ['Año', 'Mes', 'Base Rég. General', 'Base Autónomos', 'ID_Mes'], fmt_header)
    
    start_sim = date(2040, 12, 1) # Extendido para cubrir demoras largas
    end_sim = date(1980, 1, 1)
    current = start_sim
    row = 2
    
    meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                     "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    data_gen = {(int(r['Año']), r['Mes']): r['Base'] for _, r in df_gen.iterrows()}
    data_aut = {(int(r['Año']), r['Mes']): r['Base'] for _, r in df_aut.iterrows()}
    last_real_date = date(2026, 4, 1)

    while current >= end_sim:
        y, m_name = current.year, meses_nombres[current.month-1]
        ws1.write(row, 3, y, fmt_center)
        ws1.write(row, 4, m_name, fmt_center)
        ws1.write(row, 7, y*100 + current.month) # ID_Mes column
        
        is_pdf = current <= last_real_date
        if is_pdf:
            ws1.write(row, 5, data_gen.get((y, m_name), 0.0), fmt_pdf)
            ws1.write(row, 6, data_aut.get((y, m_name), 0.0), fmt_pdf)
        else:
            # Determining projection vs delay based on 1962 birth date
            # We use a static calculation for styling in this python script
            ord_ret = date(2029, 8, 1)
            style = fmt_proj if current <= ord_ret else fmt_delay
            ws1.write(row, 5, 0.0, style)
            ws1.write(row, 6, 0.0, style)
            
        current -= relativedelta(months=1)
        row += 1

    # --- PESTAÑA 2: CÁLCULO DE RESULTADOS ---
    ws2 = workbook.add_worksheet('2. Calculo de Pension')
    ws2.set_column('A:A', 50)
    ws2.set_column('B:D', 25)

    ws2.write('A1', 'DESGLOSE TÉCNICO DE PENSIÓN', fmt_title)
    
    # 1. Row Index of Month Prior to Retirement (X - 1)
    # The law says computation starts from the month prior to the month prior to retirement.
    ws2.write('A3', 'Índice de Inicio (Mes - 1):', fmt_bold)
    ws2.write_formula('B3', '=MATCH(\'1. Config y Proyeccion\'!B7, \'1. Config y Proyeccion\'!H:H, 0) + 1')
    
    # 2. Maximum Pension Projections
    ws2.write('A5', 'Pensión Máxima Actual (2024):', fmt_bold); ws2.write('B5', 3175.04, fmt_currency)
    ws2.write('A6', 'Pensión Máxima Estimada (Año Jubilación):', fmt_bold)
    ws2.write_formula('B6', '=B5 * (1.02)^(YEAR(\'1. Config y Proyeccion\'!B8)-2024)', fmt_currency)

    ws2.write_row('A8', ['Concepto de Cálculo', 'Sistema Tradicional (25a)', 'Reforma 2034 (28a)', 'MEJOR OPCIÓN'], fmt_header)
    
    # --- REGIMEN GENERAL ---
    ws2.write('A9', 'RÉGIMEN GENERAL', workbook.add_format({'bold': True, 'bg_color': '#F2F2F2'}))
    ws2.write('A10', 'Base Reguladora (BR):', fmt_bold)
    # 25a: Sum last 300 from B3 index / 350
    ws2.write_formula('B10', '=(SUM(OFFSET(\'1. Config y Proyeccion\'!$F$1, $B$3, 0, 300))) / 350', fmt_currency)
    # 28a: Best 318 of last 336 / 371
    ws2.write_formula('C10', '=(SUM(LARGE(OFFSET(\'1. Config y Proyeccion\'!$F$1, $B$3, 0, 336), ROW(INDIRECT("1:318"))))) / 371', fmt_currency)
    ws2.write_formula('D10', '=MAX(B10, C10)', fmt_highlight)

    ws2.write('A11', 'Años Cotizados (Totales):', fmt_bold)
    ws2.write_formula('B11', '=COUNTIF(\'1. Config y Proyeccion\'!F:F, ">0")/12', fmt_center)
    ws2.write_formula('C11', '=B11', fmt_center)

    ws2.write('A12', 'Pensión Base (Sin demora):', fmt_bold)
    # Applied % based on 37 years for 100%
    ws2.write_formula('B12', '=B10 * IF(B11<15, 0, MIN(1, 0.5 + (B11-15) * (0.5/(37-15))))', fmt_currency)
    ws2.write_formula('C12', '=C10 * IF(C11<15, 0, MIN(1, 0.5 + (C11-15) * (0.5/(37-15))))', fmt_currency)
    ws2.write_formula('D12', '=MAX(B12, C12)', fmt_highlight)

    # --- RÉGIMEN AUTÓNOMOS ---
    ws2.write('A14', 'RÉGIMEN AUTÓNOMOS', workbook.add_format({'bold': True, 'bg_color': '#F2F2F2'}))
    ws2.write('A15', 'Base Reguladora (BR):', fmt_bold)
    ws2.write_formula('B15', '=(SUM(OFFSET(\'1. Config y Proyeccion\'!$G$1, $B$3, 0, 300))) / 350', fmt_currency)
    ws2.write_formula('C15', '=(SUM(LARGE(OFFSET(\'1. Config y Proyeccion\'!$G$1, $B$3, 0, 336), ROW(INDIRECT("1:318"))))) / 371', fmt_currency)
    ws2.write_formula('D15', '=MAX(B15, C15)', fmt_highlight)

    ws2.write('A16', 'Años Cotizados (Totales):', fmt_bold)
    ws2.write_formula('B16', '=COUNTIF(\'1. Config y Proyeccion\'!G:G, ">0")/12', fmt_center)
    ws2.write_formula('C16', '=B16', fmt_center)

    ws2.write('A17', 'Pensión Base (Sin demora):', fmt_bold)
    ws2.write_formula('B17', '=B15 * IF(B16<15, 0, MIN(1, 0.5 + (B16-15) * (0.5/(37-15))))', fmt_currency)
    ws2.write_formula('C17', '=C15 * IF(C16<15, 0, MIN(1, 0.5 + (C11-15) * (0.5/(37-15))))', fmt_currency)
    ws2.write_formula('D17', '=MAX(B17, C17)', fmt_highlight)

    # --- TOTAL CONSOLIDADO ---
    ws2.write('A19', 'TOTAL ACUMULADO (AMBOS REGÍMENES)', fmt_header)
    ws2.write('A20', 'Suma Pensiones Base:', fmt_bold)
    ws2.write_formula('B20', '=B12 + B17', fmt_currency)
    ws2.write_formula('C20', '=C12 + C17', fmt_currency)
    ws2.write_formula('D20', '=MAX(B20, C20)', fmt_highlight)

    ws2.write('A21', 'Pensión Sujeta a Tope Máximo:', fmt_bold)
    ws2.write_formula('B21', '=MIN(B20, B6)', fmt_currency)
    ws2.write_formula('C21', '=MIN(C20, B6)', fmt_currency)

    ws2.write('A22', 'Bonificación por Demora (4% anual):', fmt_bold)
    # Bonus is calculated over the CAPPED pension
    ws2.write_formula('B22', '=B21 * (INT(\'1. Config y Proyeccion\'!B4/12) * 0.04)', fmt_currency)
    ws2.write_formula('C22', '=C21 * (INT(\'1. Config y Proyeccion\'!B4/12) * 0.04)', fmt_currency)

    ws2.set_row(23, 25)
    ws2.write('A24', 'PENSIÓN FINAL MENSUAL ESTIMADA:', fmt_title)
    ws2.write_formula('B24', '=B21 + B22', fmt_currency)
    ws2.write_formula('C24', '=C21 + C22', fmt_currency)
    ws2.write_formula('D24', '=MAX(B24, C24)', fmt_highlight)

    # --- ESTADÍSTICAS DEL PDF ---
    ws2.write('A27', 'DATOS PROCEDENTES DEL PDF', fmt_header)
    ws2.write('A28', 'Meses Cotizados Reales - General:', fmt_bold); ws2.write('B28', len(df_gen))
    ws2.write('A29', 'Meses Cotizados Reales - Autónomos:', fmt_bold); ws2.write('B29', len(df_aut))

    workbook.close()
    print(f"Simulador hyper-preciso generado en: {output_path}")

if __name__ == "__main__":
    generate_simulator()
