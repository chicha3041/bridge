# Cálculo de Pensión

## Goal
Desarrollar una herramienta en Python para el cálculo de la pensión de jubilación basándose en las normativas vigentes (cotizaciones, edad, años trabajados, etc.).

## Architecture
- **Lenguaje:** Python 3.12+
- **Gestor de dependencias:** `uv`
- **Estructura:**
  - `src/`: Código fuente del motor de cálculo.
  - `data/`: Datos históricos o tablas de cotización.
  - `tests/`: Pruebas unitarias para validar los cálculos.

## History of Actions
1. **Research & Planning:** Identified `pdfplumber` as the core library for official PDF extraction.
2. **Environment Setup:** Initialized the project folder and installed dependencies (`pdfplumber`, `pandas`, `openpyxl`, `xlsxwriter`).
3. **Core Implementation:**
   - Created `src/extractor.py` to parse the SS PDF.
   - Implemented dynamic regime detection (General vs. Autónomos).
   - Developed logic to transform yearly table rows into monthly records.
   - Implemented automated data cleaning (currency format, handling "---").
4. **Verification:** Generated `data/Bases_Cotizacion.xlsx` and verified the extraction of 227 records for General and 118 for Autónomos.
5. **Simulador Excel:** Creado `src/excel_generator.py` para generar una herramienta operativa con fórmulas reales.
   - Pestaña de configuración con fecha de nacimiento y meses de cómputo ajustables.
   - Tablas de proyección para que el usuario rellene bases futuras.
   - Lógica de cálculo final con bonificación por demora y tope de pensión máxima.

## Current State
- El motor de extracción y el generador de simulador son funcionales.
- Archivo disponible: `data/Calculadora_Pension_Pro.xlsx`.

## Next Steps
- Refinar las fórmulas de la base reguladora para que sumen dinámicamente datos reales + proyectados.
- Implementar la validación de carencia (15 años) para el derecho a la pensión.
- Añadir gráficos de evolución de la base reguladora.
