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
5. **Final Verification & Robustness:**
   - Verified play attribution logic (signs and actor tracking) with empirical tests.
   - Refactored `export_to_excel` to dynamically handle any room name and prevent crashes.
   - Validated LIN file support through synthetic test cases.
   - Confirmed 8-player output consistency across rooms.

## Current State
- The analyzer is fully functional and verified.
- Bidding and play scoring are aligned with standard Duplicate Bridge rules.
- Support for PBN and LIN files is robust.
- Web interface (`app.py`) is ready for deployment.

## Next Steps
- Implement a batch processing feature for multiple matches.
- Enhance the UI with more interactive charts for performance over time.
- Consider adding support for more complex scoring variants (e.g. board-a-match).
