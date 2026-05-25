import pdfplumber
import pandas as pd
from pathlib import Path
import re
import logging
from datetime import date
from dateutil.relativedelta import relativedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RobustExtractor")

def clean_base_value(val):
    if not val: return 0.0
    # Join multiline text and clean
    v = str(val).replace("\n", " ").strip().lower()
    
    if v == "---" or v == "" or "sin" in v: return 0.0 
    
    # Currency cleanup: remove thousands separator (dot) and replace decimal separator (comma)
    cleaned = v.replace(".", "").replace(",", ".").replace("€", "").strip()
    try:
        fval = float(cleaned)
        # Security check: ignore SS number or identification data misread as base
        if fval > 100000: return 0.0
        return fval
    except ValueError:
        return 0.0

def extract_to_master_map(pdf_path):
    master_map = {}
    current_regime = None
    last_year = None
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            logger.info(f"Escaneando página {page_num + 1}...")
            
            # Use 'lines' strategy to capture the SS grid perfectly
            tables = page.find_tables(table_settings={
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "join_tolerance": 5
            })
            
            if not tables:
                tables = page.find_tables()

            for t in tables:
                rows = t.extract()
                for row in rows:
                    if not row or not row[0]: continue
                    
                    row_text = " ".join([str(cell) for cell in row if cell]).upper()
                    
                    # 1. BLINDAGE: Ignore identification/header rows strictly
                    if "280389626156" in row_text or "APELLIDOS" in row_text or "RUIZ ORIOL" in row_text:
                        continue
                    
                    # 2. Detect Regime Change
                    if "RÉGIMEN:" in row_text:
                        if "GENERAL" in row_text:
                            current_regime = "GENERAL"
                        elif "AUTONOMO" in row_text:
                            current_regime = "AUTONOMO"
                        last_year = None 
                        continue
                    
                    if not current_regime: continue

                    # 3. Extract Year
                    first_cell = str(row[0]).strip()
                    year_match = re.match(r"^(\d{4})$", first_cell)
                    
                    if year_match:
                        y_val = int(year_match.group(1))
                        if 1950 <= y_val <= 2050:
                            last_year = y_val
                        else:
                            last_year = None
                    
                    if last_year:
                        for m_idx in range(12):
                            if m_idx + 1 < len(row):
                                val = clean_base_value(row[m_idx + 1])
                                if val > 0:
                                    key = (current_regime, last_year, m_idx + 1)
                                    master_map[key] = max(master_map.get(key, 0.0), val)
                                elif key not in master_map:
                                    master_map[key] = 0.0
    return master_map

def main():
    pdf_path = Path("data/Informe Bases Cotización Online.pdf")
    output_path = Path("data/Bases_Cotizacion.xlsx")
    
    if not pdf_path.exists():
        print("Error: PDF no encontrado.")
        return

    logger.info("Restaurando motor estable con blindaje para 2012 y ceros absolutos...")
    master_map = extract_to_master_map(pdf_path)
    
    # 1. Define the full range of the report (Jan 1987 to Dec 2026 based on PDF headers)
    start_date = date(1987, 1, 1)
    end_date = date(2026, 12, 1)
    
    months_names = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    master_data = []
    curr = start_date
    while curr <= end_date:
        y, m = curr.year, curr.month
        base_gen = master_map.get(("GENERAL", y, m), 0.0)
        base_aut = master_map.get(("AUTONOMO", y, m), 0.0)
        
        master_data.append({
            "Año": y,
            "Mes": months_names[m-1],
            "Mes_Num": m,
            "Base_Gen": base_gen,
            "Base_Aut": base_aut
        })
        curr += relativedelta(months=1)
        
    df = pd.DataFrame(master_data)
    
    active = df[(df['Base_Gen'] > 0) | (df['Base_Aut'] > 0)]
    if not active.empty:
        df = df.loc[active.index.min():active.index.max()].copy()

    df = df.sort_values(["Año", "Mes_Num"], ascending=[False, True])

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df[["Año", "Mes", "Base_Gen"]].rename(columns={"Base_Gen": "Base"}).to_excel(writer, sheet_name='Regimen_General', index=False)
        df[["Año", "Mes", "Base_Aut"]].rename(columns={"Base_Aut": "Base"}).to_excel(writer, sheet_name='Autonomos', index=False)
        
    logger.info(f"Extracción finalizada. {len(df)} meses procesados.")
    print("¡Proceso completado!")

if __name__ == "__main__":
    main()
