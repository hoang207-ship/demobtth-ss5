import io
import pandas as pd
from data_pipeline import DataCleaner, read_csv_smart, load_from_excel_flexible
from analytics_engine import MarketingAnalyticsEngine

print("=== STRESS TEST 5 KỊCH BẢN DỮ LIỆU DỊ BIỆT ===")

# 1. CSV dùng dấu ';', utf-8-sig, có 3 dòng banner phía trên tiêu đề thật
csv_text = (
    "BÁO CÁO DOANH THU QUÝ 3;;;;\n"
    "Đơn vị: Công ty ABC;;;;\n"
    "Ngày xuất: 16/11/2026;;;;\n"
    "Mã đơn;Ngày đặt;Sản phẩm;Doanh thu;Kênh\n"
    "B-01;05/07/2026;  Áo thun  ;1.500.000 VNĐ;Website\n"
    "B-02;2026-07-06;Quần jeans;2.5 triệu;Shopee\n"
)
df_csv = read_csv_smart(io.BytesIO(csv_text.encode("utf-8-sig")))
assert list(df_csv.columns) == ["Mã đơn", "Ngày đặt", "Sản phẩm", "Doanh thu", "Kênh"], list(df_csv.columns)
c1 = DataCleaner({"Untitled": df_csv})
can1, norm1, q1, _, _ = c1.clean_and_normalize()
assert can1 is True and len(norm1["Normalized_Transactions"]) == 2
assert norm1["Normalized_Transactions"]["Order_Value"].sum() == 4000000.0
print("[PASS] Kịch bản 1: CSV ';' utf-8-sig + 3 dòng banner -> Smart Header Detection & chuẩn hóa 4,000,000 đ")

# 2. Excel phi tài chính (không có doanh thu, không có mã đơn, chỉ có nhân viên/sản phẩm & ngày)
non_fin_df = pd.DataFrame({
    "Nhân viên": ["  Nguyễn Văn A  ", "Trần Thị B"],
    "Phòng ban": ["Kinh doanh", "Marketing"],
    "Ngày gia nhập": ["15/01/2025", "2025-02-20"],
})
buf_xlsx = io.BytesIO()
with pd.ExcelWriter(buf_xlsx, engine="openpyxl") as w:
    non_fin_df.to_excel(w, sheet_name="Nhan_Su", index=False)
buf_xlsx.seek(0)
ok_x, tabs_x, cls_x, _ = load_from_excel_flexible(buf_xlsx)
assert ok_x is True
c2 = DataCleaner(tabs_x, cls_x)
can2, norm2, q2, _, _ = c2.clean_and_normalize()
assert can2 is True and q2["Processing_Mode"] == "GENERAL_TABULAR"
assert norm2["Normalized_Transactions"]["Extra_Ngày gia nhập"].tolist() == ["2025-01-15", "2025-02-20"]
assert norm2["Normalized_Transactions"]["Extra_Nhân viên"].iloc[0] == "Nguyễn Văn A"
eng2 = MarketingAnalyticsEngine(norm2)
res2 = eng2.run_process_workflow()
html2 = eng2.generate_html_report()
assert "nan đ" not in html2.lower() and "nan%" not in html2.lower()
print("[PASS] Kịch bản 2: Excel phi tài chính -> GENERAL_TABULAR, can_proceed=True, không có 'nan đ' trong HTML")

# 3. Cột hỗn hợp chữ, số, NaN, ký tự đặc biệt + sanitize_df_for_display
mixed_df = pd.DataFrame({
    "Mã": ["M1", "M2", "M3"],
    "Giá trị": ["1.000.000 VNĐ", "abc @#$", None],
    "Hỗn hợp": [100, "200k", None],
})
c3 = DataCleaner({"Mixed": mixed_df})
can3, norm3, q3, _, _ = c3.clean_and_normalize()
tx3 = norm3["Normalized_Transactions"]
assert len(tx3) == 3
# Verify sanitize_df_for_display handles mixed object & list columns cleanly
import pyarrow as pa
from app import sanitize_df_for_display
san = sanitize_df_for_display(tx3)
pa.Table.from_pandas(san)  # Không được raise ArrowTypeError
print("[PASS] Kịch bản 3: Dữ liệu hỗn hợp chữ/số/NaN/list -> sanitize_df_for_display qua PyArrow không lỗi")

# 4 & 5: Chạy lại Gia Hòa 45 dòng & du-lieu-test-ban-le.csv 52 dòng
import subprocess, sys
for script in ["scratch/test_part4_validation.py", "scratch/test_du_lieu_ban_le.py"]:
    r = subprocess.run([sys.executable, script], capture_output=True, text=True)
    assert r.returncode == 0, f"{script} failed:\n{r.stdout}\n{r.stderr}"
print("[PASS] Kịch bản 4 & 5: Gia Hòa 45 dòng & du-lieu-test-ban-le.csv (1,135,530,000 đ) đạt 100%")
print("\n>>> TẤT CẢ 5/5 KỊCH BẢN STRESS TEST DEFENSIVE DATA ENGINEERING ĐẠT 100% <<<")

