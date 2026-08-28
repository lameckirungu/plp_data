from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def test_bundled_demo_app_smoke():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    assert not app.exception
    assert app.title[0].value.endswith("PumpGuard Ops")
    assert any("Prioritized maintenance queue" in header.value for header in app.subheader)
