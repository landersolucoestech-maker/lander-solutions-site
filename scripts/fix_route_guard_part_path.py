from pathlib import Path

root = Path(__file__).resolve().parents[1]
target = root / "scripts" / "test_crm_route_guards.py"
workflow = root / ".github" / "workflows" / "route-guard-path-fix.yml"
old = '"test_crm_economic_participations_ui.js.part03": 2,'
new = '"parts/tests/economic_participations/test_crm_economic_participations_ui.js.part03": 2,'
text = target.read_text(encoding="utf-8")
if old not in text:
    raise SystemExit("route guard legacy part path not found")
target.write_text(text.replace(old, new, 1), encoding="utf-8")
workflow.unlink(missing_ok=True)
Path(__file__).unlink(missing_ok=True)
print("route-guard-part-path: fixed")
