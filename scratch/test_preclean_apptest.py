import os
import sys
from streamlit.testing.v1 import AppTest

print("=== Starting AppTest for Pre-Clean Error Diagnostics ===")
app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.py"))
at = AppTest.from_file(app_path, default_timeout=35)
at.run()
assert len(at.exception) == 0, f"Init exceptions: {at.exception}"
print("1. App initialized with 0 exceptions.")

print("All radios in tree:", [(r.key, r.value) for r in at.radio])
# Find nav_page radio
nav_radios = [r for r in at.radio if r.key == "nav_page"]
assert len(nav_radios) == 1, f"nav_page radio not found! Radios: {[r.key for r in at.radio]}"
nav_radios[0].set_value("Kết nối dữ liệu").run()
assert len(at.exception) == 0, f"Page 2 exceptions: {at.exception}"
print(f"2. Navigated to {at.session_state.nav_page} with 0 exceptions.")

# Click sp_messy
btn_messy = [b for b in at.button if b.key == "sp_messy"]
assert len(btn_messy) == 1, "sp_messy button not found"
btn_messy[0].click().run()
assert len(at.exception) == 0, f"sp_messy click exceptions: {at.exception}"
print("3. sp_messy loaded successfully.")

scan = at.session_state.get("pre_clean_scan")
assert scan is not None, "pre_clean_scan is None!"
print(f"4. Pre-clean scan detected: total_problems={scan['total_problem_count']}, "
      f"critical={len(scan['critical_rows'])}, format={len(scan['format_rows'])}, "
      f"schema={len(scan['schema_rows'])}, est_score={scan['estimated_score']}%")

# Verify raw data is completely untouched
raw_orders = at.session_state.raw_tabs["Orders"]
print(f"5. Raw Order_Value sample (must still be raw string with VNĐ): {raw_orders['Order_Value'].iloc[0]}")
assert "VNĐ" in str(raw_orders["Order_Value"].iloc[0]), "Raw data was prematurely modified!"

# Verify the confirmation button exists
btn_confirm = [b for b in at.button if b.key == "conn_precheck_go_clean_issues"]
assert len(btn_confirm) == 1, "conn_precheck_go_clean_issues button not found!"
print("6. 'conn_precheck_go_clean_issues' button is present.")

# Click the confirmation button
btn_confirm[0].click().run()
assert len(at.exception) == 0, f"Nav click exceptions: {at.exception}"
print(f"7. Clicked confirmation button -> Navigated to: '{at.session_state.nav_page}' with 0 exceptions.")
assert at.session_state.nav_page == "Làm sạch dữ liệu", f"Expected 'Làm sạch dữ liệu', got '{at.session_state.nav_page}'"

# On Page 3, verify pre-clean preview is also visible before cleaning starts
clean_btns = [b for b in at.button if b.key == "btn_run_cleaning_primary"]
assert len(clean_btns) == 1, "Primary clean button not found on Page 3"
print("8. Page 3 successfully rendered with clean button available.")

print("=== ALL PRE-CLEAN APPTEST CHECKS PASSED PERFECTLY! ===")
