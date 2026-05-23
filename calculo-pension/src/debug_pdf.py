import pdfplumber
import re

pdf_path = "calculo-pension/data/Informe Bases Cotización Online.pdf"

with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages):
        print(f"\n--- PÁGINA {i+1} ---")
        words = page.extract_words()
        for w in words:
            if "Régimen:" in w['text']:
                line = page.within_bbox((0, w['top']-5, page.width, w['bottom']+5)).extract_text()
                print(f"HEADER ENCONTRADO: '{line}' en Y={w['top']}")
        
        tables = page.find_tables()
        for j, t in enumerate(tables):
            print(f"TABLA {j+1} en Y={t.bbox[1]}")
            data = t.extract()
            if data and data[0]:
                print(f"  Primeras celdas: {data[0][:3]}")
