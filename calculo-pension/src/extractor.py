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
    v = val.strip().lower()
    if v == "---" or v == "": return 0.0 
    if "sin base registrada" in v: return 1.0
    
    # Currency cleanup: "1.634,00" -> 1634.0
    cleaned = v.replace(".", "").replace(",", ".").replace("€", "").strip()
    try:
        # Check if it's just a number
        return float(cleaned)
    except ValueError:
        return 0.0

def clean_base_value(val):
    if not val: return 0.0
    # Join multiline text and clean
    v = str(val).replace("\n", " ").strip().lower()
    
    if v == "---" or v == "": return 0.0 
    if "sin" in v and "base" in v: return 1.0 # Very flexible detection
    
    # Currency cleanup: "1.634,00" -> 1634.0
    cleaned = v.replace(".", "").replace(",", ".").replace("€", "").strip()
    try:
        # Check if it's a number after cleaning
        return float(cleaned)
    except ValueError:
        return 0.0

def extract_to_master_map(pdf_path):
    master_map = {}
    current_regime = None
    last_year = None # Track the year for multi-line rows
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            logger.info(f"Escaneando página {page_num + 1}...")
            
            # Use 'lines' strategy if possible for SS grid, else 'text'
            # SS documents usually have very clear grid lines.
            tables = page.find_tables(table_settings={
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "join_tolerance": 5
            })
            
            # If no tables found with lines, fallback to text detection
            if not tables:
                tables = page.find_tables()

            for t in tables:
                table_top = t.bbox[1]
                rows = t.extract()
                
                for row in rows:
                    if not row: continue
                    
                    # 1. Detect Regime Change
                    row_text = " ".join([str(cell) for cell in row if cell]).upper()
                    if "RÉGIMEN:" in row_text:
                        if "GENERAL" in row_text:
                            current_regime = "GENERAL"
                        elif "AUTONOMO" in row_text:
                            current_regime = "AUTONOMO"
                        last_year = None # Reset year on regime change
                        continue
                    
                    if not current_regime: continue

                    # 2. Extract Year or use previous
                    first_cell = str(row[0]).strip() if row[0] else ""
                    year_match = re.match(r"^(\d{4})$", first_cell)
                    
                    if year_match:
                        last_year = int(year_match.group(1))
                    
                    # If we have a year (either new or carried over), process months
                    if last_year and (1900 < last_year < 2100):
                        # SS tables have 13 columns (Year + 12 months)
                        # If a row is a continuation of "Sin base registrada", it might not have the year
                        for m_idx in range(12):
                            if m_idx + 1 < len(row):
                                val = clean_base_value(row[m_idx + 1])
                                if val > 0:
                                    key = (current_regime, last_year, m_idx + 1)
                                    # Use the maximum value if multiple segments hit the same slot
                                    master_map[key] = max(master_map.get(key, 0.0), val)
    return master_map

def main():
    pdf_path = Path("data/Informe Bases Cotización Online.pdf")
    output_path = Path("data/Bases_Cotizacion.xlsx")
    
    if not pdf_path.exists():
        print("Error: PDF no encontrado.")
        return

    logger.info("Iniciando extracción por mapa maestro de ranuras...")
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
            "Régimen General": base_gen,
            "Autónomos": base_aut
        })
        curr += relativedelta(months=1)
        
    # Convert to DataFrame
    df = pd.DataFrame(master_data)
    
    # Filter: Only keep the range where there is ANY data in ANY column to avoid thousands of empty rows at start/end
    # However, user wants from oldest PDF date. 
    df['Has_Data'] = (df['Régimen General'] > 0) | (df['Autónomos'] > 0)
    if not df[df['Has_Data']].empty:
        first_idx = df[df['Has_Data']].index.min()
        last_idx = df[df['Has_Data']].index.max()
        df = df.loc[first_idx:last_idx].copy()

    # Sort descending for the Excel view
    df = df.sort_values(["Año", "Mes_Num"], ascending=[False, True])

    # Save to intermediate Excel
    # We create two sheets to maintain compatibility with excel_generator.py
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df_gen = df[df['Régimen General'] >= 0][["Año", "Mes", "Régimen General"]].rename(columns={"Régimen General": "Base"})
        df_aut = df[df['Autónomos'] >= 0][["Año", "Mes", "Autónomos"]].rename(columns={"Autónomos": "Base"})
        
        df_gen.to_excel(writer, sheet_name='Regimen_General', index=False)
        df_aut.to_excel(writer, sheet_name='Autonomos', index=False)
        
    logger.info(f"Extracción finalizada. {len(df)} meses en la línea temporal.")
    print("¡Proceso completado!")

if __name__ == "__main__":
    main()
