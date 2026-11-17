import pandas as pd
from data_pipeline import DataCleaner, get_messy_testcase_08_data
from analytics_engine import MarketingAnalyticsEngine

# 1. Kiểm thử get_messy_testcase_08_data()
messy = get_messy_testcase_08_data()
c1 = DataCleaner(messy)
can1, norm1, q1, err1, exc1 = c1.clean_and_normalize()
assert can1 is True, f"Expected can_proceed=True, got {can1}"
assert q1["Status"] == "NEEDS_APPROVAL", f"Expected NEEDS_APPROVAL, got {q1['Status']}"
missing_excs = [e for e in exc1 if e["Error_Type"] == "MISSING_ORDER_ID"]
assert len(missing_excs) == 1 and missing_excs[0]["Severity"] == "HIGH"

eng1 = MarketingAnalyticsEngine(norm1, initial_exceptions=exc1)
res1 = eng1.run_process_workflow()
assert res1["status"] == "COMPLETED"
for e in list(eng1.exceptions_view):
    if e.get("Approval_Status") == "PENDING_REVIEW":
        act = "REJECT" if str(e["Order_ID"]).startswith("TEMP-UNKNOWN-") else "APPROVE"
        ok, msg = eng1.resolve_exception(e["Order_ID"], act, "Trưởng phòng Marketing", "Vũ Ruy Hoàng", "Xử lý HITL", error_type=e["Error_Type"])
        assert ok, msg
ver1 = eng1.run_verification()
assert ver1["overall_status"] == "PASS", f"Verification failed: {ver1}"
print(f"[PASS] Messy TestCase_08: Status={q1['Status']}, Process={res1['status']}, Verification={ver1['overall_status']}")

# 2. Kiểm thử kịch bản 52 dòng có dòng trống Order_ID (TEMP-UNKNOWN-...) với REJECTED & CORRECTION_REQUESTED
rows_52 = [
    {"Ma_Don_Hang": f"GH-{i+1:03d}", "Gia_Tri_Don": 1000000, "Danh_Sach_Chien_Dich": "PG01", "Gia_Von_COGS": 400000}
    for i in range(49)
]
rows_52.append({"Ma_Don_Hang": "", "Gia_Tri_Don": 500000, "Danh_Sach_Chien_Dich": "PG01", "Gia_Von_COGS": 200000})  # TEMP-UNKNOWN-50 -> REJECT
rows_52.append({"Ma_Don_Hang": None, "Gia_Tri_Don": 300000, "Danh_Sach_Chien_Dich": "PG02", "Gia_Von_COGS": 100000})  # TEMP-UNKNOWN-51 -> CORRECTION_REQUESTED
rows_52.append({"Ma_Don_Hang": "", "Gia_Tri_Don": 200000, "Danh_Sach_Chien_Dich": "PG02", "Gia_Von_COGS": 80000})  # TEMP-UNKNOWN-52 -> APPROVE

c52 = DataCleaner({"Transactions": pd.DataFrame(rows_52)})
can52, norm52, q52, err52, exc52 = c52.clean_and_normalize()
assert can52 is True and q52["Status"] == "NEEDS_APPROVAL"
assert len([e for e in exc52 if e["Error_Type"] == "MISSING_ORDER_ID"]) == 3

eng52 = MarketingAnalyticsEngine(norm52, initial_exceptions=exc52)
res52 = eng52.run_process_workflow()
assert res52["status"] == "COMPLETED"

ok, _ = eng52.resolve_exception("TEMP-UNKNOWN-50", "REJECT", "Trưởng phòng Marketing", "Vũ Ruy Hoàng", "Loại đơn thiếu mã")
assert ok
ok, _ = eng52.resolve_exception("TEMP-UNKNOWN-51", "REQUEST_CORRECTION", "Trưởng phòng Marketing", "Vũ Ruy Hoàng", "Yêu cầu bổ sung mã đơn")
assert ok
ok, _ = eng52.resolve_exception("TEMP-UNKNOWN-52", "APPROVE", "Trưởng phòng Marketing", "Vũ Ruy Hoàng", "Đã xác nhận chứng từ")
assert ok

# Tổng doanh thu phân bổ phải loại trừ TEMP-UNKNOWN-50 (500k) và TEMP-UNKNOWN-51 (300k), chỉ còn 49*1M + 200k = 49,200,000
total_attr = eng52.detailed_attributed_df["Attributed_Revenue"].sum()
assert total_attr == 49200000.0, f"Expected 49,200,000, got {total_attr}"
ver52 = eng52.run_verification()
assert ver52["overall_status"] == "PASS", f"Expected PASS, got {ver52}"
print(f"[PASS] 52-row HITL: Status={q52['Status']}, Attributed={total_attr:,.0f} đ (excluded REJECTED & CORRECTION_REQUESTED), Verification={ver52['overall_status']}")

