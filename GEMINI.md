# Bridge Match Analyzer

## Goal
Build a Python-based Bridge match analyzer that evaluates 8 players' performance (typically across two tables) in bidding and play by comparing their actions against a Double Dummy Solver (DDS).

## Architecture & Scoring
- **Bidding Scoring:** Difference between the Actual Score of the contract and the optimal Par Score for the board.
- **Play Scoring:** Change in expected Bridge Score for each card played, attributed to the actor.
- **Library:** Uses `endplay` for PBN/LIN parsing and DDS integration.
- **Environment:** Python managed via `uv`.

## History of Actions
1. **Research & Planning:** Identified `endplay` as the core library. Designed the scoring algorithms for bidding (Actual - Par) and play (card-by-card DDS tracking).
2. **Environment Setup:** Initialized the project folder `bridge-analyzer/` and installed dependencies (`endplay`, `tabulate`).
3. **Core Implementation:**
   - Created `main.py` with the `BridgeAnalyzer` class.
   - Implemented PBN/LIN parsing and 8-player result aggregation.
   - Developed `_analyze_bidding` to compare results with `dds.par`.
   - Developed `_analyze_play` using `dds.solve` to track expected trick changes per card.
4. **Debugging & Refinement:**
   - Corrected `endplay` API imports and usage (e.g., `dds.par` instead of `calc_par`).
   - Resolved `Board` vs `Deal` object mismatches in the parser output.
   - Implemented `contract.score()` for precise bridge scoring calculation.
   - Created `test_match.pbn` for validation.

## Current State
- The analyzer is largely implemented but requires final verification of the play attribution logic (actor tracking and point signs).
- The `endplay` library's `d.play()` and hand tracking require careful handling as seen in recent debug sessions.

## Next Steps
- Finalize the `_analyze_play` logic to ensure robust actor tracking even in complex trick scenarios.
- Verify the 8-player table output with the `test_match.pbn` file.
- Add support for LIN files if not already fully validated.
