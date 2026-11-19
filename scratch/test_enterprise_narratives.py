import pandas as pd
from data_pipeline import (
    get_sample_marketing_data,
    get_messy_testcase_08_data,
    get_ecommerce_user_data,
    DataCleaner,
)
from analytics_engine import MarketingAnalyticsEngine, build_enterprise_report_narratives


def _assert_no_nan(narratives: dict, label: str):
    for k in [
        "block1_executive_mda",
        "block2_data_governance",
        "revenue_chart_html",
        "abc_cost_chart_html",
        "block4_internal_control",
        "block5_decision_matrix",
    ]:
        val = narratives.get(k, "")
        assert isinstance(val, str) and len(val) > 50, f"[{label}] Missing narrative block: {k}"
        low = val.lower()
        assert "nan đ" not in low and "nan%" not in low and "inf%" not in low, (
            f"[{label}] Found NaN/Inf in {k}: {val[:200]}"
        )


def test_standard_3tabs():
    tabs = get_sample_marketing_data()
    cleaner = DataCleaner(tabs)
    can_proc, norm, q_sum, _, excs = cleaner.clean_and_normalize()
    assert can_proc
    eng = MarketingAnalyticsEngine(norm, initial_exceptions=excs, return_window_days=30, quality_summary=q_sum)
    eng.run_process_workflow()
    for e in list(eng.exceptions_view):
        if e.get("Approval_Status") == "PENDING_REVIEW":
            eng.resolve_exception(e["Order_ID"], "APPROVED", "Trưởng phòng Marketing", "Vu Ruy Hoang", "Approved test")
    ver = eng.run_verification()
    narr = build_enterprise_report_narratives(
        eng.report_result, q_sum, eng.exceptions_view, ver, {"return_window_days": 30}, norm
    )
    _assert_no_nan(narr, "standard_3tabs")
    assert "Báo cáo Điều hành Tổng hợp" in narr["block1_executive_mda"]
    assert "Data Governance" in narr["block2_data_governance"]
    assert "Doanh thu" in narr["revenue_chart_html"]
    assert "Chi phí ABC" in narr["abc_cost_chart_html"]
    assert "Kiểm soát Nội bộ" in narr["block4_internal_control"]
    assert "KỊCH BẢN MỞ RỘNG ĐẦU TƯ" in narr["block5_decision_matrix"]
    html = eng.generate_html_report(quality_summary=q_sum)
    assert "Executive Management Summary" in html
    assert "Data Governance" in html
    assert "Executive Decision Matrix" in html


def test_all_profitable_and_zero_late_returns():
    # Edge case: 0 loss-making campaigns, 0 late returns, 0 division safety
    df_metrics = pd.DataFrame([
        {
            "Campaign_ID": "CMP-A",
            "Campaign_Name": "Google Search",
            "Channel": "Google",
            "Orders_Count": 10,
            "Attributed_Revenue": 10_000_000.0,
            "Attributed_COGS": 4_000_000.0,
            "Attributed_Return": 0.0,
            "Net_Sales": 10_000_000.0,
            "Direct_Cost": 1_000_000.0,
            "Allocated_Overhead": 500_000.0,
            "Cost_Driver": "Order_Volume",
            "Total_Cost": 1_500_000.0,
            "Net_Contribution": 4_500_000.0,
            "ROAS": 10_000_000.0 / 1_500_000.0,
            "ROI": 300.0,
            "Strategic_Decision": "SCALE",
        },
        {
            "Campaign_ID": "CMP-B",
            "Campaign_Name": "TikTok Ads",
            "Channel": "TikTok",
            "Orders_Count": 5,
            "Attributed_Revenue": 5_000_000.0,
            "Attributed_COGS": 2_000_000.0,
            "Attributed_Return": 0.0,
            "Net_Sales": 5_000_000.0,
            "Direct_Cost": 800_000.0,
            "Allocated_Overhead": 200_000.0,
            "Cost_Driver": "Revenue",
            "Total_Cost": 1_000_000.0,
            "Net_Contribution": 2_000_000.0,
            "ROAS": 5.0,
            "ROI": 200.0,
            "Strategic_Decision": "SCALE",
        },
    ])
    narr = build_enterprise_report_narratives(
        df_metrics,
        cleaning_report={"Data_Quality_Score": 98.5, "Missing_Fields_Count": 0, "Duplicate_Rows_Count": 0, "Auto_Fixed_Count": 1},
        exceptions_df=[],
        verification_results={"overall_status": "PASS", "tests": [{"status": "PASS"}] * 7},
        config={"return_window_days": 30, "total_orders": 15},
    )
    _assert_no_nan(narr, "all_profitable")
    assert "100% chiến dịch đều đạt lợi nhuận dương" in narr["abc_cost_chart_html"]
    assert "0 yêu cầu hoàn trả vượt hạn" in narr["block4_internal_control"]
    assert "Không có chiến dịch âm vốn" in narr["block4_internal_control"]


def test_ecommerce_and_general_tabular():
    tabs_ec = get_ecommerce_user_data()
    c_ec = DataCleaner(tabs_ec)
    ok_ec, norm_ec, q_ec, _, excs_ec = c_ec.clean_and_normalize()
    assert ok_ec
    eng_ec = MarketingAnalyticsEngine(norm_ec, initial_exceptions=excs_ec, quality_summary=q_ec)
    eng_ec.run_process_workflow()
    narr_ec = build_enterprise_report_narratives(eng_ec.report_result, q_ec, eng_ec.exceptions_view, None, None, norm_ec)
    _assert_no_nan(narr_ec, "ecommerce_no_costs")

    # GENERAL_TABULAR with zero numeric currency
    hr_df = pd.DataFrame({
        "Ma_NV": ["NV01", "NV02"],
        "Ho_Ten": ["Nguyen Van A", "Tran Thi B"],
        "Phong_Ban": ["KT", "IT"],
    })
    c_hr = DataCleaner({"NhanSu": hr_df})
    ok_hr, norm_hr, q_hr, _, excs_hr = c_hr.clean_and_normalize()
    assert ok_hr
    eng_hr = MarketingAnalyticsEngine(norm_hr, initial_exceptions=excs_hr, quality_summary=q_hr)
    eng_hr.run_process_workflow()
    narr_hr = build_enterprise_report_narratives(eng_hr.report_result, q_hr, eng_hr.exceptions_view, None, None, norm_hr)
    _assert_no_nan(narr_hr, "general_tabular")


if __name__ == "__main__":
    test_standard_3tabs()
    test_all_profitable_and_zero_late_returns()
    test_ecommerce_and_general_tabular()
    print("ALL ENTERPRISE NARRATIVE TESTS PASSED (3/3 SCENARIOS)!")
