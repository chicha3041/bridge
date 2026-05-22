from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
import shutil
import logging
from main import BridgeAnalyzer, get_imps
import endplay.parsers.pbn as pbn_parser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BridgeLab")

app = FastAPI()

# Global state to store the last analysis result
last_analysis = {
    "players_data": {},
    "active_boards": [],
    "boards_detail": {},
    "teams_roster": {"Equipo A": [], "Equipo B": []},
    "match_summary": {"gross_a": 0, "gross_b": 0, "net": 0}
}

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="ui"), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open("ui/upload.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/analysis", response_class=HTMLResponse)
async def get_analysis():
    with open("ui/hand_analysis.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/summary", response_class=HTMLResponse)
async def get_summary():
    with open("ui/summary.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/upload")
async def upload_files(
    file_abierta: UploadFile = File(...),
    file_cerrada: UploadFile = File(...)
):
    global last_analysis
    logger.info(f"Uploading files: {file_abierta.filename}, {file_cerrada.filename}")
    
    path_a = UPLOAD_DIR / "abierta_temp.pbn"
    path_c = UPLOAD_DIR / "cerrada_temp.pbn"
    
    try:
        with path_a.open("wb") as buffer: shutil.copyfileobj(file_abierta.file, buffer)
        with path_c.open("wb") as buffer: shutil.copyfileobj(file_cerrada.file, buffer)
            
        analyzer = BridgeAnalyzer()
        
        # Open Room
        with open(path_a, 'r', encoding='utf-8') as f:
            boards_a = pbn_parser.load(f)
        for b in boards_a: analyzer.analyze_deal(b, "Abierta")
            
        # Closed Room
        with open(path_c, 'r', encoding='utf-8') as f:
            boards_c = pbn_parser.load(f)
        for b in boards_c: analyzer.analyze_deal(b, "Cerrada")
            
        analyzer.finalize_analysis()

        # Update global state
        players_data_json = {}
        for name, data in analyzer.players_data.items():
            players_data_json[name] = {
                "bidding": {str(k): v for k, v in data["bidding"].items()},
                "play": {str(k): v for k, v in data["play"].items()},
                "imps": {str(k): v for k, v in data.get("imps", {}).items()}
            }
            
        last_analysis = {
            "active_boards": sorted(list(analyzer.active_boards)),
            "players_data": players_data_json,
            "boards_detail": {str(k): v for k, v in analyzer.boards_detail.items()},
            "teams_roster": {k: sorted(list(v)) for k, v in analyzer.teams_roster.items()},
            "match_summary": {
                "gross_a": analyzer.match_gross_gain['Equipo A'],
                "gross_b": analyzer.match_gross_gain['Equipo B'],
                "net": analyzer.match_gross_gain['Equipo A'] - analyzer.match_gross_gain['Equipo B']
            }
        }

        logger.info(f"Processed {len(analyzer.active_boards)} boards.")
        return JSONResponse({"status": "success", "message": "OK"})
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.get("/api/data")
async def get_data():
    return JSONResponse(last_analysis)

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
