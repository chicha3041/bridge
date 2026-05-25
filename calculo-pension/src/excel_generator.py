import pandas as pd
import xlsxwriter
from pathlib import Path
from datetime import date
from dateutil.relativedelta import relativedelta

def generate_simulator():
    input_path = Path("data/Bases_Cotizacion.xlsx")
    output_path = Path("data/Calculadora_Pension_Pro.xlsx")

    if not input_path.exists():
        print(f"Error: No se encuentra {input_path}")
        return

    # 1. Carga de datos estable
    df_gen = pd.read_excel(input_path, sheet_name='Regimen_General')
    df_aut = pd.read_excel(input_path, sheet_name='Autonomos')

    workbook = xlsxwriter.Workbook(str(output_path))
    
    # Formatos profesionales
    fmt_title = workbook.add_format({'bold': True, 'font_size': 14, 'font_color': '#FFFFFF', 'bg_color': '#1F4E78', 'border': 2})
    fmt_header = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1, 'align': 'center'})
    fmt_input = workbook.add_format({'bg_color': '#FFF2CC', 'border': 1, 'align': 'center'})
    fmt_currency = workbook.add_format({'num_format': '#,##0.00 €', 'border': 1, 'align': 'right'})
    fmt_date = workbook.add_format({'num_format': 'dd/mm/yyyy', 'align': 'center', 'border': 1})
    fmt_perc = workbook.add_format({'num_format': '0.00%', 'border': 1, 'align': 'center'})
    fmt_pdf = workbook.add_format({'bg_color': '#FFFFFF', 'border': 1, 'align': 'right'})
    fmt_proj = workbook.add_format({'bg_color': '#EBF1DE', 'border': 1, 'align': 'right'})
    fmt_delay = workbook.add_format({'bg_color': '#DEEBF7', 'border': 1, 'align': 'right'})
    fmt_bold = workbook.add_format({'bold': True, 'border': 1})
    fmt_result = workbook.add_format({'bold': True, 'font_size': 12, 'bg_color': '#FFFF00', 'border': 2, 'num_format': '#,##0.00 €'})
    fmt_center = workbook.add_format({'align': 'center', 'border': 1})

    # --- PESTAÑA 1: PANEL DE CONTROL ---
    ws1 = workbook.add_worksheet('1. Panel de Control')
    ws1.set_column('A:A', 35); ws1.set_column('B:G', 20)

    ws1.write('A1', 'CONFIGURACIÓN DE JUBILACIÓN', fmt_title)
    ws1.write('A2', 'Fecha Nacimiento:', fmt_header); ws1.write('B2', '13/08/1962', fmt_input)
    ws1.write('A3', 'Meses Demora deseada:', fmt_header); ws1.write('B3', 12, fmt_input)
    ws1.write('A4', 'Cómputo Bases (Meses):', fmt_header); ws1.write('B4', 300, fmt_input)
    
    ws1.write('A6', 'JUBILACIÓN CALCULADA', fmt_header)
    ws1.write_formula('B6', '=DATE(YEAR(B2)+67, MONTH(B2), DAY(B2))', fmt_date)
    ws1.write('A7', 'ID Mes Jubilación (Ref):', fmt_header)
    ws1.write_formula('B7', '=YEAR(B8)*100 + MONTH(B8)')
    ws1.write('A8', 'Fecha Jubilación Final:', fmt_header)
    ws1.write_formula('B8', '=EDATE(B6, B3)', fmt_date)

    ws1.write('A10', 'ESTADÍSTICAS DE TIEMPO Y ESCALA', fmt_header)
    ws1.write_row('A11', ['Escenario', 'Meses PDF', 'Años PDF', 'Meses Proy.', 'Años Proy.', 'Años TOTALES', '% Pensión'], fmt_header)
    
    for i, (name, col) in enumerate([('Reg. General', 'C'), ('Autónomos', 'D'), ('UNIFICADO', 'I')]):
        r = 11 + i
        ws1.write(r, 0, name, fmt_bold)
        ws1.write_formula(r, 1, f'=COUNTIFS(\'2. Cronologia\'!$E$1:$E$600, "PDF", \'2. Cronologia\'!${col}$1:${col}$600, ">0")')
        ws1.write_formula(r, 2, f'=B{r+1}/12', fmt_center)
        ws1.write_formula(r, 3, f'=COUNTIFS(\'2. Cronologia\'!$E$1:$E$600, "<>PDF", \'2. Cronologia\'!${col}$1:${col}$600, ">0")')
        ws1.write_formula(r, 4, f'=D{r+1}/12', fmt_center)
        ws1.write_formula(r, 5, f'=C{r+1}+E{r+1}', fmt_center)
        # PIECEWISE SCALE: 15a=50% + tramos
        ws1.write_formula(r, 6, f'=IF(F{r+1}<15, 0, MIN(1, 0.5 + (MIN(48, MAX(0, F{r+1}*12-180))*0.00215) + (MAX(0, F{r+1}*12-228)*0.0019)))', fmt_perc)

    ws1.write('A15', 'CÁLCULO DE BASES REGULADORAS', fmt_header)
    ws1.write_row('A16', ['Concepto', 'Reg. General', 'Autónomos', 'OPCIÓN CONJUNTA'], fmt_header)
    ws1.write('A17', 'Suma de Bases (Ajustada):', fmt_bold)
    ws1.write_formula('B17', '=\'3. Calculo General\'!$C$306', fmt_currency)
    ws1.write_formula('C17', '=\'4. Calculo Autonomos\'!$B$306', fmt_currency)
    ws1.write_formula('D17', '=\'5. Calculo Conjunto\'!$C$306', fmt_currency)
    ws1.write('A18', 'Divisor aplicable:', fmt_bold); ws1.write_row('B18', [350, 350, 350], fmt_center)
    ws1.write('A19', 'Base Reguladora (BR):', fmt_bold)
    ws1.write_formula('B19', '=B17/B18', fmt_currency); ws1.write_formula('C19', '=C17/C18', fmt_currency); ws1.write_formula('D19', '=D17/D18', fmt_currency)

    ws1.write('A21', 'ESTIMACIÓN DE PENSIÓN FINAL', fmt_header)
    ws1.write_row('A22', ['Opción', 'Pensión Base', 'Bonif. Demora EFECTIVA', 'TOTAL BRUTO', 'Veredicto'], fmt_header)
    
    # Delay check cell
    ws1.write('A24', 'Meses Demora EFECTIVOS:', fmt_bold)
    ws1.write_formula('B24', '=COUNTIFS(\'2. Cronologia\'!$E$1:$E$600, "DEMORA", \'2. Cronologia\'!$I$1:$I$600, 1)')
    
    # Max Pension
    ws1.write('A25', 'Tope Máximo Actual:', fmt_bold); ws1.write('B25', 3175.04, fmt_currency)

    # Option 1: SUMATORIO
    ws1.write('A26', 'Suma Independiente:', fmt_bold)
    ws1.write_formula('B26', '=B19*G12 + C19*G13', fmt_currency)
    ws1.write_formula('C26', '=MIN(B26, B25) * (INT(B24/12)*0.04)', fmt_currency)
    ws1.write_formula('D26', '=MIN(B26, B25) + C26', fmt_currency)
    
    # Option 2: UNIFICADA
    ws1.write('A27', 'Pensión Unificada:', fmt_bold)
    ws1.write_formula('B27', '=D19 * G14', fmt_currency)
    ws1.write_formula('C27', '=MIN(B27, B25) * (INT(B24/12)*0.04)', fmt_currency)
    ws1.write_formula('D27', '=MIN(B27, B25) + C27', fmt_currency)
    
    ws1.write_formula('E26', '=IF(D26>=D27, "MEJOR OPCIÓN", "")', fmt_center)
    ws1.write_formula('E27', '=IF(D27>D26, "MEJOR OPCIÓN", "")', fmt_center)

    ws1.write('A29', 'PENSIÓN MENSUAL RESULTANTE:', fmt_title)
    ws1.write_formula('B29', '=MAX(D26, D27)', fmt_result)

    # --- PESTAÑA 2: CRONOLOGÍA ---
    ws2 = workbook.add_worksheet('2. Cronologia')
    ws2.set_column('A:B', 10); ws2.set_column('C:D', 20); ws2.set_column('E:E', 15); ws2.set_column('H:I', 12)
    ws2.write_row('A1', ['Año', 'Mes', 'Base General', 'Base Autónomos', 'Origen'], fmt_header)
    meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    data_gen = {(int(r['Año']), r['Mes']): r['Base'] for _, r in df_gen.iterrows()}
    data_aut = {(int(r['Año']), r['Mes']): r['Base'] for _, r in df_aut.iterrows()}
    
    current = date(2040, 12, 1); end_date = date(1980, 1, 1); row = 1
    while current >= end_date:
        y, m = current.year, meses_nombres[current.month-1]
        ws2.write(row, 0, y, fmt_center); ws2.write(row, 1, m, fmt_center)
        is_pdf = current <= date(2026, 4, 1)
        val_gen = data_gen.get((y, m), 0.0); val_aut = data_aut.get((y, m), 0.0)
        style = fmt_pdf if is_pdf else (fmt_proj if current <= date(2029, 8, 1) else fmt_delay)
        ws2.write(row, 2, val_gen, style); ws2.write(row, 3, val_aut, style); ws2.write(row, 4, 'PDF' if is_pdf else ('DEMORA' if style==fmt_delay else 'PROYECTADO'), style)
        ws2.write(row, 7, y*100 + current.month, fmt_center)
        ws2.write_formula(row, 8, f'=IF(OR(C{row+1}>0, D{row+1}>0), 1, 0)', fmt_center)
        current -= relativedelta(months=1); row += 1

    # --- PESTAÑAS DE CÁLCULO ---
    for name, col, sheet_name in [('GENERAL', 'C', '3. Calculo General'), ('AUTONOMOS', 'D', '4. Calculo Autonomos'), ('CONJUNTO', 'C+D', '5. Calculo Conjunto')]:
        ws = workbook.add_worksheet(sheet_name)
        ws.set_column('A:A', 40); ws.set_column('B:C', 20)
        ws.write('A1', f'DETALLE TÉCNICO: {name}', fmt_title)
        if name in ['GENERAL', 'CONJUNTO']:
            ws.write_row('A4', ['Mes Relativo (Atrás)', 'Base Original', 'Base con Relleno (800/400)'], fmt_header)
            for i in range(300):
                r = 4 + i
                ws.write(r, 0, f'Mes {i+1} atrás')
                if name == 'GENERAL': f_orig = f'=INDEX(\'2. Cronologia\'!C:C, MATCH(\'1. Panel de Control\'!$B$7, \'2. Cronologia\'!$H:$H, 0)+{i+1})'
                else: f_orig = f'=INDEX(\'2. Cronologia\'!C:C, MATCH(\'1. Panel de Control\'!$B$7, \'2. Cronologia\'!$H:$H, 0)+{i+1}) + INDEX(\'2. Cronologia\'!D:D, MATCH(\'1. Panel de Control\'!$B$7, \'2. Cronologia\'!$H:$H, 0)+{i+1})'
                ws.write_formula(r, 1, f_orig, fmt_currency)
                ws.write_formula(r, 2, f'=IF(B{r+1}>0, B{r+1}, IF(COUNTIF($B$5:B{r+1}, "=0")<=48, 800, 400))', fmt_currency)
            ws.write('A306', 'SUMA BASES ORIGINAL:', fmt_bold); ws.write_formula('B306', '=SUM(B5:B304)', fmt_currency)
            ws.write('A307', 'SUMA BASES RELLENADA:', fmt_bold); ws.write_formula('C306', '=SUM(C5:C304)', fmt_currency)
        else: # AUTONOMOS
            ws.write_row('A4', ['Mes Relativo (Atrás)', 'Base Utilizada'], fmt_header)
            for i in range(300):
                r = 4 + i
                ws.write(r, 0, f'Mes {i+1} atrás')
                ws.write_formula(r, 1, f'=INDEX(\'2. Cronologia\'!D:D, MATCH(\'1. Panel de Control\'!$B$7, \'2. Cronologia\'!$H:$H, 0)+{i+1})', fmt_currency)
            ws.write('A306', 'SUMA TOTAL BASES:', fmt_bold); ws.write_formula('B306', '=SUM(B5:B304)', fmt_currency)

    workbook.close()
    print(f"Simulador restaurado al 100%: {output_path}")

if __name__ == "__main__":
    generate_simulator()
