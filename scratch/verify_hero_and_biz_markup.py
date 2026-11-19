import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from streamlit.testing.v1 import AppTest

def verify():
    app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
    at = AppTest.from_file(app_path, default_timeout=30)
    at.run()
    assert not at.exception, f"App crashed on startup: {at.exception}"
    
    # 1. Verify DF Data Forge center circle
    found_hero = False
    found_top_left = False
    found_mid_right = False
    found_bot_right = False
    found_wrappers = False
    found_biz_context = False

    print(f"Current page: {at.session_state.get('page')}")
    print(f"Data status: {at.session_state.get('data_status')}")
    print(f"Number of markdown elements: {len(at.markdown)}")
    print(f"Number of html elements: {len(at.html)}")
    found_sat1 = False
    found_sat2 = False
    found_sat3 = False
    found_mini_cols = False

    for i, m in enumerate(at.markdown):
        val = str(m.value)
        if "DF" in val and "Data Force" in val:
            if "hero-circle" in val:
                found_hero = True
            if "orbit-sat sat-1" in val and "Auto-Clean" in val:
                found_sat1 = True
            if "orbit-sat sat-2" in val and "7 Audit Tests" in val:
                found_sat2 = True
            if "orbit-sat sat-3" in val and "HITL Guardrail" in val:
                found_sat3 = True
            if "mini-col mc-1" in val and "mini-col mc-2" in val and "mini-col mc-3" in val:
                found_mini_cols = True

    print(f"Hero circle found: {found_hero}")
    print(f"Satellite 1 (Auto-Clean): {found_sat1}")
    print(f"Satellite 2 (7 Audit Tests): {found_sat2}")
    print(f"Satellite 3 (HITL Guardrail): {found_sat3}")
    print(f"Mini-grid columns (mc-1, mc-2, mc-3): {found_mini_cols}")

    assert found_hero, "Hero circle missing"
    assert found_sat1, "Satellite 1 missing"
    assert found_sat2, "Satellite 2 missing"
    assert found_sat3, "Satellite 3 missing"
    assert found_mini_cols, "Mini-col columns missing"

    # Now navigate to Page 1: Kết Nối & Tải Dữ Liệu
    from app import PAGES
    at.session_state["nav_page"] = PAGES[1]
    at.run()

    found_biz_context = False
    for i, m in enumerate(at.markdown):
        val = str(m.value)
        if "Bối cảnh doanh nghiệp" in val and "<svg" in val:
            found_biz_context = True

    print(f"Bối cảnh doanh nghiệp with SVG found on Page 1: {found_biz_context}")
    assert found_biz_context, "Biz context with SVG missing on Page 1"

    # Check inputs for Biz context
    assert len(at.text_input) > 0, "Text inputs missing"
    biz_inputs = [i.label for i in at.text_input]
    print(f"Text inputs: {biz_inputs}")
    assert any("Loại hình doanh nghiệp" in label for label in biz_inputs), "Loại hình doanh nghiệp input missing"

    biz_textareas = [a.label for a in at.text_area]
    print(f"Text areas: {biz_textareas}")
    assert any("Thông tin bổ sung" in label for label in biz_textareas), "Thông tin bổ sung textarea missing"
    assert any("Vấn đề cần phân tích" in label for label in biz_textareas), "Vấn đề cần phân tích textarea missing"

    # Check consult button
    consult_btns = [b.label for b in at.button if "Trao đổi yêu cầu" in b.label]
    print(f"Consult buttons: {consult_btns}")
    assert len(consult_btns) > 0, "Consult button missing"

    print("\n>>> ALL HERO & BIZ CONTEXT MARKUP VERIFICATIONS PASSED 100%! <<<")

if __name__ == "__main__":
    verify()
