# Demo checklist

## Before the demo
- [ ] 3 demo scenarios cached (LLM cache `.cache/` or saved `report.json`), each runs without internet
- [ ] Backup screen recording of the full flow saved locally and on a second device/cloud drive
- [ ] AWS console login tested (account, MFA device available, region ap-south-1)
- [ ] Bedrock model access confirmed; `.env` populated (never shown on screen)
- [ ] `python run.py --mock` and `pytest -q` pass on the demo laptop

## Fallbacks
- [ ] Battery: laptop charged, charger packed
- [ ] Internet down: switch to cached scenarios / recording; phone hotspot as a second option
- [ ] Bedrock error or timeout: use cached report, say so openly

## Who speaks on which slide
| Slide | Speaker |
|---|---|
| TODO | TODO |
