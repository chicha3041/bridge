# Bridge Match Analyzer

A Python-based tool to analyze Bridge matches by comparing bidding and play against a Double Dummy Solver (DDS).

## Features
- **Bidding Analysis:** Compares the potential score of the contract against the optimal Par Score.
- **Play Analysis:** Tracks card-by-card changes in expected tricks and attributes points to the player.
- **Support:** Handles PBN and LIN files.
- **Output:** Generates a technical report in the console and a detailed Excel file with IMP attribution.
- **Web Interface:** Includes a FastAPI-based web UI for easy file uploading and analysis visualization.

## Installation
Ensure you have `uv` installed.
```bash
uv sync
```

## Usage
### CLI
Analyze a pair of PBN files (Open and Closed rooms):
```bash
uv run python main.py abierta.pbn cerrada.pbn
```

### Web Interface
Start the web server:
```bash
uv run python app.py
```
Then navigate to `http://localhost:8000`.

## Logic
- **Bidding Score:** `Actual Potential Score - Par Score`.
- **Play Score:** Sum of `Δ Expected Bridge Score` for each card played.
- **Actor Attribution:** Points are attributed to the player who played the card (declarer is responsible for dummy's cards).
