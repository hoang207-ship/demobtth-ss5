import io
import time
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
from streamlit.testing.v1 import AppTest

from data_pipeline import (
    MAX_ROW_LIMIT,
    DataCleaner,
    get_sample_marketing_data,
    get_ecommerce_user_data,
)
from analytics_engine import MarketingAnalyticsEngine


def test_1_native_i18n_and_notranslate():
    with open("app.py", "r", encoding="utf-8") as f:
        app_src = f.read()
    assert '<meta name="google" content="notranslate">' in app_src
    assert 'translate="no"' in app_src
    assert ("Data Forge — Hệ thống Phân tích & Kiểm toán Dữ liệu Doanh nghiệp" in app_src or "GROWTHMETRIC — Hệ thống Phân tích & Kiểm toán Dữ liệu Doanh nghiệp" in app_src)
    assert "Hồ sơ chờ phê duyệt (HITL)" in app_src
    assert "Xuất Báo cáo Quản trị (Reports & Export)" in app_src
    assert "Cấu hình Hệ thống & Định mức (Settings)" in app_src

    tabs = get_sample_marketing_data()
    cleaner = DataCleaner(tabs)
    _, norm, q_sum, _, excs = cleaner.clean_and_normalize()
    eng = MarketingAnalyticsEngine(norm, excs, quality_summary=q_sum)
    eng.run_process_workflow()
    html_rep = eng.generate_html_report(quality_summary=q_sum)
    assert '<meta name="google" content="notranslate">' in html_rep
    assert 'translate="no"' in html_rep
    print("[PASS] Test 1: Chặn dịch máy (notranslate) & chuẩn hóa thuật ngữ Enterprise I18N")


def test_2_quota_guardrail_20001_rows():
    assert MAX_ROW_LIMIT == 20000
    n_rows = 20001
    df_big = pd.DataFrame({
        "Order_ID": [f"ORD-{i+1:05d}" for i in range(n_rows)],
        "Order_Date": ["2026-06-01"] * n_rows,
        "Order_Value": [100000] * n_rows,
        "Campaign_List": ["PG01"] * n_rows,
        "Channel": ["Shopee"] * n_rows,
    })

    t0 = time.time()
    cleaner = DataCleaner({"22_vuot_20001_dong": df_big})
    can_proc, norm, q_sum, errs, excs = cleaner.clean_and_normalize()
    elapsed = time.time() - t0
    assert elapsed < 10.0, f"Xử lý 20,001 dòng quá chậm: {elapsed:.2f}s"

    assert can_proc is True
    assert q_sum["Quota_Exceeded"] is True
    assert q_sum["Raw_Transactions_Count"] == 20001
    assert q_sum["Max_Row_Limit"] == 20000
    assert q_sum["Excess_Rows_Count"] == 1
    assert q_sum["Quarantined_Rows_Count"] == 1
    assert q_sum["Status"] == "QUOTA_WARNING", f"Không được SUCCESS âm thầm, thực tế: {q_sum['Status']}"
    assert "CẢNH BÁO QUOTA (20,001 / 20,000 dòng)" in q_sum["Quota_Status_Text"]
    assert q_sum["Data_Quality_Score"] < 100.0
    assert len(norm["Normalized_Transactions"]) == 20000
    assert len(norm["Quarantined_Records"]) == 1
    assert any(e["Error_Type"] == "QUOTA_EXCEEDED_QUARANTINE" for e in excs)

    # Chế độ 1: Tự động cắt ngọn & Đẩy dòng dư sang Exceptions (đã APPROVED tự động)
    c_trunc = DataCleaner({"22_vuot_20001_dong": df_big}, quota_policy="TRUNCATE_TO_QUOTA")
    _, norm_t, q_t, _, excs_t = c_trunc.clean_and_normalize()
    assert len(norm_t["Normalized_Transactions"]) == 20000
    assert len(norm_t["Quarantined_Records"]) == 1
    q_excs_t = [e for e in excs_t if e["Error_Type"] == "QUOTA_EXCEEDED_QUARANTINE"]
    assert len(q_excs_t) == 1 and q_excs_t[0]["Approval_Status"] == "APPROVED"

    # Chế độ 2: Cho phép xử lý ngoại lệ toàn bộ 20,001 dòng
    c_allow = DataCleaner({"22_vuot_20001_dong": df_big}, quota_policy="ALLOW_ALL_ROWS")
    _, norm_a, q_a, _, excs_a = c_allow.clean_and_normalize()
    assert len(norm_a["Normalized_Transactions"]) == 20001
    assert len(norm_a["Quarantined_Records"]) == 0
    assert q_a["Status"] == "QUOTA_WARNING"
    assert any(e["Error_Type"] == "QUOTA_OVERRIDE_APPROVED" and e["Approval_Status"] == "APPROVED" for e in excs_a)

    print(f"[PASS] Test 2: Quota Guardrail 20,001 dòng ({elapsed:.2f}s) — QUOTA_WARNING, Quarantine=1, Truncate & AllowAll OK")


def test_3_4_and_5_waterfall_whatif_excel_and_ui():
    # Kiểm tra Waterfall Chart & What-If & Excel 5 sheet qua AppTest & trực tiếp
    tabs = get_sample_marketing_data()
    cleaner = DataCleaner(tabs)
    _, norm, q_sum, errs, excs = cleaner.clean_and_normalize()
    eng = MarketingAnalyticsEngine(norm, excs, quality_summary=q_sum)
    eng.run_process_workflow()
    for e in list(eng.exceptions_view):
        if e.get("Approval_Status") == "PENDING_REVIEW":
            eng.resolve_exception(e["Order_ID"], "APPROVED", "Trưởng phòng Marketing", "Admin", "OK test")
    ver = eng.run_verification()
    assert ver["overall_status"] == "PASS"

    # Test 5: Export Audit Excel Pack (5 sheets)
    xlsx_bytes = eng.generate_enterprise_audit_excel_pack(
        quality_summary=q_sum,
        cleaning_errors=errs,
        audit_log=cleaner.audit_log,
        reconciliation_table=cleaner.reconciliation_table,
    )
    xl = pd.ExcelFile(io.BytesIO(xlsx_bytes))
    expected_sheets = [
        "01_Executive_Summary",
        "02_Campaign_P&L_ABC",
        "03_Cleaned_Data_Sample",
        "04_Quarantine_&_Exceptions",
        "05_System_Audit_Log",
    ]
    assert xl.sheet_names == expected_sheets, f"Sheet mismatch: {xl.sheet_names}"
    print(f"[PASS] Test 5: Enterprise Audit Excel Pack ({len(xlsx_bytes):,} bytes) đủ 5 sheets: {xl.sheet_names}")

    # Test 3 & 4 trên AppTest (bao gồm cả Single-Table Audit Mode với ecom và Multi-Table với std)
    at = AppTest.from_file("../app.py", default_timeout=60).run()
    assert not at.exception, at.exception

    # Single-table Audit Mode (ecom)
    at.button(key="qs_ecom").click().run()
    at.button(key="ov_run_all").click().run()
    assert not at.exception, at.exception
    info_msgs = "\n".join(i.value for i in at.info)
    assert "Single-Table Audit Mode" in info_msgs, f"Thiếu cảnh báo Single-Table Audit Mode: {info_msgs}"
    exp_labels = [e.label for e in at.expander]
    assert any("What-If Simulator" in lb for lb in exp_labels), f"Thiếu What-If Simulator expander: {exp_labels}"
    print("[PASS] Test 3 & 4 (UI Single-Table Waterfall + What-If Simulator)")

    # Reset & kiểm tra Multi-table (std) + trang Xuất Báo cáo Quản trị (Reports & Export)
    at.radio(key="nav_page").set_value("Cấu hình Hệ thống & Định mức (Settings)").run()
    at.button(key="btn_reset").click().run()
    at.radio(key="nav_page").set_value("Overview (Tổng quan)").run()
    at.button(key="qs_std").click().run()
    at.button(key="ov_run_all").click().run()
    assert not at.exception, at.exception

    # Duyệt toàn bộ ngoại lệ HITL
    at.radio(key="nav_page").set_value("Phê Duyệt Exceptions").run()
    for _ in range(15):
        pend = [e for e in at.session_state["exceptions_list"] if e.get("Approval_Status") == "PENDING_REVIEW"]
        if not pend:
            break
        at.text_area[0].input("Chấp thuận kiểm toán")
        [b for b in at.button if "Xác nhận" in str(b.label)][0].click().run()
    at.radio(key="nav_page").set_value("Verification Suite").run()
    at.button(key="btn_verify").click().run()
    assert at.session_state["verification_status"] == "PASS"

    at.radio(key="nav_page").set_value("Xuất Báo cáo Quản trị (Reports & Export)").run()
    assert not at.exception, at.exception
    print("[PASS] Test 5 (UI Reports & Export page HTML + Excel Pack + What-If Simulator)")


if __name__ == "__main__":
    test_1_native_i18n_and_notranslate()
    test_2_quota_guardrail_20001_rows()
    test_3_4_and_5_waterfall_whatif_excel_and_ui()
    print("\nALL 5 ENTERPRISE SAAS UPGRADE TESTS PASSED 100%!")
