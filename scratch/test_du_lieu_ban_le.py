import pandas as pd
from schema_mapper import AutoSchemaMapper
from data_pipeline import DataCleaner
from analytics_engine import MarketingAnalyticsEngine

# 1. Kiểm tra ánh xạ các cột tiếng Việt của du-lieu-test-ban-le.csv
cols = [
    "Mã dòng", "Tháng", "Khu vực", "Kênh bán", "Sản phẩm",
    "Số đơn", "Doanh thu (VNĐ)", "Chi phí giá vốn", "Lợi nhuận gộp"
]
m = AutoSchemaMapper().map_columns(cols)
assert m["mapped_dict"]["Tháng"] == "Order_Date", m["mapped_dict"]
assert m["mapped_dict"]["Sản phẩm"] == "Product_Name", m["mapped_dict"]
assert m["mapped_dict"]["Khu vực"] == "Region", m["mapped_dict"]
assert m["mapped_dict"]["Số đơn"] == "Quantity", m["mapped_dict"]
assert m["mapped_dict"]["Mã dòng"] == "Order_ID", m["mapped_dict"]
assert m["mapped_dict"]["Doanh thu (VNĐ)"] == "Order_Value", m["mapped_dict"]
assert m["mapped_dict"]["Chi phí giá vốn"] == "COGS", m["mapped_dict"]
assert m["mapped_dict"]["Lợi nhuận gộp"] == "Source_Profit", m["mapped_dict"]
print("[PASS] Schema_Mapping_Table:", m["mapped_dict"])

# 2. Tạo bộ dữ liệu 52 dòng mô phỏng du-lieu-test-ban-le.csv:
#    - 48 dòng duy nhất tổng: Net=1,135,530,000 | COGS=603,680,000 | Profit=531,850,000
#    - Kênh bán: Website 40.0% (454,212,000), Sàn TMĐT 32.4% (367,911,720), Cửa hàng 27.6% (313,406,280)
#    - 2 bản sao trùng lặp: DS-008 và DS-043
#    - 2 dòng trắng hoàn toàn -> tổng 52 dòng
products = ["Sơ mi", "Quần jeans", "Áo thun", "Túi tote"]
regions = ["Miền Bắc", "Miền Trung", "Miền Nam"]
months = ["2026-07", "2026-08", "2026-09", "2026-10"]
channels = ["Website"] * 19 + ["Sàn thương mại điện tử"] * 16 + ["Cửa hàng"] * 13

target_ch_rev = {
    "Website": 454212000,               # 40.0%
    "Sàn thương mại điện tử": 367911720, # 32.4%
    "Cửa hàng": 313406280,              # 27.6%
}
target_cogs = 603680000

rows = []
ch_counts = {"Website": 19, "Sàn thương mại điện tử": 16, "Cửa hàng": 13}
ch_idx = {"Website": 0, "Sàn thương mại điện tử": 0, "Cửa hàng": 0}
cogs_each = target_cogs // 48
cogs_rem = target_cogs - cogs_each * 48

for i in range(48):
    ch = channels[i]
    cnt = ch_counts[ch]
    base_rev = target_ch_rev[ch] // cnt
    rem_rev = target_ch_rev[ch] - base_rev * cnt
    rev = base_rev + (rem_rev if ch_idx[ch] == 0 else 0)
    ch_idx[ch] += 1
    cg = cogs_each + (cogs_rem if i == 0 else 0)
    rows.append({
        "Mã dòng": f"DS-{i+1:03d}",
        "Tháng": months[i % 4],
        "Khu vực": regions[i % 3],
        "Kênh bán": ch,
        "Sản phẩm": products[i % 4],
        "Số đơn": 5 + (i % 4),
        "Doanh thu (VNĐ)": rev,
        "Chi phí giá vốn": cg,
        "Lợi nhuận gộp": rev - cg,
    })

# Chèn 2 dòng trắng hoàn toàn và 2 bản sao trùng lặp DS-008, DS-043 -> tổng 52 dòng
rows.insert(10, {"Mã dòng": "", "Tháng": "", "Khu vực": "", "Kênh bán": "", "Sản phẩm": "", "Số đơn": None, "Doanh thu (VNĐ)": None, "Chi phí giá vốn": None, "Lợi nhuận gộp": None})
rows.insert(25, {"Mã dòng": None, "Tháng": None, "Khu vực": None, "Kênh bán": None, "Sản phẩm": None, "Số đơn": None, "Doanh thu (VNĐ)": None, "Chi phí giá vốn": None, "Lợi nhuận gộp": None})
rows.append(dict(rows[7]))   # bản sao DS-008
rows.append(dict(rows[44]))  # bản sao DS-043
assert len(rows) == 52

cleaner = DataCleaner({"du-lieu-test-ban-le": pd.DataFrame(rows)})
can_proc, norm_data, q_sum, errs, excs = cleaner.clean_and_normalize()
tx = norm_data["Normalized_Transactions"]

assert can_proc is True
assert len(tx) == 50, f"Phải bỏ 2 dòng trắng, còn 50 dòng (48 gốc + 2 trùng), thực tế: {len(tx)}"
assert len(excs) == 2 and {e["Order_ID"] for e in excs} == {"DS-008", "DS-043"}, excs
assert not any(e["Error_Type"] == "MISSING_ORDER_ID" for e in excs)
assert not any(e["Error_Type"] == "EXCEPTION_INVALID_DATE" for e in errs)
print(f"[PASS] Cleaning: 52 raw -> {len(tx)} normalized (skipped 2 empty rows), 2 duplicate exceptions: {[e['Order_ID'] for e in excs]}")

# 3. Chạy Process 6 bước & từ chối 2 bản sao trùng lặp DS-008, DS-043
eng = MarketingAnalyticsEngine(norm_data, initial_exceptions=excs)
res = eng.run_process_workflow()
assert res["status"] == "COMPLETED"

for oid in ["DS-008", "DS-043"]:
    ok, msg = eng.resolve_exception(oid, "REJECT", "Trưởng phòng Marketing", "Vũ Ruy Hoàng", "Loại bản sao trùng lặp", error_type="DUPLICATE_ORDER_ID")
    assert ok, msg

active = eng.get_active_transactions_df()
assert len(active) == 48, f"Expected 48 unique rows, got {len(active)}"
net_sum = active["Order_Value"].sum()
cogs_sum = active["COGS"].sum()
prof_sum = active["Source_Profit"].sum()
assert net_sum == 1135530000.0
assert cogs_sum == 603680000.0
assert prof_sum == 531850000.0

ver = eng.run_verification()
assert ver["overall_status"] == "PASS", ver
print(f"[PASS] After REJECT duplicates: Active={len(active)} rows | Net Sales={net_sum:,.0f} đ | COGS={cogs_sum:,.0f} đ | Profit={prof_sum:,.0f} đ | Verification={ver['overall_status']}")

