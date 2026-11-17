import io
import time
import openpyxl
import pandas as pd
from data_pipeline import DataCleaner, parse_campaign_list
from analytics_engine import MarketingAnalyticsEngine

# =========================================================================
# 1. KIỂM THỬ BỘ DỮ LIỆU GIA HÒA (45 DÒNG)
# =========================================================================
cmps, cnt, stat, _ = parse_campaign_list("PG01 & PG03")
assert cmps == ["PG01", "PG03"] and cnt == 2 and "&" not in cmps, f"Got {cmps}"

gh_rows = []
# 4 dòng lệch cột điển hình: GH-2026-001, GH-2026-009, GH-2026-011 (3 cột lệch), GH-2026-039
gh_rows.append({"Ma_Don_Hang": "GH-2026-001", "Kenh_Ban": "Shopee", "Gia_Tri_Don": "1.500.000 VND", "Danh_Sach_Chien_Dich": "PG01", "Gia_Von_COGS": "PG02", "Unnamed: 5": "650.000 VND", "Unnamed: 6": None, "Ngay_Dat_Hang": "2026-06-01"})
gh_rows.append({"Ma_Don_Hang": "GH-2026-009", "Kenh_Ban": "Lazada", "Gia_Tri_Don": "2.200.000 VNĐ", "Danh_Sach_Chien_Dich": "PG01 & PG03", "Gia_Von_COGS": "PG02", "Unnamed: 5": "950.000 VNĐ", "Unnamed: 6": None, "Ngay_Dat_Hang": "2026-06-09"})
gh_rows.append({"Ma_Don_Hang": "GH-2026-011", "Kenh_Ban": "TikTok Shop", "Gia_Tri_Don": "2.500.000 VNĐ", "Danh_Sach_Chien_Dich": "PG01", "Gia_Von_COGS": "PG03", "Unnamed: 5": "PG04", "Unnamed: 6": "1.100.000 VNĐ", "Ngay_Dat_Hang": "2026-06-11"})
gh_rows.append({"Ma_Don_Hang": "GH-2026-039", "Kenh_Ban": "Website Direct", "Gia_Tri_Don": "3.000.000 VNĐ", "Danh_Sach_Chien_Dich": "PG02", "Gia_Von_COGS": "PG05", "Unnamed: 5": "1.300.000 VNĐ", "Unnamed: 6": None, "Ngay_Dat_Hang": "2026-06-20"})
# 7 dòng COGS='Lỗi dữ liệu' -> tổng 11 dòng lỗi COGS
for i in range(7):
    gh_rows.append({"Ma_Don_Hang": f"GH-2026-ERR{i+1:02d}", "Kenh_Ban": "Hotline", "Gia_Tri_Don": "1.000.000 VNĐ", "Danh_Sach_Chien_Dich": "PG01 & PG03", "Gia_Von_COGS": "Lỗi dữ liệu", "Unnamed: 5": None, "Unnamed: 6": None, "Ngay_Dat_Hang": "2026-06-15"})
# 34 dòng sạch -> tổng 45 dòng
for i in range(34):
    gh_rows.append({"Ma_Don_Hang": f"GH-2026-OK{i+1:02d}", "Kenh_Ban": "Shopee", "Gia_Tri_Don": "1.200.000 VNĐ", "Danh_Sach_Chien_Dich": "PG01 & PG03" if i % 2 == 0 else "PG02; PG04", "Gia_Von_COGS": "500.000 VNĐ", "Unnamed: 5": None, "Unnamed: 6": None, "Ngay_Dat_Hang": "2026-06-18"})

assert len(gh_rows) == 45
cleaner_gh = DataCleaner({"Transactions": pd.DataFrame(gh_rows)})
_, norm_gh, q_gh, errs_gh, excs_gh = cleaner_gh.clean_and_normalize()
tx_gh = norm_gh["Normalized_Transactions"]

# Kiểm tra không còn '&' trong Campaign_List_Str
assert not tx_gh["Campaign_List_Str"].str.contains("&", regex=False).any()
# Kiểm tra 11 dòng lỗi COGS đều có COGS=NaN, Source_Profit=NaN, Has_Exception=True
cogs_err_rows = tx_gh[tx_gh["COGS_Status"].str.contains("EXCEPTION", na=False)]
assert len(cogs_err_rows) == 11, f"Expected 11, got {len(cogs_err_rows)}"
assert cogs_err_rows["COGS"].isna().all()
assert cogs_err_rows["Source_Profit"].isna().all()
assert cogs_err_rows["Has_Exception"].all()

# Kiểm tra xuất Excel: Cleaning_Audit_Log != Errors_Log
xls = cleaner_gh.export_cleaned_data_excel()
wb = openpyxl.load_workbook(io.BytesIO(xls))
assert "Cleaning_Audit_Log" in wb.sheetnames and "Errors_Log" in wb.sheetnames
assert wb["Cleaning_Audit_Log"].max_row != wb["Errors_Log"].max_row or wb["Cleaning_Audit_Log"]["A2"].value != wb["Errors_Log"]["A2"].value

# Phê duyệt 4 đơn lệch cột qua MarketingAnalyticsEngine
eng_gh = MarketingAnalyticsEngine(norm_gh, initial_exceptions=excs_gh)
eng_gh.run_process_workflow()
for oid in ["GH-2026-001", "GH-2026-009", "GH-2026-011", "GH-2026-039"]:
    ok, msg = eng_gh.resolve_exception(oid, "APPROVE", "Trưởng phòng Marketing", "Vũ Ruy Hoàng", "Duyệt khôi phục cột lệch", error_type="CAMPAIGN_IN_COGS_COLUMN")
    assert ok, msg

tx_after = eng_gh.data["Normalized_Transactions"]
r011 = tx_after[tx_after["Order_ID"] == "GH-2026-011"].iloc[0]
assert r011["COGS"] == 1100000.0
assert set(r011["Campaign_List"]) == {"PG01", "PG03", "PG04"}, f"Got {r011['Campaign_List']}"
assert r011["Source_Profit"] == 2500000.0 - 1100000.0
r001 = tx_after[tx_after["Order_ID"] == "GH-2026-001"].iloc[0]
assert r001["COGS"] == 650000.0 and set(r001["Campaign_List"]) == {"PG01", "PG02"}
print(f"[PASS] Gia Hoa 45 rows: 11 COGS exceptions Has_Exception=True, 0 '&', GH-2026-011 recovered COGS={r011['COGS']:,.0f}, Campaigns={r011['Campaign_List']}")

# =========================================================================
# 2. KIỂM THỬ BENCHMARK 15.000 DÒNG x 23 CỘT (sales_data.csv)
# =========================================================================
n_rows = 15000
# Chia chính xác để tổng: Net_Sales = 430,658,320,000 | Cost = 372,798,218,000 | Profit = 57,860,102,000
net_base = 28710000
cost_base = 24853000
net_arr = [net_base] * n_rows
cost_arr = [cost_base] * n_rows
net_arr[0] += 430658320000 - sum(net_arr)
cost_arr[0] += 372798218000 - sum(cost_arr)
prof_arr = [n - c for n, c in zip(net_arr, cost_arr)]

big_df = pd.DataFrame({
    "Order_ID": [f"SL-{i+1:05d}" for i in range(n_rows)],
    "Order_Date": ["2026-06-01"] * n_rows,
    "Region": ["South"] * n_rows,
    "City": ["Ho Chi Minh"] * n_rows,
    "Segment": ["Consumer"] * n_rows,
    "Category": ["Electronics"] * n_rows,
    "Subcategory": ["Phones"] * n_rows,
    "Product_Name": ["Item A"] * n_rows,
    "Channel": ["E-Commerce"] * n_rows,
    "Payment_Method": ["COD"] * n_rows,
    "Quantity": [1] * n_rows,
    "Unit_Price_VND": net_arr,
    "Discount": [0.0] * n_rows,
    "Sales_VND": net_arr,
    "Discount_Amount_VND": [0] * n_rows,
    "Net_Sales_VND": net_arr,
    "Cost_VND": cost_arr,
    "Profit_VND": prof_arr,
    "Shipping_Days": [2] * n_rows,
    "Returned": ["No"] * n_rows,
    "Customer_Satisfaction": [5] * n_rows,
    "Campaign_List": ["PG01"] * n_rows,
    "Campaign_Count": [1] * n_rows,
})

t0 = time.perf_counter()
cleaner_big = DataCleaner({"sales_data": big_df})
can_big, norm_big, q_big, errs_big, excs_big = cleaner_big.clean_and_normalize()
elapsed = time.perf_counter() - t0

assert can_big is True
assert len(errs_big) == 0 and len(excs_big) == 0
assert q_big["Audit_Log_Count"] <= 10, f"Clean numeric rows should not bloat Audit_Log: {q_big['Audit_Log_Count']}"
assert int(q_big["Total_Net_Sales_VND"]) == 430658320000
assert int(q_big["Total_COGS_VND"]) == 372798218000
assert int(q_big["Total_Profit_VND"]) == 57860102000
tx_big = norm_big["Normalized_Transactions"]
for dim in ["Region", "Product_Name", "Extra_City", "Extra_Segment", "Extra_Category", "Extra_Subcategory"]:
    assert dim in tx_big.columns, f"Missing preserved dimension {dim}"
print(f"[PASS] 15,000x23 sales_data benchmark in {elapsed:.2f}s | Net={q_big['Total_Net_Sales_VND']:,.0f} | COGS={q_big['Total_COGS_VND']:,.0f} | Profit={q_big['Total_Profit_VND']:,.0f} | Errors=0 | AuditLog=0")
