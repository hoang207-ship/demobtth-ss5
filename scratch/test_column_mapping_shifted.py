import pandas as pd
from data_pipeline import DataCleaner

raw_rows = [
    {"Ma_Don_Hang": "GH-2026-001", "Kenh_Ban": "Shopee", "Gia_Tri_Don": "1.500.000 VND", "Danh_Sach_Chien_Dich": "PG01", "Gia_Von_COGS": "PG02", "Unnamed: 5": "650.000 VND", "Ngay_Dat_Hang": "2026-06-01"},
    {"Ma_Don_Hang": "GH-2026-002", "Kenh_Ban": "Website Direct", "Gia_Tri_Don": "2.5 triệu", "Danh_Sach_Chien_Dich": "PG02; PG03", "Gia_Von_COGS": "1.1 triệu", "Unnamed: 5": None, "Ngay_Dat_Hang": "02/06/2026"},
    {"Ma_Don_Hang": "GH-2026-003", "Kenh_Ban": "TikTok Shop", "Gia_Tri_Don": "800000", "Danh_Sach_Chien_Dich": "PG01 / PG04", "Gia_Von_COGS": "380000", "Unnamed: 5": None, "Ngay_Dat_Hang": "2026-06-03"},
    {"Ma_Don_Hang": "GH-2026-004", "Kenh_Ban": "Hotline", "Gia_Tri_Don": "Lỗi dữ liệu", "Danh_Sach_Chien_Dich": "PG03", "Gia_Von_COGS": "500000", "Unnamed: 5": None, "Ngay_Dat_Hang": "2026-06-04"},
    {"Ma_Don_Hang": "GH-2026-005", "Kenh_Ban": "Lazada", "Gia_Tri_Don": "3.200.000 VNĐ", "Danh_Sach_Chien_Dich": "PG02", "Gia_Von_COGS": "Lỗi dữ liệu", "Unnamed: 5": None, "Ngay_Dat_Hang": "05-06-2026"},
]

raw_df = pd.DataFrame(raw_rows)
raw_snapshot = raw_df.copy(deep=True)

cleaner = DataCleaner({"GiaHoa_Raw_Messy_TestCase_08": raw_df})
can_proc, norm_data, q_sum, errs, excs = cleaner.clean_and_normalize()
tx = norm_data["Normalized_Transactions"]

# 1. GH-2026-001: PG02 không bị biến thành 0, không bị nhận nhầm là COGS; 650.000 VND ở cột F được ghi nhận ứng viên khôi phục
r1 = tx[tx["Order_ID"] == "GH-2026-001"].iloc[0]
assert pd.isna(r1["COGS"]), f"COGS phải là NaN/None khi ô chứa PG02, không được là {r1['COGS']}"
assert r1["COGS_Status"] == "EXCEPTION_CAMPAIGN_IN_COGS"
assert r1["Unmapped_Currency_Candidate"] == 650000.0
assert "F2" in r1["Unmapped_Currency_Cell"]
assert pd.isna(r1["Source_Profit"]) and r1["Formula_Status"] == "INSUFFICIENT_DATA"

# 2. GH-2026-002: 2.5 triệu -> 2,500,000; COGS 1.1 triệu -> 1,100,000; Profit = 1,400,000
r2 = tx[tx["Order_ID"] == "GH-2026-002"].iloc[0]
assert r2["Order_Value"] == 2500000.0 and r2["COGS"] == 1100000.0 and r2["Source_Profit"] == 1400000.0

# 3. GH-2026-003: 800000 -> 800,000; COGS 380000 -> 380,000; Profit = 420,000
r3 = tx[tx["Order_ID"] == "GH-2026-003"].iloc[0]
assert r3["Order_Value"] == 800000.0 and r3["COGS"] == 380000.0 and r3["Source_Profit"] == 420000.0

# 4. GH-2026-004: Order_Value='Lỗi dữ liệu' -> NaN (không biến thành 0), Profit=INSUFFICIENT_DATA
r4 = tx[tx["Order_ID"] == "GH-2026-004"].iloc[0]
assert pd.isna(r4["Order_Value"]) and pd.isna(r4["Source_Profit"])

# 5. GH-2026-005: COGS='Lỗi dữ liệu' -> NaN (không biến thành 0), Profit=INSUFFICIENT_DATA
r5 = tx[tx["Order_ID"] == "GH-2026-005"].iloc[0]
assert pd.isna(r5["COGS"]) and pd.isna(r5["Source_Profit"])

# 6. Raw Data không bị thay đổi
pd.testing.assert_frame_equal(raw_df, raw_snapshot)

# 7. Xuất file Excel thực tế
excel_bytes = cleaner.export_cleaned_data_excel()
out_path = "Cleaned_GiaHoa_ColumnMapping_Fixed.xlsx"
with open(out_path, "wb") as f:
    f.write(excel_bytes)

print("OUT_EXCEL:", out_path, len(excel_bytes), "bytes")
print("EXCEPTIONS:", len(excs))
for e in excs:
    print(f" - [{e['Error_Type']}] {e['Order_ID']} | Raw: {e['Raw_Value']} | Norm: {e['Normalized_Value']}")
print("AUDIT_LOG:", len(cleaner.audit_log), "entries")
print("ALL 8 COLUMN MAPPING & SHIFTED DATA CHECKS PASSED!")

