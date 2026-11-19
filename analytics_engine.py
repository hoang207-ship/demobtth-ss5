import datetime
import html as _html_lib
import io
import re
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np


def is_valid_num(val: Any) -> bool:
    """Kiểm tra giá trị số hợp lệ (không phải None và không phải NaN)."""
    if val is None:
        return False
    try:
        return not bool(pd.isna(val))
    except Exception:
        return False


def safe_float(val: Any, default: float = 0.0) -> float:
    """Chuyển đổi an toàn sang float, trả về default nếu None/NaN hoặc lỗi."""
    if not is_valid_num(val):
        return default
    try:
        f = float(val)
        return default if pd.isna(f) else f
    except Exception:
        return default


def _esc(val: Any) -> str:
    return _html_lib.escape("" if val is None else str(val))


def _fmt_curr(val: Any) -> str:
    return f"{safe_float(val, 0.0):,.0f} đ"


def _parse_money_from_text(text: Any) -> float:
    s = str(text or "")
    m = re.search(r"-?\d[\d,\.]*", s)
    if not m:
        return 0.0
    num_str = m.group(0).replace(",", "")
    return safe_float(num_str, 0.0)


ENTERPRISE_NARRATIVE_CSS = """
.ent-wrap { margin: 14px 0 18px 0; font-family: 'Inter', 'Segoe UI', sans-serif; }
.ent-card {
    background: #FFFFFF;
    border: 1px solid #EADDD5;
    border-radius: 18px;
    padding: 20px 24px;
    box-shadow: 0 4px 18px rgba(41, 35, 38, 0.05);
    margin-bottom: 16px;
    transition: transform 0.30s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.30s ease, border-color 0.25s ease;
}
.ent-card:hover {
    transform: translateY(-3px);
    border-color: #D8C4B8;
    box-shadow: 0 14px 30px rgba(41, 35, 38, 0.09);
}
.ent-card.brief { border-left: 5px solid #C21F20; background: #FFFFFF; }
.ent-card.gov { border-left: 5px solid #258B86; background: #FFFFFF; }
.ent-card.control { border-left: 5px solid #D69A3B; background: #FFFFFF; }
.ent-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px dashed #EADDD5; }
.ent-title { font-family: 'Plus Jakarta Sans', 'Inter', sans-serif; font-size: 15px; font-weight: 800; color: #292326; letter-spacing: .1px; }
.ent-sub { font-size: 12px; color: #766A68; font-weight: 500; }
.ent-badge { font-family: 'Plus Jakarta Sans', 'Inter', sans-serif; font-size: 11px; font-weight: 700; padding: 4px 12px; border-radius: 999px; border: 1px solid; white-space: nowrap; transition: transform 0.22s ease; }
.ent-badge:hover { transform: scale(1.04); }
.ent-badge.pos { background: #E6F5EE; color: #27845E; border-color: #BCE3D1; }
.ent-badge.warn { background: #FDF4E3; color: #A66E14; border-color: #F4DAA3; }
.ent-badge.neg { background: #FDF1F0; color: #C21F20; border-color: #F2C9CA; }
.ent-list { margin: 0; padding-left: 18px; color: #292326; font-size: 13px; line-height: 1.65; }
.ent-list li { margin-bottom: 7px; transition: transform 0.22s ease; }
.ent-list li:hover { transform: translateX(3px); }
.ent-list li:last-child { margin-bottom: 0; }
.ent-mono { font-family: 'Inter', monospace; font-weight: 700; color: #7C1F27; background: #F8EDE6; border: 1px solid #EADDD5; padding: 2px 8px; border-radius: 7px; font-size: 12px; font-variant-numeric: tabular-nums; }
.ent-pos { font-family: 'Inter', sans-serif; font-weight: 700; color: #27845E; font-variant-numeric: tabular-nums; }
.ent-warn { font-family: 'Inter', sans-serif; font-weight: 700; color: #D69A3B; font-variant-numeric: tabular-nums; }
.ent-neg { font-family: 'Inter', sans-serif; font-weight: 700; color: #C21F20; font-variant-numeric: tabular-nums; }
.ent-commentary {
    margin-top: 14px;
    background: #F8EDE6;
    border: 1px solid #EADDD5;
    border-left: 4px solid #D69A3B;
    border-radius: 14px;
    padding: 14px 18px;
    transition: transform 0.28s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.28s ease;
}
.ent-commentary:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 22px rgba(214, 154, 59, 0.14);
}
.ent-commentary-title { font-family: 'Plus Jakarta Sans', 'Inter', sans-serif; font-size: 12px; font-weight: 800; color: #C21F20; text-transform: uppercase; letter-spacing: .5px; margin-bottom: 6px; }
.ent-commentary ul { margin: 0; padding-left: 16px; font-size: 12.5px; line-height: 1.6; color: #292326; }
.ent-commentary li { margin-bottom: 5px; }
.ent-matrix-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 12px; }
@media (max-width: 900px) { .ent-matrix-grid { grid-template-columns: 1fr; } }
.ent-mcard {
    border-radius: 16px;
    padding: 18px 20px;
    border: 1px solid #EADDD5;
    background: #FFFFFF;
    transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.3s ease;
}
.ent-mcard:hover {
    transform: translateY(-4px);
    box-shadow: 0 14px 30px rgba(41, 35, 38, 0.09);
}
.ent-mcard.pos { border-top: 4px solid #27845E; background: #FFFFFF; }
.ent-mcard.warn { border-top: 4px solid #D69A3B; background: #FFFFFF; }
.ent-mcard.neg { border-top: 4px solid #C21F20; background: #FFFFFF; }
.ent-mcard-h { font-family: 'Plus Jakarta Sans', 'Inter', sans-serif; font-size: 13.5px; font-weight: 800; margin-bottom: 8px; color: #292326; }
.ent-mcard p { font-size: 12.5px; line-height: 1.58; color: #766A68; margin: 0 0 7px 0; }
.ent-mcard p:last-child { margin-bottom: 0; }
"""


def build_enterprise_report_narratives(
    df_campaign_metrics: Any,
    cleaning_report: Optional[Dict[str, Any]] = None,
    exceptions_df: Any = None,
    verification_results: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
    raw_or_cleaned_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Sinh toàn bộ 5 khối thuyết minh & kiểm toán dữ liệu doanh nghiệp (Enterprise BI Narratives)
    dùng chung cho Streamlit Overview (app.py) và HTML Report (generate_html_report).
    """
    cfg = config or {}
    clean_rep = cleaning_report or {}
    raw_data = raw_or_cleaned_data or {}

    if isinstance(df_campaign_metrics, pd.DataFrame):
        df = df_campaign_metrics.copy()
    elif isinstance(df_campaign_metrics, list):
        df = pd.DataFrame(df_campaign_metrics)
    else:
        df = pd.DataFrame()

    if isinstance(exceptions_df, pd.DataFrame):
        exc_list = exceptions_df.to_dict("records") if not exceptions_df.empty else []
    elif isinstance(exceptions_df, list):
        exc_list = [dict(e) for e in exceptions_df]
    else:
        exc_list = []

    return_window = int(safe_float(cfg.get("return_window_days", 30), 30))

    if df.empty:
        empty_box = (
            '<div class="ent-card brief"><div class="ent-head">'
            '<div class="ent-title">Báo cáo Điều hành Tổng hợp (MD&amp;A)</div>'
            '<span class="ent-badge warn">Chưa có dữ liệu phân tích</span></div>'
            '<p style="font-size:13px;color:#475569;margin:0;">Chưa có bảng tổng hợp chiến dịch để tạo thuyết minh quản trị.</p></div>'
        )
        return {
            "block1_executive_mda": empty_box,
            "block2_data_governance": "",
            "revenue_chart_html": "",
            "abc_cost_chart_html": "",
            "block4_internal_control": "",
            "block5_decision_matrix": "",
            "metrics": {},
        }

    # Chuẩn hóa cột số an toàn (tránh NaN / ZeroDivisionError)
    df["_orders"] = df["Orders_Count"].apply(safe_float) if "Orders_Count" in df.columns else 0.0
    df["_rev"] = df["Attributed_Revenue"].apply(safe_float) if "Attributed_Revenue" in df.columns else 0.0
    df["_gross"] = df["Gross_Revenue"].apply(safe_float) if "Gross_Revenue" in df.columns else df["_rev"]
    df["_ret"] = df["Attributed_Return"].apply(safe_float) if "Attributed_Return" in df.columns else 0.0
    df["_cogs"] = df["Attributed_COGS"].apply(safe_float) if "Attributed_COGS" in df.columns else 0.0
    df["_ns"] = df["Net_Sales"].apply(safe_float) if "Net_Sales" in df.columns else 0.0

    has_costs = ("Total_Cost" in df.columns) and df["Total_Cost"].apply(is_valid_num).any()
    df["_dc"] = df["Direct_Cost"].apply(safe_float) if "Direct_Cost" in df.columns else 0.0
    df["_oh"] = df["Allocated_Overhead"].apply(safe_float) if "Allocated_Overhead" in df.columns else 0.0
    df["_tc"] = df["Total_Cost"].apply(safe_float) if has_costs else 0.0
    df["_nc"] = df["Net_Contribution"].apply(safe_float) if (has_costs and "Net_Contribution" in df.columns) else 0.0
    df["_roi"] = df["ROI"].apply(safe_float) if (has_costs and "ROI" in df.columns) else 0.0
    df["_roas"] = df["ROAS"].apply(safe_float) if (has_costs and "ROAS" in df.columns) else 0.0
    df["_ret_rate"] = np.where(df["_rev"] > 0, (df["_ret"] / df["_rev"]) * 100.0, 0.0)

    if "Campaign_Name" not in df.columns:
        df["Campaign_Name"] = df.get("Campaign_ID", "N/A")
    if "Channel" not in df.columns:
        df["Channel"] = "General"
    if "Cost_Driver" not in df.columns:
        df["Cost_Driver"] = "Order_Volume"

    df_tx = raw_data.get("Normalized_Transactions")
    df_ret = raw_data.get("Normalized_Returns")

    # Tổng hợp Khối 1: Executive MD&A
    if cfg.get("total_orders") is not None:
        total_orders = int(safe_float(cfg.get("total_orders"), 0))
    elif df_tx is not None and not df_tx.empty:
        total_orders = int(len(df_tx))
    else:
        total_orders = int(df["_orders"].sum())

    total_campaigns = int(len(df))
    attributed_revenue = float(df["_rev"].sum())
    gross_revenue = float(df["_gross"].sum())
    if "Gross_Revenue" not in df.columns and df_tx is not None and not df_tx.empty and "Gross_Sales" in df_tx.columns:
        tx_gross_sum = float(df_tx["Gross_Sales"].apply(safe_float).sum())
        if tx_gross_sum > gross_revenue:
            gross_revenue = tx_gross_sum
    if gross_revenue < attributed_revenue:
        gross_revenue = attributed_revenue
    total_discount = max(0.0, gross_revenue - attributed_revenue)
    attributed_return = float(df["_ret"].sum())
    return_rate = (attributed_return / attributed_revenue * 100.0) if attributed_revenue > 0 else 0.0
    net_sales = float(df["_ns"].sum())

    total_cost = float(df["_tc"].sum()) if has_costs else 0.0
    direct_cost = float(df["_dc"].sum()) if has_costs else 0.0
    allocated_overhead = float(df["_oh"].sum()) if has_costs else 0.0
    direct_cost_pct = (direct_cost / total_cost * 100.0) if total_cost > 0 else 0.0
    overhead_pct = (allocated_overhead / total_cost * 100.0) if total_cost > 0 else 0.0

    drivers = [
        str(x).strip()
        for x in df["Cost_Driver"].dropna().astype(str).unique().tolist()
        if str(x).strip() not in ("", "None", "nan")
    ]
    cost_driver = ", ".join(drivers) if drivers else "Order_Volume / Revenue"

    net_contribution = float(df["_nc"].sum()) if has_costs else 0.0
    net_margin = (net_contribution / net_sales * 100.0) if (has_costs and net_sales > 0) else 0.0
    total_roi = (net_contribution / total_cost * 100.0) if (has_costs and total_cost > 0) else 0.0
    total_roas = (attributed_revenue / total_cost) if (has_costs and total_cost > 0) else 0.0

    nc_cls = "ent-pos" if net_contribution >= 0 else "ent-neg"
    if has_costs:
        cost_bullet_html = (
            f"<b>Cấu trúc chi phí ABC &amp; Lợi nhuận đóng góp (Net Contribution):</b> "
            f"Tổng chi phí vận hành chiến dịch là <span class='ent-mono'>{_fmt_curr(total_cost)}</span>, "
            f"bao gồm <span class='ent-mono'>{_fmt_curr(direct_cost)}</span> chi phí trực tiếp (<span class='ent-mono'>{direct_cost_pct:.1f}%</span>) "
            f"và <span class='ent-mono'>{_fmt_curr(allocated_overhead)}</span> chi phí chung phân bổ theo tiêu thức <i>{_esc(cost_driver)}</i> "
            f"(<span class='ent-mono'>{overhead_pct:.1f}%</span>). "
            f"<b>Lợi nhuận đóng góp ròng (Net Contribution)</b> toàn doanh nghiệp đạt <span class='{nc_cls}'>{_fmt_curr(net_contribution)}</span> "
            f"(Biên lợi nhuận ròng đạt <span class='{nc_cls}'>{net_margin:.1f}%</span>, ROI đạt <span class='{nc_cls}'>{total_roi:+.1f}%</span>, ROAS đạt <span class='ent-mono'>{total_roas:.2f}x</span>)."
        )
    else:
        cost_bullet_html = (
            f"<b>Cấu trúc chi phí ABC &amp; Lợi nhuận đóng góp (Net Contribution):</b> "
            f"Dữ liệu chi phí chiến dịch (<code>Campaign_Costs</code>) chưa được cung cấp trong nguồn đầu vào, do đó "
            f"<span class='ent-warn'>chưa đủ cơ sở ghi nhận chi phí trực tiếp / chi phí chung phân bổ và Net Contribution</span>. "
            f"Doanh thu thuần sau hoàn trả (Net Sales) hiện đạt <span class='ent-pos'>{_fmt_curr(net_sales)}</span>."
        )

    block1_html = f"""
    <div class="ent-card brief">
        <div class="ent-head">
            <div>
                <div class="ent-title">1. Báo cáo Điều hành Tổng hợp (Executive Management Summary — MD&amp;A)</div>
                <div class="ent-sub">Tổng hợp tự động từ số liệu sau làm sạch, phân bổ đa điểm chạm &amp; đối soát kế toán quản trị</div>
            </div>
            <span class="ent-badge {'pos' if (not has_costs or net_contribution >= 0) else 'neg'}">{'Hiệu suất Dương' if (not has_costs or net_contribution >= 0) else 'Cần Kiểm soát Lỗ'}</span>
        </div>
        <ul class="ent-list">
            <li><b>Quy mô &amp; Luồng doanh thu gộp:</b> Trong kỳ báo cáo, hệ thống đã hợp nhất và xử lý <span class="ent-mono">{total_orders:,}</span> giao dịch từ <span class="ent-mono">{total_campaigns}</span> nhóm chiến dịch kinh doanh. <b>Tổng doanh thu gộp (<i>Gross Revenue</i>)</b> đạt <span class="ent-mono">{_fmt_curr(gross_revenue)}</span> (sau giảm giá/chiết khấu thương mại <span class="ent-warn">{_fmt_curr(total_discount)}</span>, doanh thu ghi nhận trước hoàn trả đạt <span class="ent-mono">{_fmt_curr(attributed_revenue)}</span>).</li>
            <li><b>Đối soát giảm trừ doanh thu (Return Reconciliation):</b> Giá trị hàng bán bị trả lại trong khung <span class="ent-mono">{return_window}</span> ngày là <span class="ent-neg">{_fmt_curr(attributed_return)}</span> (chiếm <span class="ent-warn">{return_rate:.2f}%</span> doanh thu trước hoàn), đưa <b>Doanh thu thuần thực hiện (Net Sales)</b> về mức <span class="ent-pos">{_fmt_curr(net_sales)}</span>.</li>
            <li>{cost_bullet_html}</li>
        </ul>
    </div>
    """

    # Khối 2: Data Governance & ETL Audit Log
    quality_score = safe_float(clean_rep.get("Data_Quality_Score", 100.0), 100.0)
    if quality_score >= 85.0:
        status_badge = "Chuẩn kiểm toán"
        badge_cls = "pos"
    elif quality_score >= 65.0:
        status_badge = "Cần lưu ý"
        badge_cls = "warn"
    else:
        status_badge = "Rủi ro sai lệch"
        badge_cls = "neg"

    missing_count = int(safe_float(clean_rep.get("Missing_Fields_Count", 0), 0))
    duplicate_count = int(safe_float(clean_rep.get("Duplicate_Rows_Count", 0), 0))
    mismatch_count = int(safe_float(clean_rep.get("Auto_Fixed_Count", 0), 0)) + int(safe_float(clean_rep.get("Total_Errors_Count", 0), 0))

    if df_ret is not None and not df_ret.empty and df_tx is not None and not df_tx.empty and "Order_ID" in df_tx.columns and "Order_ID" in df_ret.columns:
        tx_ids = set(df_tx["Order_ID"].dropna().astype(str).str.strip())
        ret_ids = df_ret["Order_ID"].dropna().astype(str).str.strip()
        matched_cnt = sum(1 for oid in ret_ids if oid in tx_ids)
        match_rate = (matched_cnt / len(df_ret) * 100.0) if len(df_ret) > 0 else 100.0
        match_note = f"({matched_cnt}/{len(df_ret)} mã đơn hoàn trả khớp thành công)"
    else:
        match_rate = 100.0
        match_note = "(Không phát sinh đơn hoàn ngoài bảng hoặc khớp 100%)"

    ver_tests = (verification_results or {}).get("tests") or []
    if ver_tests:
        passed_direct = sum(1 for t in ver_tests if t.get("status") == "PASS")
        na_tests = sum(1 for t in ver_tests if t.get("status") == "NOT_APPLICABLE")
        passed_checks = passed_direct + na_tests if (verification_results or {}).get("overall_status") == "PASS" else passed_direct
        ver_note = f"{passed_direct} PASS trực tiếp, {na_tests} N/A không áp dụng" if na_tests > 0 else "Hoàn tất đối soát CHK-01 đến CHK-07"
    else:
        passed_checks = 0
        ver_note = "Chưa chạy Verification Suite — vào mục Verification để chứng nhận"

    block2_html = f"""
    <div class="ent-card gov">
        <div class="ent-head">
            <div>
                <div class="ent-title">2. Biên bản Đối soát &amp; Chất lượng Dữ liệu Đầu vào (Data Governance &amp; ETL Audit Log)</div>
                <div class="ent-sub">Bằng chứng kiểm toán toàn vẹn dữ liệu đa nguồn (Transactions • Returns • Campaign_Costs)</div>
            </div>
            <span class="ent-badge {badge_cls}">Data Quality: {quality_score:.1f}/100 — {_esc(status_badge)}</span>
        </div>
        <ul class="ent-list">
            <li><b>Chỉ số Tín nhiệm Dữ liệu (Data Quality Score):</b> Đạt <span class="ent-mono">{quality_score:.1f}/100</span> — Trạng thái: <span class="ent-badge {badge_cls}">{_esc(status_badge)}</span>.</li>
            <li><b>Nhật ký Làm sạch &amp; Chuẩn hóa (Data Sanitization Summary):</b> Đã phát hiện và xử lý <span class="ent-mono">{missing_count:,}</span> bản ghi khuyết thiếu trường trọng yếu, cô lập/loại trừ <span class="ent-mono">{duplicate_count:,}</span> giao dịch trùng lặp (<code>Order_ID</code> / <code>Return_ID</code>), và chuẩn hóa <span class="ent-mono">{mismatch_count:,}</span> điểm lệch định dạng/schema.</li>
            <li><b>Đối soát chéo (Cross-Tab Reconciliation):</b> Tỷ lệ khớp lệnh <code>Order_ID</code> giữa bảng Giao dịch (<code>Transactions</code>) và bảng Hoàn trả (<code>Returns</code>) đạt <span class="ent-pos">{match_rate:.1f}%</span> <span style="color:#64748B;font-size:12px;">{_esc(match_note)}</span>.</li>
            <li><b>Chứng nhận Kiểm toán Hệ thống (Verification Gate):</b> Vượt qua <span class="ent-mono">{passed_checks}/7</span> bài kiểm tra toàn vẹn số liệu (<code>CHK-01</code> đến <code>CHK-07</code>) <span style="color:#64748B;font-size:12px;">— {_esc(ver_note)}</span>.</li>
        </ul>
    </div>
    """

    # Khối 3a: Thuyết minh dưới Biểu đồ Doanh thu & Giảm trừ
    top_ns_row = df.sort_values("_ns", ascending=False).iloc[0]
    top_ns_camp = str(top_ns_row["Campaign_Name"])
    top_ns_chan = str(top_ns_row["Channel"])
    top_ns_val = float(top_ns_row["_ns"])
    top_rev_share = (top_ns_val / net_sales * 100.0) if net_sales > 0 else 0.0

    ret_pos_df = df[df["_ret"] > 0].copy()
    if not ret_pos_df.empty:
        max_ret_row = ret_pos_df.sort_values(["_ret_rate", "_ret"], ascending=False).iloc[0]
        highest_ret_camp = str(max_ret_row["Campaign_Name"])
        max_ret_rate = float(max_ret_row["_ret_rate"])
        max_ret_val = float(max_ret_row["_ret"])
        diff_vs_avg = max_ret_rate - return_rate
        ret_comment_html = (
            f"<b>Rủi ro thất thoát sau bán hàng (Return Erosion):</b> "
            f"Cảnh báo chiến dịch <b>{_esc(highest_ret_camp)}</b> có tỷ lệ hoàn trả lên tới <span class='ent-neg'>{max_ret_rate:.2f}%</span> "
            f"(tương đương thất thoát <span class='ent-neg'>{_fmt_curr(max_ret_val)}</span>), "
            f"{'cao hơn' if diff_vs_avg >= 0 else 'thấp hơn'} <span class='ent-warn'>{abs(diff_vs_avg):.2f}%</span> so với mức trung bình toàn hệ thống (<span class='ent-mono'>{return_rate:.2f}%</span>)."
        )
    else:
        ret_comment_html = (
            f"<b>Rủi ro thất thoát sau bán hàng (Return Erosion):</b> "
            f"<span class='ent-pos'>Không phát sinh thất thoát hoàn trả (0 đ — Tỷ lệ hoàn trả 0.00%)</span>; toàn bộ doanh thu phân bổ được bảo toàn trọn vẹn thành Net Sales."
        )

    if df_tx is not None and not df_tx.empty and "Campaign_Count" in df_tx.columns:
        mt_cnt = int((pd.to_numeric(df_tx["Campaign_Count"], errors="coerce").fillna(1) >= 2).sum())
        mt_pct = (mt_cnt / len(df_tx) * 100.0) if len(df_tx) > 0 else 0.0
    else:
        mt_pct = 0.0

    if mt_pct > 0:
        mt_html = (
            f"<b>Hiệu ứng đa điểm chạm (Multi-Touch Attribution Impact):</b> "
            f"Có <span class='ent-mono'>{mt_pct:.1f}%</span> đơn hàng đi qua từ 2 chiến dịch trở lên, chứng tỏ sự cộng hưởng giữa kênh nhận diện (<i>Upper-Funnel</i>) và kênh chuyển đổi (<i>Lower-Funnel</i>)."
        )
    else:
        mt_html = (
            f"<b>Hiệu ứng đa điểm chạm (Multi-Touch Attribution Impact):</b> "
            f"Có <span class='ent-mono'>0.0%</span> đơn hàng đa điểm chạm — 100% đơn hàng chuyển đổi trực tiếp qua một chiến dịch đơn lẻ hoặc kênh tự nhiên."
        )

    revenue_chart_html = f"""
    <div class="ent-commentary">
        <div class="ent-commentary-title">Thuyết minh Chỉ số — Doanh thu &amp; Giảm trừ (Analytical Commentary)</div>
        <ul>
            <li><b>Động lực tăng trưởng chính (Revenue Driver):</b> Điểm sáng doanh thu thuộc về <b>{_esc(top_ns_camp)}</b> (Kênh <i>{_esc(top_ns_chan)}</i>), đóng góp <span class="ent-pos">{_fmt_curr(top_ns_val)}</span> (chiếm <span class="ent-mono">{top_rev_share:.1f}%</span> tổng Net Sales toàn hệ thống).</li>
            <li>{ret_comment_html}</li>
            <li>{mt_html}</li>
        </ul>
    </div>
    """

    # Khối 3b: Thuyết minh dưới Biểu đồ Phân bổ Chi phí ABC & Lợi nhuận Ròng
    if has_costs:
        cost_active = df[df["_tc"] > 0].copy()
        best_pool = cost_active if not cost_active.empty else df
        best_row = best_pool.sort_values(["_roi", "_nc"], ascending=False).iloc[0]
        best_roi_camp = str(best_row["Campaign_Name"])
        best_nc_val = float(best_row["_nc"])
        best_roi_val = float(best_row["_roi"])
        best_roas_val = float(best_row["_roas"])

        oh_row = df.sort_values("_oh", ascending=False).iloc[0]
        oh_camp = str(oh_row["Campaign_Name"])
        max_oh_val = float(oh_row["_oh"])
        oh_camp_tc = float(oh_row["_tc"])
        oh_share = (max_oh_val / oh_camp_tc * 100.0) if oh_camp_tc > 0 else 0.0
        oh_driver = str(oh_row["Cost_Driver"])

        loss_df = df[df["_nc"] < 0].copy()
        loss_count = int(len(loss_df))
        if loss_count > 0:
            worst_row = loss_df.sort_values("_nc", ascending=True).iloc[0]
            worst_camp = str(worst_row["Campaign_Name"])
            worst_loss = float(worst_row["_nc"])
            loss_html = (
                f"<b>Điểm nghẽn thâm hụt (Profitability Bottleneck):</b> "
                f"Ghi nhận <span class='ent-neg'>{loss_count}</span> chiến dịch có Net Contribution &lt; 0 "
                f"(nặng nhất là <b>{_esc(worst_camp)}</b> với mức lỗ <span class='ent-neg'>{_fmt_curr(worst_loss)}</span>), cần lập tức tái cơ cấu hoặc cắt giảm ngân sách."
            )
        else:
            loss_html = (
                f"<b>Điểm nghẽn thâm hụt (Profitability Bottleneck):</b> "
                f"<span class='ent-pos'>100% chiến dịch đều đạt lợi nhuận dương (Net Contribution &ge; 0)</span> — không ghi nhận chiến dịch thâm hụt vốn trong kỳ."
            )

        abc_cost_chart_html = f"""
        <div class="ent-commentary">
            <div class="ent-commentary-title">Thuyết minh Chỉ số — Chi phí ABC &amp; Lợi nhuận Ròng (Capital Commentary)</div>
            <ul>
                <li><b>Hiệu quả sử dụng vốn (Capital Efficiency):</b> Chiến dịch dẫn đầu về hiệu suất sinh lời là <b>{_esc(best_roi_camp)}</b> với Net Contribution đạt <span class="ent-pos">{_fmt_curr(best_nc_val)}</span> (<span class="ent-pos">ROI = {best_roi_val:+.1f}%</span>, <span class="ent-mono">ROAS = {best_roas_val:.2f}x</span>).</li>
                <li><b>Áp lực chi phí gián tiếp (Overhead Burden):</b> Chiến dịch <b>{_esc(oh_camp)}</b> đang gánh tỷ trọng chi phí chung phân bổ lớn nhất (<span class="ent-warn">{_fmt_curr(max_oh_val)}</span> — chiếm <span class="ent-mono">{oh_share:.1f}%</span> tổng chi phí chiến dịch) theo tiêu thức vận hành <i>{_esc(oh_driver)}</i>.</li>
                <li>{loss_html}</li>
            </ul>
        </div>
        """
    else:
        abc_cost_chart_html = f"""
        <div class="ent-commentary">
            <div class="ent-commentary-title">Thuyết minh Chỉ số — Cơ cấu Lợi nhuận &amp; Chi phí (Capital Commentary)</div>
            <ul>
                <li><b>Hiệu quả sử dụng vốn (Capital Efficiency):</b> Hiện chưa có bảng chi phí chiến dịch (<code>Campaign_Costs</code>) để tính <i>ROI / ROAS</i> thuần theo ABC.</li>
                <li><b>Áp lực chi phí gián tiếp (Overhead Burden):</b> Chưa ghi nhận chi phí phân bổ gián tiếp (Allocated Overhead).</li>
                <li><b>Điểm nghẽn thâm hụt (Profitability Bottleneck):</b> <span class="ent-pos">100% chiến dịch đang ghi nhận Net Sales dương sau giảm trừ hoàn trả</span>; cần bổ sung tab <code>Campaign_Costs</code> để kiểm toán lợi nhuận ròng.</li>
            </ul>
        </div>
        """

    # Khối 4: Kiểm soát nội bộ & Ngoại lệ (Internal Control & HITL Exceptions)
    late_excs = [e for e in exc_list if e.get("Error_Type") == "OUT_OF_WINDOW_RETURN"]
    late_count = len(late_excs)
    late_amount = 0.0
    if late_count > 0:
        for e in late_excs:
            oid = str(e.get("Order_ID", "")).strip()
            matched_amt = 0.0
            if df_ret is not None and not df_ret.empty and "Order_ID" in df_ret.columns and "Return_Amount" in df_ret.columns:
                sub_r = df_ret[df_ret["Order_ID"].astype(str).str.strip() == oid]
                if not sub_r.empty:
                    matched_amt = safe_float(sub_r["Return_Amount"].apply(safe_float).sum(), 0.0)
            if matched_amt <= 0:
                matched_amt = _parse_money_from_text(e.get("Raw_Value"))
            late_amount += matched_amt
        late_html = (
            f"<b>Kiểm soát hoàn trả quá hạn (Out-of-Window Returns):</b> "
            f"Phát hiện <span class='ent-warn'>{late_count}</span> yêu cầu hoàn trả vượt quá thời hạn quy định <span class='ent-mono'>{return_window}</span> ngày "
            f"(Tổng giá trị liên quan: <span class='ent-neg'>{_fmt_curr(late_amount)}</span>)."
        )
    else:
        late_html = (
            f"<b>Kiểm soát hoàn trả quá hạn (Out-of-Window Returns):</b> "
            f"<span class='ent-pos'>0 yêu cầu hoàn trả vượt hạn</span> — 100% giao dịch hoàn trả tuân thủ đúng khung <span class='ent-mono'>{return_window}</span> ngày."
        )

    neg_df = df[(df["_roi"] < 0) | (df["_nc"] < 0)].copy() if has_costs else pd.DataFrame()
    if not neg_df.empty:
        neg_items = [
            f"<b>{_esc(r['Campaign_Name'])}</b> (<span class='ent-neg'>ROI {safe_float(r['_roi']):+.1f}%</span>, lỗ <span class='ent-neg'>{_fmt_curr(r['_nc'])}</span>)"
            for _, r in neg_df.iterrows()
        ]
        neg_html = (
            f"<b>Cảnh báo chiến dịch âm vốn (Negative ROI Alert):</b> "
            f"Cần đóng băng ngân sách hoặc phê duyệt đặc biệt đối với {len(neg_items)} chiến dịch: {', '.join(neg_items)}."
        )
    else:
        neg_html = (
            f"<b>Cảnh báo chiến dịch âm vốn (Negative ROI Alert):</b> "
            f"<span class='ent-pos'>Không có chiến dịch âm vốn (100% chiến dịch đạt ROI &ge; 0%)</span>."
        )

    total_exc = len(exc_list)
    if total_exc == 0:
        hitl_html = (
            f"<b>Trạng thái Phê duyệt Kiểm soát viên (HITL Approval Status):</b> "
            f"<span class='ent-pos'>Hệ thống sạch ngoại lệ (0 mục phát sinh)</span> — Không có hồ sơ chờ giải trình."
        )
    else:
        n_app = sum(1 for e in exc_list if e.get("Approval_Status") == "APPROVED")
        n_rej = sum(1 for e in exc_list if e.get("Approval_Status") in ("REJECTED", "CORRECTION_REQUESTED"))
        n_pen = sum(1 for e in exc_list if e.get("Approval_Status") == "PENDING_REVIEW")
        notes = [
            f"<code>{_esc(e.get('Order_ID'))}</code> ({_esc(e.get('Reviewer', 'Admin'))}): <i>\"{_esc(e.get('Note'))}\"</i>"
            for e in exc_list
            if str(e.get("Note", "")).strip()
        ][:3]
        notes_suffix = f" | Giải trình gần nhất: {'; '.join(notes)}." if notes else ""
        hitl_html = (
            f"<b>Trạng thái Phê duyệt Kiểm soát viên (HITL Approval Status):</b> "
            f"Tổng <span class='ent-mono'>{total_exc}</span> ngoại lệ "
            f"(<span class='ent-pos'>{n_app} Đã duyệt</span> • <span class='ent-neg'>{n_rej} Từ chối/Yêu cầu sửa</span> • <span class='ent-warn'>{n_pen} Chờ duyệt</span>)"
            f"{notes_suffix}"
        )

    block4_html = f"""
    <div class="ent-card control">
        <div class="ent-head">
            <div>
                <div class="ent-title">4. Báo cáo Kiểm soát Nội bộ &amp; Ngoại lệ (Internal Control &amp; HITL Exceptions)</div>
                <div class="ent-sub">Giám sát tuân thủ chính sách hoàn trả, kiểm soát chiến dịch âm vốn &amp; nhật ký phê duyệt thẩm quyền</div>
            </div>
            <span class="ent-badge {'pos' if (late_count == 0 and neg_df.empty and sum(1 for e in exc_list if e.get('Approval_Status') == 'PENDING_REVIEW') == 0) else 'warn'}">Internal Control</span>
        </div>
        <ul class="ent-list">
            <li>{late_html}</li>
            <li>{neg_html}</li>
            <li>{hitl_html}</li>
        </ul>
    </div>
    """

    # Khối 5: Ma trận Khuyến nghị Quản trị 3 Kịch bản
    if has_costs:
        stop_df = df[(df["_nc"] < 0) | (df["_roi"] < 0)].copy()
        stop_ids = set(stop_df["Campaign_ID"].astype(str))
        scale_df = df[(~df["Campaign_ID"].astype(str).isin(stop_ids)) & (df["_roi"] >= 20.0) & (df["_ret_rate"] <= 15.0) & (df["_nc"] > 0)].copy()
        if scale_df.empty:
            dec_col = df["Strategic_Decision"].astype(str) if "Strategic_Decision" in df.columns else pd.Series("", index=df.index)
            scale_df = df[(~df["Campaign_ID"].astype(str).isin(stop_ids)) & (dec_col.str.contains("SCALE", case=False, na=False)) & (df["_nc"] > 0)].copy()
        scale_ids = set(scale_df["Campaign_ID"].astype(str))
        opt_df = df[(~df["Campaign_ID"].astype(str).isin(stop_ids | scale_ids))].copy()

        target_proj_df = scale_df if not scale_df.empty else df[df["_nc"] > 0]
        if not target_proj_df.empty and float(target_proj_df["_tc"].sum()) > 0:
            proj_dc_add = float(target_proj_df["_dc"].sum()) * 0.20
            marginal_roi = float(target_proj_df["_nc"].sum()) / float(target_proj_df["_tc"].sum())
            projected_nc = net_contribution + max(0.0, proj_dc_add * marginal_roi)
        else:
            projected_nc = net_contribution

        scale_names = ", ".join(f"<b>{_esc(x)}</b>" for x in scale_df["Campaign_Name"].tolist()) if not scale_df.empty else "<i>Chưa có chiến dịch đạt ngưỡng ROI &ge; 20%</i>"
        opt_names = ", ".join(f"<b>{_esc(x)}</b>" for x in opt_df["Campaign_Name"].tolist()) if not opt_df.empty else "<i>Không có chiến dịch ở vùng trung gian</i>"
        stop_names = ", ".join(f"<b>{_esc(x)}</b>" for x in stop_df["Campaign_Name"].tolist()) if not stop_df.empty else "<span class='ent-pos'>Không có chiến dịch thâm hụt vốn (100% đạt lợi nhuận dương)</span>"

        proj_sentence = (
            f"Dự phóng nếu tăng <span class='ent-mono'>+20% Direct Cost</span> cho nhóm ngôi sao theo hiệu suất biên hiện tại, "
            f"<b>Net Contribution</b> toàn cục dự kiến tăng lên mức <span class='ent-pos'>{_fmt_curr(projected_nc)}</span>."
        )
    else:
        projected_nc = 0.0
        top_half = df.sort_values("_ns", ascending=False).head(max(1, len(df) // 2))
        rest_df = df[~df.index.isin(top_half.index)]
        scale_names = ", ".join(f"<b>{_esc(x)}</b>" for x in top_half["Campaign_Name"].tolist())
        opt_names = ", ".join(f"<b>{_esc(x)}</b>" for x in rest_df["Campaign_Name"].tolist()) if not rest_df.empty else "<i>Các chiến dịch hiện hữu</i>"
        stop_names = "<span class='ent-pos'>Chưa phát hiện chiến dịch âm vốn (thiếu tab Campaign_Costs)</span>"
        proj_sentence = (
            "Bổ sung tab <code>Campaign_Costs</code> để kích hoạt mô phỏng tăng <span class='ent-mono'>+20% Direct Cost</span> và dự phóng Net Contribution ròng."
        )

    block5_html = f"""
    <div class="ent-card" style="padding:18px 20px;">
        <div class="ent-head">
            <div>
                <div class="ent-title">5. Ma trận Khuyến nghị Quản trị 3 Kịch bản (Executive Decision Matrix — Khuyến nghị Kinh doanh)</div>
                <div class="ent-sub">Kế hoạch phân bổ lại nguồn vốn &amp; kiểm soát rủi ro dành cho Ban Giám đốc / CFO</div>
            </div>
            <span class="ent-badge pos">TIẾP TỤC THỬ NGHIỆM &amp; TÁI PHÂN BỔ</span>
        </div>
        <div class="ent-matrix-grid">
            <div class="ent-mcard pos">
                <div class="ent-mcard-h">🟢 KỊCH BẢN MỞ RỘNG ĐẦU TƯ (SCALE &amp; REALLOCATE)</div>
                <p><b>Nhóm áp dụng</b> (<code>ROI &ge; 20%</code>, hoàn trả thấp &le; 15%): {scale_names}.</p>
                <p><b>Hành động điều hành:</b> Tiếp tục thử nghiệm &amp; mở rộng, tăng <span class="ent-pos">15% - 25%</span> ngân sách Direct Cost vào các khung giờ/tệp chuyển đổi tốt nhất. {proj_sentence}</p>
            </div>
            <div class="ent-mcard warn">
                <div class="ent-mcard-h">🟡 KỊCH BẢN TÁI CẤU TRÚC VẬN HÀNH &amp; CHI PHÍ (COST &amp; PROCESS OPTIMIZATION)</div>
                <p><b>Nhóm áp dụng</b> (<code>0% &le; ROI &lt; 20%</code> hoặc tỷ lệ hoàn trả &gt; 15%): {opt_names}.</p>
                <p><b>Hành động điều hành:</b> Điều chỉnh cơ chế — rà soát chất lượng sản phẩm/khâu giao vận để hạ tỷ lệ hoàn trả và đàm phán lại định mức phân bổ chi phí chung (<i>Cost Driver</i>).</p>
            </div>
            <div class="ent-mcard neg">
                <div class="ent-mcard-h">🔴 KỊCH BẢN CẮT GIẢM &amp; KIỂM SOÁT RỦI RO (STOP-LOSS &amp; AUDIT)</div>
                <p><b>Nhóm áp dụng</b> (<code>Net Contribution &lt; 0</code> hoặc <code>ROI &lt; 0%</code>): {stop_names}.</p>
                <p><b>Hành động điều hành:</b> Cắt giảm tối thiểu <span class="ent-neg">50%</span> ngân sách trực tiếp hoặc tạm dừng ngay lập tức, chuyển nguồn vốn thu hồi sang nhóm 🟢 Scale.</p>
            </div>
        </div>
    </div>
    """

    return {
        "block1_executive_mda": block1_html,
        "block2_data_governance": block2_html,
        "revenue_chart_html": revenue_chart_html,
        "abc_cost_chart_html": abc_cost_chart_html,
        "block4_internal_control": block4_html,
        "block5_decision_matrix": block5_html,
        "metrics": {
            "total_orders": total_orders,
            "total_campaigns": total_campaigns,
            "gross_revenue": gross_revenue,
            "total_discount": total_discount,
            "attributed_revenue": attributed_revenue,
            "attributed_return": attributed_return,
            "return_rate": return_rate,
            "net_sales": net_sales,
            "total_cost": total_cost,
            "direct_cost": direct_cost,
            "allocated_overhead": allocated_overhead,
            "net_contribution": net_contribution,
            "net_margin": net_margin,
            "total_roi": total_roi,
            "total_roas": total_roas,
            "quality_score": quality_score,
            "match_rate": match_rate,
            "passed_checks": passed_checks,
            "late_returns_count": late_count,
            "late_returns_amount": late_amount,
            "projected_net_contribution": projected_nc,
        },
    }


class MarketingAnalyticsEngine:
    """
    Động cơ phân tích hiệu quả chiến dịch Marketing & Kiểm toán tài chính:
    - Centralized Data Model (Hỗ trợ cả trường hợp 3 tabs chuẩn hoặc 1 tab Transactions duy nhất).
    - Multi-touch Revenue Attribution (Doanh thu chia đều theo số lượng campaign tham gia).
    - Return Reconciliation (Return Window 15-30 ngày, tránh trừ trùng).
    - Activity Based Costing (ABC) phân bổ chi phí trực tiếp & gián tiếp.
    - Human-in-the-Loop: Quản lý và phê duyệt ngoại lệ có kiểm soát thẩm quyền.
    - Verification Suite: 7 phép kiểm toán tự động (PASS / FAIL / NOT_APPLICABLE).
    - Standalone HTML Dashboard Generator.
    """

    AUTHORIZED_ROLES = [
        "Trưởng phòng Marketing",
        "Trưởng phòng Marketing & Tài chính",
        "Quản trị viên",
        "Admin",
        "Ban Giám Đốc",
        "Giám đốc Kinh doanh"
    ]

    def __init__(
        self,
        normalized_data: Dict[str, pd.DataFrame],
        initial_exceptions: Optional[List[Dict[str, Any]]] = None,
        return_window_days: int = 30,
        quality_summary: Optional[Dict[str, Any]] = None,
    ):
        self.data = normalized_data
        self.return_window_days = return_window_days
        self.quality_summary = quality_summary
        self.processing_log: List[Dict[str, Any]] = []
        self.step_states: Dict[str, Any] = {}
        # Nạp các ngoại lệ từ giai đoạn Data Cleaning vào hàng đợi phê duyệt
        self.exceptions_view: List[Dict[str, Any]] = [dict(e) for e in (initial_exceptions or [])]
        self.report_result: Optional[pd.DataFrame] = None
        self.detailed_attributed_df: Optional[pd.DataFrame] = None
        self.verification_results: Dict[str, Any] = {}
        self.approval_history: List[Dict[str, Any]] = []

    def log(self, step_name: str, status: str, message: str, details: Optional[Dict[str, Any]] = None):
        entry = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "step": step_name,
            "status": status,
            "message": message,
            "details": details or {}
        }
        self.processing_log.append(entry)

    # ==========================================================================
    # GIAI ĐOẠN 3: PROCESS - 6 BƯỚC XỬ LÝ
    # ==========================================================================

    def run_process_workflow(self) -> Dict[str, Any]:
        """Thực thi tuần tự 6 bước của quy trình Process."""
        self.processing_log = []

        # BƯỚC 1: DATA CENTRALIZATION
        step1_res = self._step1_data_centralization()
        self.step_states["step1"] = step1_res
        if step1_res["status"] == "FAILED":
            return {"status": "FAILED", "failed_step": "step1", "message": step1_res.get("error")}

        # BƯỚC 2: REVENUE ATTRIBUTION
        step2_res = self._step2_revenue_attribution(step1_res["centralized_tx"])
        self.step_states["step2"] = step2_res
        if step2_res["status"] == "FAILED":
            return {"status": "FAILED", "failed_step": "step2", "message": step2_res.get("error")}

        # BƯỚC 3: RETURN RECONCILIATION
        step3_res = self._step3_return_reconciliation(step2_res["attributed_df"])
        self.step_states["step3"] = step3_res
        if step3_res["status"] == "FAILED":
            return {"status": "FAILED", "failed_step": "step3", "message": step3_res.get("error")}

        # BƯỚC 4: COST ALLOCATION (ACTIVITY BASED COSTING)
        step4_res = self._step4_cost_allocation(step3_res["reconciled_df"])
        self.step_states["step4"] = step4_res
        if step4_res["status"] == "FAILED":
            return {"status": "FAILED", "failed_step": "step4", "message": step4_res.get("error")}

        # BƯỚC 5: PROCESS AUTOMATION & NET CONTRIBUTION
        step5_res = self._step5_net_contribution(step4_res["campaign_summary_df"])
        self.step_states["step5"] = step5_res

        # BƯỚC 6: CAMPAIGN DECISION & HUMAN-IN-THE-LOOP
        step6_res = self._step6_campaign_decision()
        self.step_states["step6"] = step6_res

        return {
            "status": "COMPLETED",
            "step_states": self.step_states,
            "report_result": self.report_result,
            "exceptions_view": self.exceptions_view,
            "log": self.processing_log
        }

    # --- Bước 1: Data Centralization ---
    def _step1_data_centralization(self) -> Dict[str, Any]:
        self.log("Step 1: Centralization", "RUNNING", "Đang tích hợp dữ liệu từ các Tab đã chuẩn hóa...")
        try:
            df_tx = self.data.get("Normalized_Transactions")
            if df_tx is None or df_tx.empty:
                # Fallback nếu truyền key Transactions
                df_tx = self.data.get("Transactions")

            if df_tx is None or df_tx.empty:
                self.log("Step 1: Centralization", "FAILED", "Thiếu dữ liệu đơn hàng (Transactions). Không thể tiếp tục.")
                return {"status": "FAILED", "error": "Thiếu dữ liệu Transactions"}

            df_ret = self.data.get("Normalized_Returns", self.data.get("Returns"))
            df_costs = self.data.get("Normalized_Campaign_Costs", self.data.get("Campaign_Costs"))

            has_returns = (df_ret is not None and not df_ret.empty)
            has_costs = (df_costs is not None and not df_costs.empty)

            total_orders = len(df_tx)
            total_returns = len(df_ret) if has_returns else 0
            total_costs = len(df_costs) if has_costs else 0

            msg = f"Tập trung thành công {total_orders} đơn hàng. Dữ liệu Hoàn trả: {'Có ('+str(total_returns)+' bản ghi)' if has_returns else 'Chưa cung cấp'}. Dữ liệu Chi phí: {'Có ('+str(total_costs)+' chiến dịch)' if has_costs else 'Chưa cung cấp'}."
            self.log("Step 1: Centralization", "PASS", msg, {
                "orders_count": total_orders,
                "has_returns": has_returns,
                "has_costs": has_costs
            })

            return {
                "name": "BƯỚC 1: Tập trung dữ liệu (Centralized Data Model)",
                "status": "PASS",
                "centralized_tx": df_tx.copy(deep=True),
                "has_returns": has_returns,
                "has_costs": has_costs,
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
            }
        except Exception as e:
            self.log("Step 1: Centralization", "FAILED", f"Lỗi tập trung dữ liệu: {str(e)}")
            return {"name": "BƯỚC 1: Tập trung dữ liệu", "status": "FAILED", "error": str(e)}

    def get_active_transactions_df(self) -> Optional[pd.DataFrame]:
        """
        Trả về bảng Normalized_Transactions đã loại trừ các bản ghi bị từ chối:
        - Nếu là ngoại lệ DUPLICATE_ORDER_ID bị REJECTED / CORRECTION_REQUESTED: chỉ loại bản sao (Is_Duplicate_Copy == True), giữ nguyên bản gốc.
        - Các ngoại lệ khác bị REJECTED / CORRECTION_REQUESTED: loại theo Order_ID.
        """
        df_tx = self.data.get("Normalized_Transactions", self.data.get("Transactions"))
        if df_tx is None or df_tx.empty:
            return df_tx

        dup_rejected_ids = set(
            e["Order_ID"] for e in self.exceptions_view
            if e.get("Error_Type") == "DUPLICATE_ORDER_ID"
            and e.get("Approval_Status") in ("REJECTED", "CORRECTION_REQUESTED")
        )
        other_rejected_ids = set(
            e["Order_ID"] for e in self.exceptions_view
            if e.get("Error_Type") != "DUPLICATE_ORDER_ID"
            and e.get("Approval_Status") in ("REJECTED", "CORRECTION_REQUESTED")
        )

        mask = pd.Series(True, index=df_tx.index)
        if other_rejected_ids:
            mask &= ~df_tx["Order_ID"].isin(other_rejected_ids)
        if dup_rejected_ids:
            if "Is_Duplicate_Copy" in df_tx.columns:
                mask &= ~(df_tx["Order_ID"].isin(dup_rejected_ids) & (df_tx["Is_Duplicate_Copy"] == True))
            else:
                # Fallback nếu dữ liệu cũ không có cột Is_Duplicate_Copy: giữ dòng đầu tiên của mỗi Order_ID
                is_dup_copy = df_tx.duplicated(subset=["Order_ID"], keep="first")
                mask &= ~(df_tx["Order_ID"].isin(dup_rejected_ids) & is_dup_copy)
        return df_tx[mask].copy()

    # --- Bước 2: Multi-touch Revenue Attribution ---
    def _step2_revenue_attribution(self, df_tx: pd.DataFrame) -> Dict[str, Any]:
        self.log("Step 2: Revenue Attribution", "RUNNING", "Đang tính phân bổ doanh thu đa điểm chạm (Multi-touch Attribution)...")
        try:
            active_df = self.get_active_transactions_df()
            if active_df is None:
                active_df = df_tx

            attributed_rows = []
            total_source_revenue = 0.0
            total_attributed_revenue = 0.0
            unattributed_orders_count = 0

            for _, r in active_df.iterrows():
                order_id = r["Order_ID"]
                order_val = safe_float(r.get("Order_Value"), 0.0)
                disc_amt = max(0.0, safe_float(r.get("Discount_Amount"), 0.0))
                raw_gross = r.get("Gross_Sales")
                if is_valid_num(raw_gross) and safe_float(raw_gross, 0.0) > 0:
                    parsed_gross = safe_float(raw_gross, order_val)
                    gross_val = max(order_val + disc_amt, parsed_gross) if parsed_gross <= order_val else parsed_gross
                else:
                    gross_val = order_val + disc_amt
                cogs = safe_float(r.get("COGS"), 0.0)
                order_date = r.get("Order_Date")
                channel = r.get("Channel", "Unknown")

                total_source_revenue += order_val

                raw_cmps = r.get("Campaign_List")
                cmp_data_status = r.get("Campaign_Data_Status", "AVAILABLE")

                if raw_cmps is None or (isinstance(raw_cmps, float) and pd.isna(raw_cmps)):
                    clean_cmps = []
                elif isinstance(raw_cmps, str):
                    if raw_cmps.strip() in ["", "KHONG_CO", "MISSING_SOURCE_DATA", "nan", "None", "null"]:
                        clean_cmps = []
                    else:
                        clean_cmps = [c.strip() for c in raw_cmps.split(";") if c.strip() and c.strip() not in ["KHONG_CO", "MISSING_SOURCE_DATA"]]
                elif isinstance(raw_cmps, (list, tuple, set)):
                    clean_cmps = [str(c).strip() for c in raw_cmps if str(c).strip() and str(c).strip() not in ["KHONG_CO", "MISSING_SOURCE_DATA"]]
                else:
                    clean_cmps = []

                cmp_count = len(clean_cmps)

                if cmp_count > 0:
                    attr_rev_per_touch = order_val / cmp_count
                    attr_gross_per_touch = gross_val / cmp_count
                    attr_cogs_per_touch = cogs / cmp_count
                    for cmp_id in clean_cmps:
                        attributed_rows.append({
                            "Order_ID": order_id,
                            "Order_Date": order_date,
                            "Channel": channel,
                            "Campaign_ID": cmp_id,
                            "Gross_Order_Value": gross_val,
                            "Campaign_Count": cmp_count,
                            "Attributed_Gross_Revenue": attr_gross_per_touch,
                            "Attributed_Revenue": attr_rev_per_touch,
                            "Attributed_COGS": attr_cogs_per_touch,
                            "Attributed_Return": 0.0,
                            "Net_Sales": attr_rev_per_touch,
                            "Return_Status": "No_Return"
                        })
                        total_attributed_revenue += attr_rev_per_touch
                else:
                    # Trường hợp không có mã chiến dịch:
                    # - Nếu do nguồn thiếu cột chiến dịch -> MISSING_SOURCE_DATA
                    # - Nếu có cột nhưng khách không qua chiến dịch -> ORGANIC_NO_CAMPAIGN
                    unattributed_orders_count += 1
                    campaign_tag = "CHƯA_GẮN_CHIẾN_DỊCH (MISSING_SOURCE_DATA)" if cmp_data_status == "MISSING_SOURCE_DATA" else "ORGANIC_NO_CAMPAIGN"
                    attributed_rows.append({
                        "Order_ID": order_id,
                        "Order_Date": order_date,
                        "Channel": channel,
                        "Campaign_ID": campaign_tag,
                        "Gross_Order_Value": gross_val,
                        "Campaign_Count": 1,
                        "Attributed_Gross_Revenue": gross_val,
                        "Attributed_Revenue": order_val,
                        "Attributed_COGS": cogs,
                        "Attributed_Return": 0.0,
                        "Net_Sales": order_val,
                        "Return_Status": "No_Return"
                    })
                    total_attributed_revenue += order_val

            df_attributed = pd.DataFrame(attributed_rows)
            self.detailed_attributed_df = df_attributed

            # Kiểm tra cân đối doanh thu (Attributed Sum == Source Sum)
            diff = abs(total_source_revenue - total_attributed_revenue)
            is_balanced = diff < 0.01

            self.log("Step 2: Revenue Attribution", "PASS" if is_balanced else "WARNING",
                f"Phân bổ thành công {len(df_attributed)} lượt chạm. Doanh thu nguồn: {total_source_revenue:,.0f} đ, Tổng phân bổ: {total_attributed_revenue:,.0f} đ (Độ lệch: {diff:.2f}).", {
                    "source_revenue": total_source_revenue,
                    "attributed_revenue": total_attributed_revenue,
                    "difference": diff,
                    "organic_orders": unattributed_orders_count
                }
            )

            return {
                "name": "BƯỚC 2: Phân bổ doanh thu (Multi-touch Attribution)",
                "status": "PASS",
                "attributed_df": df_attributed,
                "total_source_revenue": total_source_revenue,
                "total_attributed_revenue": total_attributed_revenue,
                "is_balanced": is_balanced,
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
            }
        except Exception as e:
            self.log("Step 2: Revenue Attribution", "FAILED", f"Lỗi phân bổ doanh thu: {str(e)}")
            return {"name": "BƯỚC 2: Phân bổ doanh thu", "status": "FAILED", "error": str(e)}

    # --- Bước 3: Return Reconciliation ---
    def _step3_return_reconciliation(self, df_attributed: pd.DataFrame) -> Dict[str, Any]:
        self.log("Step 3: Return Reconciliation", "RUNNING", "Đang đối soát hàng hoàn trả theo Return Window...")
        try:
            df_ret = self.data.get("Normalized_Returns", self.data.get("Returns"))
            has_returns = (df_ret is not None and not df_ret.empty)

            df_reconciled = df_attributed.copy(deep=True)

            if not has_returns:
                self.log("Step 3: Return Reconciliation", "PASS", "Không có dữ liệu hoàn trả (Returns). Giữ nguyên Net Sales = Attributed Revenue.")
                return {
                    "name": "BƯỚC 3: Đối soát hàng hoàn trả (Return Reconciliation)",
                    "status": "PASS",
                    "reconciled_df": df_reconciled,
                    "total_valid_returns": 0.0,
                    "total_net_sales": df_reconciled["Net_Sales"].sum(),
                    "out_of_window_count": 0,
                    "is_applicable": False,
                    "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
                }

            # Có dữ liệu hoàn trả -> Thực hiện đối soát
            total_valid_returns = 0.0
            out_of_window_count = 0

            # Lấy các ngoại lệ đã được phê duyệt chấp thuận đối trừ
            approved_exceptions = set(
                e["Order_ID"] for e in self.exceptions_view
                if e.get("Approval_Status") == "APPROVED"
            )

            for _, ret_row in df_ret.iterrows():
                ret_order_id = str(ret_row.get("Order_ID")).strip()
                ret_amount = float(ret_row.get("Return_Amount", 0.0))
                ret_date_str = ret_row.get("Return_Date")

                match_indices = df_reconciled[df_reconciled["Order_ID"] == ret_order_id].index.tolist()
                if not match_indices:
                    continue

                order_date_str = df_reconciled.loc[match_indices[0], "Order_Date"]

                # Kiểm tra Return Window
                days_gap = None
                is_out_of_window = False
                if order_date_str and ret_date_str:
                    try:
                        d_order = datetime.datetime.strptime(str(order_date_str)[:10], "%Y-%m-%d")
                        d_ret = datetime.datetime.strptime(str(ret_date_str)[:10], "%Y-%m-%d")
                        days_gap = (d_ret - d_order).days
                        if days_gap > self.return_window_days:
                            is_out_of_window = True
                    except Exception:
                        pass

                # Nếu ngoài hạn và chưa được duyệt -> Đưa vào Exceptions
                if is_out_of_window and (ret_order_id not in approved_exceptions):
                    out_of_window_count += 1
                    # Kiểm tra xem đã có trong exceptions_view chưa
                    if not any(e["Order_ID"] == ret_order_id and e["Error_Type"] == "OUT_OF_WINDOW_RETURN" for e in self.exceptions_view):
                        self.exceptions_view.append({
                            "Order_ID": ret_order_id,
                            "Campaign_ID": df_reconciled.loc[match_indices[0], "Campaign_ID"],
                            "Error_Type": "OUT_OF_WINDOW_RETURN",
                            "Raw_Value": f"{ret_amount:,.0f} đ (sau {days_gap} ngày)",
                            "Normalized_Value": f"Return Window: {self.return_window_days} ngày",
                            "Severity": "HIGH",
                            "Error_Description": f"Đơn {ret_order_id} hoàn trả sau {days_gap} ngày, vượt chính sách {self.return_window_days} ngày. Số tiền hoàn: {ret_amount:,.0f} đ.",
                            "Proposed_Action": "Trưởng phòng xem xét chấp thuận hoàn tiền đặc biệt hoặc từ chối",
                            "Approval_Status": "PENDING_REVIEW",
                            "Reviewer": "Chưa duyệt",
                            "Review_Time": "N/A",
                            "Note": ""
                        })
                    continue

                # Trong hạn hoặc đã được phê duyệt -> Phân bổ hoàn trả đều theo số lượng campaign
                cmp_count = len(match_indices)
                attr_ret_per_touch = ret_amount / cmp_count

                for idx in match_indices:
                    df_reconciled.at[idx, "Attributed_Return"] += attr_ret_per_touch
                    df_reconciled.at[idx, "Return_Status"] = "Approved_Return"

                total_valid_returns += ret_amount

            # Cập nhật Net Sales
            df_reconciled["Net_Sales"] = df_reconciled["Attributed_Revenue"] - df_reconciled["Attributed_Return"]
            self.detailed_attributed_df = df_reconciled
            total_net_sales = df_reconciled["Net_Sales"].sum()

            self.log("Step 3: Return Reconciliation", "PASS",
                f"Đối soát hoàn trả hoàn tất: {len(df_ret)} đơn hoàn trả. Hợp lệ đã trừ: {total_valid_returns:,.0f} đ. Net Sales: {total_net_sales:,.0f} đ.", {
                    "valid_returns": total_valid_returns,
                    "net_sales": total_net_sales,
                    "out_of_window": out_of_window_count
                }
            )

            return {
                "name": "BƯỚC 3: Đối soát hàng hoàn trả (Return Reconciliation)",
                "status": "PASS",
                "reconciled_df": df_reconciled,
                "total_valid_returns": total_valid_returns,
                "total_net_sales": total_net_sales,
                "out_of_window_count": out_of_window_count,
                "is_applicable": True,
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
            }
        except Exception as e:
            self.log("Step 3: Return Reconciliation", "FAILED", f"Lỗi đối soát hoàn trả: {str(e)}")
            return {"name": "BƯỚC 3: Đối soát hàng hoàn trả", "status": "FAILED", "error": str(e)}

    # --- Bước 4: Cost Allocation (Activity Based Costing - ABC) ---
    def _step4_cost_allocation(self, df_reconciled: pd.DataFrame) -> Dict[str, Any]:
        self.log("Step 4: Cost Allocation", "RUNNING", "Đang phân bổ chi phí ABC (Trực tiếp & Gián tiếp)...")
        try:
            df_costs = self.data.get("Normalized_Campaign_Costs", self.data.get("Campaign_Costs"))
            has_costs = (df_costs is not None and not df_costs.empty)

            # Tổng hợp theo Campaign_ID từ dữ liệu bán hàng
            agg_kwargs = {
                "Orders_Count": ("Order_ID", "count"),
                "Attributed_Revenue": ("Attributed_Revenue", "sum"),
                "Attributed_COGS": ("Attributed_COGS", "sum"),
                "Attributed_Return": ("Attributed_Return", "sum"),
                "Net_Sales": ("Net_Sales", "sum"),
            }
            if "Attributed_Gross_Revenue" in df_reconciled.columns:
                agg_kwargs["Gross_Revenue"] = ("Attributed_Gross_Revenue", "sum")
            campaign_sales = df_reconciled.groupby("Campaign_ID").agg(**agg_kwargs).reset_index()
            if "Gross_Revenue" not in campaign_sales.columns:
                campaign_sales["Gross_Revenue"] = campaign_sales["Attributed_Revenue"]

            if not has_costs:
                # Không có dữ liệu chi phí -> Không tự bịa chi phí = 0
                campaign_sales["Direct_Cost"] = None
                campaign_sales["Allocated_Overhead"] = None
                campaign_sales["Total_Cost"] = None
                campaign_sales["Campaign_Name"] = campaign_sales["Campaign_ID"]
                campaign_sales["Channel"] = "General"

                self.log("Step 4: Cost Allocation", "PASS", "Không có dữ liệu chi phí (Campaign_Costs). Bỏ qua phân bổ ABC.")
                return {
                    "name": "BƯỚC 4: Phân bổ chi phí ABC (Cost Allocation)",
                    "status": "PASS",
                    "campaign_summary_df": campaign_sales,
                    "is_applicable": False,
                    "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
                }

            # Có dữ liệu chi phí -> Merge và phân bổ ABC
            merged = pd.merge(df_costs, campaign_sales, on="Campaign_ID", how="outer")
            merged["Campaign_Name"] = merged["Campaign_Name"].fillna(merged["Campaign_ID"])
            merged["Channel"] = merged["Channel"].fillna("General")
            merged["Direct_Cost"] = merged["Direct_Cost"].fillna(0.0)
            merged["Overhead_Cost"] = merged["Overhead_Cost"].fillna(0.0)
            merged["Orders_Count"] = merged["Orders_Count"].fillna(0)
            merged["Attributed_Revenue"] = merged["Attributed_Revenue"].fillna(0.0)
            merged["Gross_Revenue"] = merged["Gross_Revenue"].fillna(merged["Attributed_Revenue"]).fillna(0.0)
            merged["Attributed_COGS"] = merged["Attributed_COGS"].fillna(0.0)
            merged["Attributed_Return"] = merged["Attributed_Return"].fillna(0.0)
            merged["Net_Sales"] = merged["Net_Sales"].fillna(0.0)

            total_orders = max(1, merged["Orders_Count"].sum())
            total_rev = max(1.0, merged["Attributed_Revenue"].sum())

            # Phân bổ Overhead theo Cost Driver
            allocated_overheads = []
            for _, r in merged.iterrows():
                driver = str(r.get("Cost_Driver", "Order_Volume")).strip()
                ovh = float(r.get("Overhead_Cost", 0.0))
                if "revenue" in driver.lower() or "doanh thu" in driver.lower():
                    weight = float(r["Attributed_Revenue"]) / total_rev
                else:
                    weight = float(r["Orders_Count"]) / total_orders
                allocated_overheads.append(ovh * weight)

            merged["Allocated_Overhead"] = allocated_overheads
            merged["Total_Cost"] = merged["Direct_Cost"] + merged["Allocated_Overhead"]

            self.log("Step 4: Cost Allocation", "PASS", f"Phân bổ ABC thành công cho {len(merged)} chiến dịch.", {
                "campaigns_count": len(merged),
                "total_cost": merged["Total_Cost"].sum()
            })

            return {
                "name": "BƯỚC 4: Phân bổ chi phí ABC (Cost Allocation)",
                "status": "PASS",
                "campaign_summary_df": merged,
                "is_applicable": True,
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
            }
        except Exception as e:
            self.log("Step 4: Cost Allocation", "FAILED", f"Lỗi phân bổ chi phí ABC: {str(e)}")
            return {"name": "BƯỚC 4: Phân bổ chi phí ABC", "status": "FAILED", "error": str(e)}

    # --- Bước 5: Net Contribution Calculation ---
    def _step5_net_contribution(self, df_summary: pd.DataFrame) -> Dict[str, Any]:
        self.log("Step 5: Net Contribution", "RUNNING", "Đang tính toán Net Contribution, ROI và ROAS...")
        try:
            df_result = df_summary.copy(deep=True)
            has_costs = "Total_Cost" in df_result.columns and df_result["Total_Cost"].notna().any()

            if has_costs:
                # Net Contribution = Net Sales - COGS - Total Cost
                df_result["Net_Contribution"] = df_result["Net_Sales"] - df_result["Attributed_COGS"] - df_result["Total_Cost"]

                # ROAS = Attributed Revenue / Total Cost
                df_result["ROAS"] = np.where(
                    df_result["Total_Cost"] > 0,
                    df_result["Attributed_Revenue"] / df_result["Total_Cost"],
                    0.0
                )

                # ROI = (Net Contribution / Total Cost) * 100
                df_result["ROI"] = np.where(
                    df_result["Total_Cost"] > 0,
                    (df_result["Net_Contribution"] / df_result["Total_Cost"]) * 100.0,
                    0.0
                )
            else:
                df_result["Net_Contribution"] = None
                df_result["ROAS"] = None
                df_result["ROI"] = None

            self.report_result = df_result

            # Đưa cảnh báo về chiến dịch âm lợi nhuận vào Exceptions nếu có
            if has_costs:
                for _, r in df_result.iterrows():
                    cid = r["Campaign_ID"]
                    if cid != "ORGANIC_NO_CAMPAIGN" and r["Net_Contribution"] is not None and r["Net_Contribution"] < 0:
                        if not any(e["Campaign_ID"] == cid and e["Error_Type"] == "UNPROFITABLE_CAMPAIGN" for e in self.exceptions_view):
                            self.exceptions_view.append({
                                "Order_ID": "MULTIPLE_ORDERS",
                                "Campaign_ID": cid,
                                "Error_Type": "UNPROFITABLE_CAMPAIGN",
                                "Raw_Value": f"Lỗ: {r['Net_Contribution']:,.0f} đ",
                                "Normalized_Value": f"ROAS: {r['ROAS']:.2f}x",
                                "Severity": "HIGH",
                                "Error_Description": f"Chiến dịch {r['Campaign_Name']} bị lỗ Net Contribution: {r['Net_Contribution']:,.0f} đ (ROAS: {r['ROAS']:.2f}x)",
                                "Proposed_Action": "Trưởng phòng xem xét điều chỉnh ngân sách hoặc dừng chương trình",
                                "Approval_Status": "PENDING_REVIEW",
                                "Reviewer": "Chưa duyệt",
                                "Review_Time": "N/A",
                                "Note": ""
                            })

            self.log("Step 5: Net Contribution", "PASS", f"Đã tính toán hoàn tất cho {len(df_result)} chiến dịch.", {
                "has_costs": has_costs,
                "total_net_sales": df_result["Net_Sales"].sum()
            })

            return {
                "name": "BƯỚC 5: Tự động hóa tính toán (Net Contribution Automation)",
                "status": "PASS",
                "report_rows": len(df_result),
                "has_costs": has_costs,
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
            }
        except Exception as e:
            self.log("Step 5: Net Contribution", "FAILED", f"Lỗi tính toán: {str(e)}")
            return {"name": "BƯỚC 5: Tự động hóa tính toán", "status": "FAILED", "error": str(e)}

    # --- Bước 6: Campaign Decision & Human-in-the-Loop ---
    def _step6_campaign_decision(self) -> Dict[str, Any]:
        df_result = self.report_result
        has_costs = "Net_Contribution" in df_result.columns and df_result["Net_Contribution"].notna().any()

        decisions = []
        for _, r in df_result.iterrows():
            if not has_costs:
                decisions.append("DATA_INSUFFICIENT (Chưa có dữ liệu chi phí)")
            elif "MISSING_SOURCE_DATA" in str(r["Campaign_ID"]):
                decisions.append("CAMPAIGN_DATA_PENDING (Chưa gắn chiến dịch marketing)")
            elif r["Campaign_ID"] == "ORGANIC_NO_CAMPAIGN":
                decisions.append("ORGANIC_TRAFFIC (Kênh tự nhiên)")
            else:
                roas = r["ROAS"]
                net_contrib = r["Net_Contribution"]
                if roas >= 2.5 and net_contrib > 0:
                    decisions.append("SCALE (Tiếp tục thử nghiệm & Mở rộng)")
                elif roas >= 1.0 and net_contrib >= 0:
                    decisions.append("OPTIMIZE (Điều chỉnh cơ chế)")
                else:
                    decisions.append("TERMINATE (Dừng chương trình / Tối ưu khẩn cấp)")

        df_result["Strategic_Decision"] = decisions
        self.report_result = df_result

        pending_exceptions = [e for e in self.exceptions_view if e.get("Approval_Status") == "PENDING_REVIEW"]
        status = "WAITING_APPROVAL" if pending_exceptions else "PASS"

        self.log("Step 6: Campaign Decision", status,
            f"Phân loại chiến lược 3 nhóm hoàn tất. Ngoại lệ chờ Trưởng phòng duyệt: {len(pending_exceptions)} mục.", {
                "total_exceptions": len(self.exceptions_view),
                "pending_approval": len(pending_exceptions)
            }
        )

        return {
            "name": "BƯỚC 6: Ra quyết định & Phê duyệt ngoại lệ (Human-in-the-Loop)",
            "status": status,
            "total_exceptions": len(self.exceptions_view),
            "pending_approval": len(pending_exceptions),
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
        }

    # ==========================================================================
    # HUMAN-IN-THE-LOOP: PHÊ DUYỆT NGOẠI LỆ CÓ KIỂM SOÁT THẨM QUYỀN
    # ==========================================================================

    def _recover_shifted_transaction_row(self, order_id: str, exc_item: Dict[str, Any]) -> None:
        """Khôi phục COGS, Campaign_List và Source_Profit cho dòng bị lệch cột khi Trưởng phòng APPROVED."""
        df_tx = self.data.get("Normalized_Transactions")
        if df_tx is None or df_tx.empty:
            return
        mask = df_tx["Order_ID"] == order_id
        if not mask.any():
            return

        cand_curr = exc_item.get("Unmapped_Currency_Candidate")
        shifted_cmps = exc_item.get("Shifted_Campaigns") or []
        if not shifted_cmps and exc_item.get("Campaign_ID") not in (None, "", "N/A", "UNKNOWN"):
            shifted_cmps = [c.strip().upper() for c in str(exc_item["Campaign_ID"]).split(";") if c.strip()]

        for row_idx in df_tx.index[mask]:
            # 1. Khôi phục COGS từ Unmapped_Currency_Candidate (nếu có)
            row_cand = cand_curr if cand_curr is not None else df_tx.at[row_idx, "Unmapped_Currency_Candidate"] if "Unmapped_Currency_Candidate" in df_tx.columns else None
            if row_cand is not None and not pd.isna(row_cand):
                df_tx.at[row_idx, "COGS"] = float(row_cand)
                if "COGS_Status" in df_tx.columns:
                    df_tx.at[row_idx, "COGS_Status"] = "RECOVERED_APPROVED"

            # 2. Gộp các mã chiến dịch bị lệch vào Campaign_List / Campaign_List_Str / Campaign_Count
            row_shifted = list(shifted_cmps)
            if not row_shifted and "Shifted_Campaigns" in df_tx.columns:
                raw_sc = df_tx.at[row_idx, "Shifted_Campaigns"]
                if isinstance(raw_sc, str) and raw_sc.strip():
                    row_shifted = [c.strip().upper() for c in raw_sc.split(";") if c.strip()]

            if row_shifted:
                curr_list = df_tx.at[row_idx, "Campaign_List"]
                if isinstance(curr_list, list):
                    merged = list(curr_list)
                elif isinstance(curr_list, str) and curr_list.strip() not in ("", "KHONG_CO", "MISSING_SOURCE_DATA"):
                    merged = [c.strip().upper() for c in curr_list.split(";") if c.strip()]
                else:
                    merged = []
                for c in row_shifted:
                    if c not in merged:
                        merged.append(c)
                df_tx.at[row_idx, "Campaign_List"] = merged
                df_tx.at[row_idx, "Campaign_List_Str"] = "; ".join(merged)
                df_tx.at[row_idx, "Campaign_Count"] = len(merged)

            # 3. Tính lại Source_Profit = Order_Value - COGS khi đủ dữ liệu
            ov = df_tx.at[row_idx, "Order_Value"]
            cg = df_tx.at[row_idx, "COGS"]
            if ov is not None and not pd.isna(ov) and cg is not None and not pd.isna(cg):
                df_tx.at[row_idx, "Source_Profit"] = float(ov) - float(cg)
                if "Formula_Status" in df_tx.columns:
                    df_tx.at[row_idx, "Formula_Status"] = "COMPUTED_NET_MINUS_COGS"

    def resolve_exception(
        self,
        order_id: str,
        action: str,
        reviewer_role: str,
        reviewer_name: str = "Admin",
        note: Optional[str] = None,
        error_type: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Phê duyệt hoặc từ chối ngoại lệ với kiểm soát thẩm quyền chặt chẽ:
        - Lọc theo cặp (Order_ID, Error_Type) khi có error_type.
        - Tự động khôi phục dữ liệu lệch cột (CAMPAIGN_IN_COGS_COLUMN) khi APPROVED.
        """
        if reviewer_role not in self.AUTHORIZED_ROLES:
            return False, f"Từ chối thao tác: Vai trò '{reviewer_role}' không có thẩm quyền phê duyệt ngoại lệ (Yêu cầu: Trưởng phòng Marketing hoặc Quản trị viên)."

        def _match(e: Dict[str, Any]) -> bool:
            return e.get("Order_ID") == order_id and (error_type is None or e.get("Error_Type") == error_type)

        raw_name = str(reviewer_name or "").strip()
        if note is None and raw_name:
            # Hỗ trợ tương thích lời gọi 4 tham số: (order_id, action, reviewer_role, note)
            clean_note = raw_name
            clean_name = str(reviewer_role or "Admin").strip()
        else:
            clean_note = str(note or "").strip()
            clean_name = raw_name or "Admin"

        if not clean_note and action in ["APPROVE", "CHẤP THUẬN", "APPROVED"]:
            target_items = [e for e in self.exceptions_view if _match(e)]
            if target_items and target_items[0].get("Severity") in ["CRITICAL", "HIGH"]:
                return False, f"Bắt buộc nhập lý do / ghi chú giải trình khi phê duyệt ngoại lệ có độ rủi ro {target_items[0].get('Severity')}."

        updated = False
        action_std = "APPROVED" if "APPROVE" in action.upper() else ("REJECTED" if "REJECT" in action.upper() else "CORRECTION_REQUESTED")

        for e in self.exceptions_view:
            if _match(e):
                e["Approval_Status"] = action_std
                e["Reviewer"] = f"{clean_name} ({reviewer_role})"
                e["Review_Time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                e["Note"] = clean_note
                updated = True

                if action_std == "APPROVED" and e.get("Error_Type") == "CAMPAIGN_IN_COGS_COLUMN":
                    self._recover_shifted_transaction_row(order_id, e)

                self.approval_history.append({
                    "Order_ID": order_id,
                    "Error_Type": e.get("Error_Type", ""),
                    "Action": action_std,
                    "Reviewer": clean_name,
                    "Role": reviewer_role,
                    "Timestamp": e["Review_Time"],
                    "Note": clean_note
                })

        if updated:
            self.log("Human-in-the-Loop", "PASS", f"Đã cập nhật trạng thái {action_std} cho ngoại lệ {order_id} bởi {clean_name}.")
            self.run_process_workflow()
            return True, f"Phê duyệt thành công: Đã chuyển trạng thái sang {action_std} cho {order_id}."
        else:
            return False, f"Không tìm thấy ngoại lệ với mã: {order_id}."

    # ==========================================================================
    # GIAI ĐOẠN 4: VERIFICATION (7 PHÉP KIỂM TOÁN TỰ ĐỘNG)
    # ==========================================================================

    def run_verification(self) -> Dict[str, Any]:
        """
        Thực hiện 7 phép kiểm toán tự động theo đúng tiêu chuẩn hệ thống:
        CHK-01: Schema và tính đầy đủ dữ liệu.
        CHK-02: Tính duy nhất của Order_ID và Return_ID.
        CHK-03: Tính hợp lệ của giá trị tiền tệ.
        CHK-04: Đối soát tổng doanh thu phân bổ với doanh thu nguồn.
        CHK-05: Đối soát hoàn trả và ngăn trừ trùng.
        CHK-06: Kiểm tra ngoại lệ và phê duyệt hợp lệ.
        CHK-07: Đối soát chi phí và Net Contribution.
        """
        tests = []
        is_all_applicable_pass = True

        df_tx = self.data.get("Normalized_Transactions", self.data.get("Transactions"))
        df_ret = self.data.get("Normalized_Returns", self.data.get("Returns"))
        df_costs = self.data.get("Normalized_Campaign_Costs", self.data.get("Campaign_Costs"))

        has_ret = (df_ret is not None and not df_ret.empty)
        has_costs = (df_costs is not None and not df_costs.empty)

        # CHK-01: Schema và tính đầy đủ dữ liệu
        req_cols = ["Order_ID", "Order_Value", "Campaign_List"]
        present_cols = [c for c in req_cols if c in df_tx.columns] if df_tx is not None else []
        t1_pass = (len(present_cols) == len(req_cols))
        tests.append({
            "code": "CHK-01",
            "name": "Kiểm tra Schema & Tính Đầy Đủ Dữ Liệu",
            "condition": "Bắt buộc có đầy đủ các trường: Order_ID, Order_Value, Campaign_List",
            "expected": f"Đầy đủ {len(req_cols)} trường cốt lõi",
            "actual": f"Có {len(present_cols)}/{len(req_cols)} trường ({', '.join(present_cols)})",
            "status": "PASS" if t1_pass else "FAIL",
            "impact": "Cơ sở dữ liệu đầu vào cho toàn bộ thuật toán phân tích"
        })
        if not t1_pass: is_all_applicable_pass = False

        # CHK-02: Tính duy nhất của Order_ID và Return_ID
        unresolved_dups = [
            e for e in self.exceptions_view
            if e.get("Error_Type") == "DUPLICATE_ORDER_ID" and e.get("Approval_Status") == "PENDING_REVIEW"
        ]
        t2_pass = (len(unresolved_dups) == 0)
        tests.append({
            "code": "CHK-02",
            "name": "Tính Duy Nhất Của Order_ID & Return_ID",
            "condition": "Không còn mã đơn trùng lặp chưa được Trưởng phòng phê duyệt giải trình",
            "expected": "0 đơn trùng chưa duyệt",
            "actual": f"Còn {len(unresolved_dups)} đơn trùng đang chờ duyệt",
            "status": "PASS" if t2_pass else "FAIL",
            "impact": "Tránh nhân đôi doanh thu và giao dịch ảo"
        })
        if not t2_pass: is_all_applicable_pass = False

        # CHK-03: Tính hợp lệ của giá trị tiền tệ
        unresolved_curr_errors = [
            e for e in self.exceptions_view
            if e.get("Error_Type") in ["INVALID_CURRENCY_FORMAT", "NEGATIVE_CURRENCY"] and e.get("Approval_Status") == "PENDING_REVIEW"
        ]
        t3_pass = (len(unresolved_curr_errors) == 0)
        tests.append({
            "code": "CHK-03",
            "name": "Tính Hợp Lệ Của Giá Trị Tiền Tệ",
            "condition": "Không có giá trị tiền tệ âm hoặc sai định dạng chưa qua phê duyệt",
            "expected": "0 lỗi tiền tệ chưa duyệt",
            "actual": f"Còn {len(unresolved_curr_errors)} lỗi tiền tệ chờ xử lý",
            "status": "PASS" if t3_pass else "FAIL",
            "impact": "Đảm bảo tính chính xác tuyệt đối của số tiền đối soát"
        })
        if not t3_pass: is_all_applicable_pass = False

        # CHK-04: Đối soát tổng doanh thu phân bổ với doanh thu nguồn
        if self.detailed_attributed_df is not None:
            total_attr = self.detailed_attributed_df["Attributed_Revenue"].sum()
            active_df = self.get_active_transactions_df()
            valid_source = float(pd.to_numeric(active_df["Order_Value"], errors="coerce").fillna(0.0).sum()) if active_df is not None else 0.0
            diff_rev = abs(valid_source - total_attr)
            t4_pass = (diff_rev < 0.01)
            tests.append({
                "code": "CHK-04",
                "name": "Đối Soát Doanh Thu Phân Bổ Với Nguồn",
                "condition": "Tổng Attributed Revenue == Tổng Doanh thu nguồn hợp lệ (Độ lệch < 0.01)",
                "expected": f"{valid_source:,.0f} đ",
                "actual": f"{total_attr:,.0f} đ (Lệch: {diff_rev:.2f} đ)",
                "status": "PASS" if t4_pass else "FAIL",
                "impact": "Chứng minh thuật toán Multi-touch không làm thất thoát hoặc tạo khống doanh thu"
            })
            if not t4_pass: is_all_applicable_pass = False
        else:
            tests.append({
                "code": "CHK-04",
                "name": "Đối Soát Doanh Thu Phân Bổ Với Nguồn",
                "condition": "Chưa hoàn tất bước phân bổ doanh thu",
                "expected": "Hoàn tất Process",
                "actual": "Chưa chạy Process",
                "status": "FAIL",
                "impact": "Chưa có số liệu phân bổ"
            })
            is_all_applicable_pass = False

        # CHK-05: Đối soát hoàn trả và ngăn trừ trùng
        if has_ret:
            unresolved_returns = [
                e for e in self.exceptions_view
                if e.get("Error_Type") == "OUT_OF_WINDOW_RETURN" and e.get("Approval_Status") == "PENDING_REVIEW"
            ]
            t5_pass = (len(unresolved_returns) == 0)
            tests.append({
                "code": "CHK-05",
                "name": "Đối Soát Hoàn Trả & Ngăn Trừ Trùng",
                "condition": "Toàn bộ đơn hoàn ngoài Return Window phải được Trưởng phòng duyệt",
                "expected": "0 đơn hoàn ngoài hạn chưa duyệt",
                "actual": f"Còn {len(unresolved_returns)} đơn hoàn ngoài hạn chờ duyệt",
                "status": "PASS" if t5_pass else "FAIL",
                "impact": "Tránh khấu trừ hoàn trả sai chính sách"
            })
            if not t5_pass: is_all_applicable_pass = False
        else:
            tests.append({
                "code": "CHK-05",
                "name": "Đối Soát Hoàn Trả & Ngăn Trừ Trùng",
                "condition": "Bảng tính không có dữ liệu hoàn trả (Returns Tab)",
                "expected": "Có dữ liệu hoàn trả",
                "actual": "Dữ liệu hoàn trả chưa được cung cấp",
                "status": "NOT_APPLICABLE",
                "impact": "Bỏ qua phép kiểm hoàn trả một cách an toàn và minh bạch"
            })

        # CHK-06: Kiểm tra ngoại lệ và phê duyệt hợp lệ (Human-in-the-Loop)
        pending_all = [e for e in self.exceptions_view if e.get("Approval_Status") == "PENDING_REVIEW"]
        t6_pass = (len(pending_all) == 0)
        tests.append({
            "code": "CHK-06",
            "name": "Kiểm Tra Ngoại Lệ & Phê Duyệt Hợp Lệ (Human-in-the-Loop)",
            "condition": "Toàn bộ ngoại lệ phải được người có thẩm quyền phê duyệt trước khi phát hành",
            "expected": "0 ngoại lệ chờ duyệt",
            "actual": f"Còn {len(pending_all)} ngoại lệ chưa được duyệt",
            "status": "PASS" if t6_pass else "FAIL",
            "impact": "Đảm bảo tính chịu trách nhiệm của cấp quản lý trước khi xuất báo cáo"
        })
        if not t6_pass: is_all_applicable_pass = False

        # CHK-07: Đối soát chi phí và Net Contribution
        if has_costs and self.report_result is not None:
            df_res = self.report_result
            ns_s = pd.to_numeric(df_res["Net_Sales"], errors="coerce").fillna(0.0)
            cg_s = pd.to_numeric(df_res["Attributed_COGS"], errors="coerce").fillna(0.0)
            tc_s = pd.to_numeric(df_res["Total_Cost"], errors="coerce").fillna(0.0)
            nc_s = pd.to_numeric(df_res["Net_Contribution"], errors="coerce").fillna(0.0)
            diff_series = abs((ns_s - cg_s - tc_s) - nc_s)
            calc_diff = safe_float(diff_series.max(), 0.0) if not diff_series.empty else 0.0
            t7_pass = (calc_diff < 0.01)
            tests.append({
                "code": "CHK-07",
                "name": "Đối Soát Chi Phí ABC & Net Contribution",
                "condition": "Net Contribution = Net Sales - COGS - Total ABC Cost (Khớp tuyệt đối)",
                "expected": "Khớp công thức 100%",
                "actual": f"Độ lệch tối đa: {calc_diff:.4f} đ",
                "status": "PASS" if t7_pass else "FAIL",
                "impact": "Bảo đảm báo cáo tài chính tuân thủ chuẩn kế toán quản trị"
            })
            if not t7_pass: is_all_applicable_pass = False
        else:
            tests.append({
                "code": "CHK-07",
                "name": "Đối Soát Chi Phí ABC & Net Contribution",
                "condition": "Bảng tính không có dữ liệu chi phí chiến dịch (Campaign_Costs Tab)",
                "expected": "Có dữ liệu chi phí",
                "actual": "Dữ liệu chi phí chưa được cung cấp",
                "status": "NOT_APPLICABLE",
                "impact": "Không thể kiểm toán Net Contribution khi chưa có số liệu chi phí"
            })

        pass_count = sum(1 for t in tests if t["status"] == "PASS")
        fail_count = sum(1 for t in tests if t["status"] == "FAIL")
        na_count = sum(1 for t in tests if t["status"] == "NOT_APPLICABLE")

        self.verification_results = {
            "overall_status": "PASS" if is_all_applicable_pass else "FAIL",
            "tests": tests,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "na_count": na_count,
            "total_tests": len(tests),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        return self.verification_results

    # ==========================================================================
    # GIAI ĐOẠN 5: XUẤT BÁO CÁO HTML STANDALONE
    # ==========================================================================

    def generate_html_report(self, quality_summary: Optional[Dict[str, Any]] = None) -> str:
        """Sinh file HTML Dashboard & Báo cáo Quản trị Kiểm toán doanh nghiệp, độc lập hoàn toàn."""
        if self.report_result is None:
            return "<h1>Báo cáo chưa được khởi tạo. Vui lòng chạy quy trình PROCESS trước.</h1>"

        df_res = self.report_result
        has_costs = "Total_Cost" in df_res.columns and df_res["Total_Cost"].notna().any()

        total_gross = safe_float(df_res["Attributed_Revenue"].sum(), 0.0)
        total_gross_rev = safe_float(df_res["Gross_Revenue"].sum(), total_gross) if "Gross_Revenue" in df_res.columns else total_gross
        total_cogs = safe_float(df_res["Attributed_COGS"].sum(), 0.0)
        total_net_sales = safe_float(df_res["Net_Sales"].sum(), 0.0)
        total_returns = safe_float(df_res["Attributed_Return"].sum(), 0.0)
        total_costs = safe_float(df_res["Total_Cost"].sum(), 0.0) if has_costs else 0.0
        total_net_contrib = safe_float(df_res["Net_Contribution"].sum(), 0.0) if has_costs else None

        active_tx = self.get_active_transactions_df()
        narratives = build_enterprise_report_narratives(
            df_campaign_metrics=df_res,
            cleaning_report=quality_summary or self.quality_summary or self.data.get("Quality_Summary"),
            exceptions_df=self.exceptions_view,
            verification_results=self.verification_results,
            config={
                "return_window_days": self.return_window_days,
                "total_orders": len(active_tx) if active_tx is not None else None,
            },
            raw_or_cleaned_data=self.data,
        )

        rows_html = ""
        for _, r in df_res.iterrows():
            cid = _esc(r["Campaign_ID"])
            cname = _esc(r["Campaign_Name"])
            rev = safe_float(r["Attributed_Revenue"], 0.0)
            ret = safe_float(r["Attributed_Return"], 0.0)
            cogs = safe_float(r["Attributed_COGS"], 0.0)
            ns = safe_float(r["Net_Sales"], 0.0)
            cost = r["Total_Cost"] if has_costs else None
            nc = r["Net_Contribution"] if has_costs else None
            roas = r["ROAS"] if has_costs else None
            roi = r["ROI"] if has_costs else None
            dec = str(r.get("Strategic_Decision", "N/A"))

            badge_color = "#27845E" if "SCALE" in dec else ("#D69A3B" if "OPTIMIZE" in dec else ("#C21F20" if "TERMINATE" in dec else "#766A68"))

            rows_html += f"""
            <tr>
                <td><b>{cname}</b><br><span style="font-size:11px; color:#766A68;">{cid} • {_esc(r.get('Channel', 'N/A'))}</span></td>
                <td style="text-align:right;">{rev:,.0f} đ</td>
                <td style="text-align:right; color:#C21F20;">{ret:,.0f} đ</td>
                <td style="text-align:right; color:#766A68;">{cogs:,.0f} đ</td>
                <td style="text-align:right; font-weight:600; color:#5277A6;">{ns:,.0f} đ</td>
                <td style="text-align:right;">{f"{safe_float(cost):,.0f} đ" if is_valid_num(cost) else "<i>Chưa có</i>"}</td>
                <td style="text-align:right; font-weight:700; color:{'#27845E' if (is_valid_num(nc) and safe_float(nc) >= 0) else '#C21F20'};">{f"{safe_float(nc):,.0f} đ" if is_valid_num(nc) else "<i>Chưa có</i>"}</td>
                <td style="text-align:center;">{f"{safe_float(roas):.2f}x" if is_valid_num(roas) else "N/A"}</td>
                <td style="text-align:center;">{f"{safe_float(roi):+.1f}%" if is_valid_num(roi) else "N/A"}</td>
                <td style="text-align:center;"><span style="background:{badge_color}; color:#FFF; font-size:11px; font-weight:600; padding:4px 8px; border-radius:6px;">{_esc(dec.split(' ')[0])}</span></td>
            </tr>
            """

        exc_html = ""
        for idx, e in enumerate(self.exceptions_view):
            status_color = "#27845E" if e.get("Approval_Status") == "APPROVED" else ("#C21F20" if e.get("Approval_Status") == "REJECTED" else "#D69A3B")
            exc_html += f"""
            <tr>
                <td>{idx+1}</td>
                <td><b>{_esc(e.get('Order_ID'))}</b></td>
                <td><span style="background:#F8EDE6; color:#292326; padding:2px 6px; border-radius:4px; font-size:11px;">{_esc(e.get('Error_Type'))}</span></td>
                <td>{_esc(e.get('Error_Description'))}</td>
                <td><span style="color:{status_color}; font-weight:700;">{_esc(e.get('Approval_Status'))}</span><br><small style="color:#766A68;">{_esc(e.get('Reviewer', 'N/A'))}</small></td>
                <td><i>{_esc(e.get('Note') or 'Không có')}</i></td>
            </tr>
            """

        html = f"""<!DOCTYPE html>
<html lang="vi" translate="no" class="notranslate">
<head>
    <meta charset="UTF-8">
    <meta name="google" content="notranslate">
    <title>Data Forge — Hệ thống Phân tích &amp; Kiểm toán Dữ liệu Doanh nghiệp</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', 'Segoe UI', sans-serif; background: radial-gradient(ellipse 56% 48% at 4% 8%, rgba(107, 23, 46, 0.34) 0%, transparent 70%), radial-gradient(ellipse 52% 46% at 96% 12%, rgba(142, 30, 62, 0.26) 0%, transparent 68%), radial-gradient(ellipse 50% 46% at 16% 94%, rgba(123, 30, 54, 0.24) 0%, transparent 72%), linear-gradient(135deg, #FBECEF 0%, #F4DCE0 46%, #F0D1D8 100%); color: #292326; margin: 0; padding: 26px; line-height: 1.5; }}
        .report-shell {{ max-width: 1220px; margin: 0 auto; }}
        .report-header {{ background: linear-gradient(125deg, #FFFFFF 0%, #FBF0EC 42%, #7C1F27 100%); border: 1px solid #EADDD5; border-top: 5px solid #C21F20; border-radius: 20px; padding: 24px 28px; margin-bottom: 18px; box-shadow: 0 8px 24px rgba(109, 27, 41, 0.10); }}
        .header-title {{ font-family: 'Plus Jakarta Sans', 'Inter', sans-serif; font-size: 21px; font-weight: 800; color: #292326; }}
        .header-sub {{ font-size: 13px; color: #766A68; margin-top: 4px; }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 18px; }}
        .kpi-card {{ background: #FFFFFF; border: 1px solid #EADDD5; border-top: 3px solid #C21F20; border-radius: 18px; padding: 18px 20px; box-shadow: 0 4px 16px rgba(41, 35, 38, 0.05); transition: transform 0.28s ease, box-shadow 0.28s ease; }}
        .kpi-card:hover {{ transform: translateY(-4px); box-shadow: 0 12px 28px rgba(41, 35, 38, 0.09); }}
        .kpi-label {{ font-family: 'Plus Jakarta Sans', 'Inter', sans-serif; font-size: 11.5px; color: #766A68; text-transform: uppercase; font-weight: 700; }}
        .kpi-value {{ font-family: 'Plus Jakarta Sans', 'Inter', sans-serif; font-size: 23px; font-weight: 800; color: #292326; margin-top: 4px; font-variant-numeric: tabular-nums; }}
        .section-card {{ background: #FFFFFF; border: 1px solid #EADDD5; border-radius: 18px; padding: 22px 24px; margin-bottom: 18px; box-shadow: 0 4px 16px rgba(41, 35, 38, 0.05); transition: transform 0.28s ease, box-shadow 0.28s ease; }}
        .section-card:hover {{ transform: translateY(-2px); box-shadow: 0 12px 26px rgba(41, 35, 38, 0.08); }}
        .section-title {{ font-family: 'Plus Jakarta Sans', 'Inter', sans-serif; font-size: 15px; font-weight: 800; margin-bottom: 14px; display: flex; align-items: center; gap: 8px; text-transform: uppercase; color: #292326; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; border-radius: 14px; overflow: hidden; }}
        th {{ font-family: 'Plus Jakarta Sans', 'Inter', sans-serif; background: #F8EDE6; color: #6D1B29; font-weight: 700; text-align: left; padding: 11px 12px; border-bottom: 2px solid #EADDD5; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #F2E7E0; color: #292326; }}
        tr:hover {{ background: #FFF8F0; }}
        {ENTERPRISE_NARRATIVE_CSS}
    </style>
</head>
<body>
    <div class="report-shell">
        <div class="report-header">
            <div class="header-title">BÁO CÁO HIỆU QUẢ MARKETING CAMPAIGN &amp; ĐỐI SOÁT TÀI CHÍNH QUẢN TRỊ</div>
            <div class="header-sub">Enterprise BI &amp; Data Governance • Multi-touch Attribution • Activity Based Costing • Xuất ngày: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
        </div>

        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Tổng Doanh Thu Gộp (Gross Revenue)</div>
                <div class="kpi-value">{total_gross_rev:,.0f} đ</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Net Sales (Sau hoàn)</div>
                <div class="kpi-value" style="color:#5277A6;">{total_net_sales:,.0f} đ</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Chi Phí ABC</div>
                <div class="kpi-value" style="color:#D69A3B;">{f"{total_costs:,.0f} đ" if has_costs else "Chưa cung cấp"}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Net Contribution</div>
                <div class="kpi-value" style="color:{'#27845E' if (total_net_contrib is not None and total_net_contrib >= 0) else '#C21F20'};">{f"{total_net_contrib:,.0f} đ" if total_net_contrib is not None else "Chưa cung cấp"}</div>
            </div>
        </div>

        {narratives["block1_executive_mda"]}
        {narratives["block2_data_governance"]}

        <div class="section-card">
            <div class="section-title">📊 HIỆU QUẢ TỪNG CHIẾN DỊCH (MULTI-TOUCH ATTRIBUTION &amp; ABC COSTING)</div>
            <table>
                <thead>
                    <tr>
                        <th>Chiến Dịch</th>
                        <th style="text-align:right;">Doanh Thu Phân Bổ</th>
                        <th style="text-align:right;">Hoàn Trả</th>
                        <th style="text-align:right;">Giá Vốn (COGS)</th>
                        <th style="text-align:right;">Net Sales</th>
                        <th style="text-align:right;">Chi Phí ABC</th>
                        <th style="text-align:right;">Net Contribution</th>
                        <th style="text-align:center;">ROAS</th>
                        <th style="text-align:center;">ROI (%)</th>
                        <th style="text-align:center;">Quyết Định Chiến Lược</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
            {narratives["revenue_chart_html"]}
            {narratives["abc_cost_chart_html"]}
        </div>

        {narratives["block4_internal_control"]}
        {narratives["block5_decision_matrix"]}

        <div class="section-card">
            <div class="section-title">💡 KHUYẾN NGHỊ KINH DOANH CHIẾN LƯỢC (QUY TẮC 3 NHÓM HÀNH ĐỘNG)</div>
            <div style="font-size:13px; line-height:1.65;">
                <p><b>1. TIẾP TỤC THỬ NGHIỆM &amp; MỞ RỘNG (SCALE):</b> Dành cho các chiến dịch có ROAS &ge; 2.5x và Net Contribution dương bền vững.</p>
                <p><b>2. ĐIỀU CHỈNH CƠ CHẾ (OPTIMIZE):</b> Dành cho các chiến dịch hòa vốn hoặc biên lợi nhuận thấp, cần đàm phán giảm chi phí tiếp thị hoặc tối ưu tệp khách hàng.</p>
                <p><b>3. DỪNG CHƯƠNG TRÌNH (TERMINATE):</b> Dành cho các chiến dịch âm lợi nhuận sâu, chuyển ngân sách sang các kênh chuyển đổi cao.</p>
            </div>
        </div>

        <div class="section-card">
            <div class="section-title">⚠️ DANH SÁCH NGOẠI LỆ &amp; LỊCH SỬ PHÊ DUYỆT (HUMAN-IN-THE-LOOP)</div>
            <table>
                <thead>
                    <tr>
                        <th>STT</th>
                        <th>Mã Đơn</th>
                        <th>Loại Lỗi</th>
                        <th>Mô Tả</th>
                        <th>Trạng Thái &amp; Người Duyệt</th>
                        <th>Ghi Chú Giải Trình</th>
                    </tr>
                </thead>
                <tbody>
                    {exc_html if exc_html else "<tr><td colspan='6' style='text-align:center;'>Không có ngoại lệ nào phát sinh.</td></tr>"}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>"""
        return html

    def generate_enterprise_audit_excel_pack(
        self,
        quality_summary: Optional[Dict[str, Any]] = None,
        cleaning_errors: Optional[List[Dict[str, Any]]] = None,
        audit_log: Optional[List[Dict[str, Any]]] = None,
        reconciliation_table: Optional[List[Dict[str, Any]]] = None,
    ) -> bytes:
        """
        Xuất gói Hồ sơ Kiểm toán Excel đa Sheet chuẩn Enterprise SaaS:
        1. 01_Executive_Summary
        2. 02_Campaign_P&L_ABC
        3. 03_Cleaned_Data_Sample
        4. 04_Quarantine_&_Exceptions
        5. 05_System_Audit_Log
        """
        def _safe_df(df_in: Any) -> pd.DataFrame:
            if df_in is None:
                return pd.DataFrame()
            if isinstance(df_in, list):
                df_in = pd.DataFrame(df_in) if df_in else pd.DataFrame()
            if not isinstance(df_in, pd.DataFrame) or df_in.empty:
                return pd.DataFrame()
            out = df_in.copy()
            for col in out.columns:
                if out[col].dtype == "object":
                    out[col] = out[col].apply(
                        lambda v: re.sub(
                            r"[\x00-\x08\x0b\x0c\x0e-\x1f]",
                            "",
                            ", ".join(map(str, v)) if isinstance(v, (list, tuple, set)) else ("" if (v is None or (isinstance(v, float) and pd.isna(v))) else str(v)),
                        )
                    )
            return out

        q_sum = quality_summary or self.quality_summary or self.data.get("Quality_Summary") or {}
        df_rep = _safe_df(self.report_result)
        active_tx = self.get_active_transactions_df()
        df_tx_sample = _safe_df(active_tx.head(1000) if (active_tx is not None and not active_tx.empty) else self.data.get("Normalized_Transactions"))
        df_quar = _safe_df(self.data.get("Quarantined_Records"))
        df_exc = _safe_df(self.exceptions_view)
        df_err = _safe_df(cleaning_errors or [])
        df_au = _safe_df((audit_log or [])[:1500])
        df_proc = _safe_df(self.processing_log)
        df_app = _safe_df(self.approval_history)
        ver_res = self.verification_results or {}
        df_ver = _safe_df(ver_res.get("tests") or [])
        rec_list = reconciliation_table if reconciliation_table is not None else q_sum.get("Reconciliation_Table", [])
        df_rec = _safe_df(rec_list)

        narr = build_enterprise_report_narratives(
            df_campaign_metrics=self.report_result,
            cleaning_report=q_sum,
            exceptions_df=self.exceptions_view,
            verification_results=ver_res,
            config={
                "return_window_days": self.return_window_days,
                "total_orders": len(active_tx) if active_tx is not None else None,
            },
            raw_or_cleaned_data=self.data,
        )
        m = narr.get("metrics", {})
        has_costs = self.report_result is not None and "Total_Cost" in self.report_result.columns and self.report_result["Total_Cost"].notna().any()

        summary_rows = [
            {"Chỉ tiêu Điều hành": "Thời điểm xuất Hồ sơ Kiểm toán", "Giá trị": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Ghi chú": "Data Forge Enterprise BI"},
            {"Chỉ tiêu Điều hành": "Trạng thái Làm sạch Dữ liệu", "Giá trị": str(q_sum.get("Status", "N/A")), "Ghi chú": str(q_sum.get("Quota_Status_Text", "TRONG ĐỊNH MỨC"))},
            {"Chỉ tiêu Điều hành": "Điểm Tín nhiệm Dữ liệu (Data Quality Score)", "Giá trị": f"{safe_float(q_sum.get('Data_Quality_Score', m.get('quality_score', 100.0))):.1f}/100", "Ghi chú": f"Số dòng gốc: {int(safe_float(q_sum.get('Raw_Transactions_Count', m.get('total_orders', 0)))):,}"},
            {"Chỉ tiêu Điều hành": "Tổng số Đơn hàng Hợp lệ", "Giá trị": int(m.get("total_orders", len(active_tx) if active_tx is not None else 0)), "Ghi chú": f"{int(m.get('total_campaigns', len(df_rep)))} nhóm chiến dịch"},
            {"Chỉ tiêu Điều hành": "Tổng Doanh thu Gộp (Gross Revenue)", "Giá trị": float(m.get("gross_revenue", 0.0)), "Ghi chú": "Trước chiết khấu và hoàn trả"},
            {"Chỉ tiêu Điều hành": "Tổng Doanh thu Phân bổ (Attributed Revenue)", "Giá trị": float(m.get("attributed_revenue", 0.0)), "Ghi chú": "Sau giảm giá thương mại"},
            {"Chỉ tiêu Điều hành": "Giảm trừ Hoàn trả (Attributed Return)", "Giá trị": float(m.get("attributed_return", 0.0)), "Ghi chú": f"Return Window: {self.return_window_days} ngày ({float(m.get('return_rate', 0.0)):.2f}%)"},
            {"Chỉ tiêu Điều hành": "Doanh thu Thuần (Net Sales)", "Giá trị": float(m.get("net_sales", 0.0)), "Ghi chú": "Doanh thu thực nhận sau hoàn trả"},
            {"Chỉ tiêu Điều hành": "Chi phí Trực tiếp (Direct Cost)", "Giá trị": float(m.get("direct_cost", 0.0)) if has_costs else "Chưa cung cấp", "Ghi chú": "Theo tab Campaign_Costs"},
            {"Chỉ tiêu Điều hành": "Chi phí Chung Phân bổ (Allocated Overhead ABC)", "Giá trị": float(m.get("allocated_overhead", 0.0)) if has_costs else "Chưa cung cấp", "Ghi chú": "Phân bổ theo Cost Driver"},
            {"Chỉ tiêu Điều hành": "Tổng Chi phí ABC (Total Cost)", "Giá trị": float(m.get("total_cost", 0.0)) if has_costs else "Chưa cung cấp", "Ghi chú": "Direct Cost + Allocated Overhead"},
            {"Chỉ tiêu Điều hành": "Lợi nhuận Đóng góp Ròng (Net Contribution)", "Giá trị": float(m.get("net_contribution", 0.0)) if has_costs else "Chưa cung cấp", "Ghi chú": f"ROI: {float(m.get('total_roi', 0.0)):+.1f}% | ROAS: {float(m.get('total_roas', 0.0)):.2f}x" if has_costs else "Cần dữ liệu chi phí"},
            {"Chỉ tiêu Điều hành": "Kết quả Kiểm toán Hệ thống (Verification Gate)", "Giá trị": str(ver_res.get("overall_status", "NOT_RUN")), "Ghi chú": f"{ver_res.get('pass_count', 0)} PASS / {ver_res.get('na_count', 0)} N/A / {ver_res.get('fail_count', 0)} FAIL"},
            {"Chỉ tiêu Điều hành": "Số dòng bị Cách ly (Data Quarantine)", "Giá trị": len(df_quar), "Ghi chú": f"Giới hạn MAX_ROW_LIMIT = {int(safe_float(q_sum.get('Max_Row_Limit', 20000))):,}"},
        ]
        df_exec = pd.DataFrame(summary_rows)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # Sheet 1: 01_Executive_Summary
            df_exec.to_excel(writer, sheet_name="01_Executive_Summary", index=False, startrow=0)
            if not df_rec.empty:
                df_rec.to_excel(writer, sheet_name="01_Executive_Summary", index=False, startrow=len(df_exec) + 3)

            # Sheet 2: 02_Campaign_P&L_ABC
            if df_rep.empty:
                pd.DataFrame([{"Thông báo": "Chưa có dữ liệu báo cáo chiến dịch (cần chạy Process 6 bước)."}]).to_excel(
                    writer, sheet_name="02_Campaign_P&L_ABC", index=False
                )
            else:
                df_rep.to_excel(writer, sheet_name="02_Campaign_P&L_ABC", index=False)

            # Sheet 3: 03_Cleaned_Data_Sample
            if df_tx_sample.empty:
                pd.DataFrame([{"Thông báo": "Chưa có dữ liệu giao dịch sau chuẩn hóa."}]).to_excel(
                    writer, sheet_name="03_Cleaned_Data_Sample", index=False
                )
            else:
                df_tx_sample.to_excel(writer, sheet_name="03_Cleaned_Data_Sample", index=False)

            # Sheet 4: 04_Quarantine_&_Exceptions
            cur_r4 = 0
            if not df_exc.empty:
                pd.DataFrame([{"Phần": "I. DANH SÁCH NGOẠI LỆ CHỜ/ĐÃ PHÊ DUYỆT (HITL EXCEPTIONS)"}]).to_excel(
                    writer, sheet_name="04_Quarantine_&_Exceptions", index=False, header=False, startrow=cur_r4
                )
                df_exc.to_excel(writer, sheet_name="04_Quarantine_&_Exceptions", index=False, startrow=cur_r4 + 1)
                cur_r4 += len(df_exc) + 4
            if not df_quar.empty:
                pd.DataFrame([{"Phần": "II. DỮ LIỆU CÁCH LY VƯỢT NGƯỠNG QUOTA (DATA QUARANTINE)"}]).to_excel(
                    writer, sheet_name="04_Quarantine_&_Exceptions", index=False, header=False, startrow=cur_r4
                )
                df_quar.to_excel(writer, sheet_name="04_Quarantine_&_Exceptions", index=False, startrow=cur_r4 + 1)
                cur_r4 += len(df_quar) + 4
            if not df_err.empty:
                pd.DataFrame([{"Phần": "III. NHẬT KÝ CẢNH BÁO & LỖI LÀM SẠCH"}]).to_excel(
                    writer, sheet_name="04_Quarantine_&_Exceptions", index=False, header=False, startrow=cur_r4
                )
                df_err.to_excel(writer, sheet_name="04_Quarantine_&_Exceptions", index=False, startrow=cur_r4 + 1)
                cur_r4 += len(df_err) + 4
            if cur_r4 == 0:
                pd.DataFrame([{"Trạng thái": "Không phát sinh ngoại lệ hoặc bản ghi cách ly."}]).to_excel(
                    writer, sheet_name="04_Quarantine_&_Exceptions", index=False
                )

            # Sheet 5: 05_System_Audit_Log
            cur_r5 = 0
            if not df_ver.empty:
                pd.DataFrame([{"Phần": "I. KẾT QUẢ 7 PHÉP KIỂM TOÁN TỰ ĐỘNG (CHK-01 .. CHK-07)"}]).to_excel(
                    writer, sheet_name="05_System_Audit_Log", index=False, header=False, startrow=cur_r5
                )
                df_ver.to_excel(writer, sheet_name="05_System_Audit_Log", index=False, startrow=cur_r5 + 1)
                cur_r5 += len(df_ver) + 4
            if not df_app.empty:
                pd.DataFrame([{"Phần": "II. LỊCH SỬ PHÊ DUYỆT HUMAN-IN-THE-LOOP"}]).to_excel(
                    writer, sheet_name="05_System_Audit_Log", index=False, header=False, startrow=cur_r5
                )
                df_app.to_excel(writer, sheet_name="05_System_Audit_Log", index=False, startrow=cur_r5 + 1)
                cur_r5 += len(df_app) + 4
            if not df_proc.empty:
                pd.DataFrame([{"Phần": "III. NHẬT KÝ THỰC THI 6 BƯỚC WORKFLOW"}]).to_excel(
                    writer, sheet_name="05_System_Audit_Log", index=False, header=False, startrow=cur_r5
                )
                df_proc.to_excel(writer, sheet_name="05_System_Audit_Log", index=False, startrow=cur_r5 + 1)
                cur_r5 += len(df_proc) + 4
            if not df_au.empty:
                pd.DataFrame([{"Phần": "IV. NHẬT KÝ THAY ĐỔI LÀM SẠCH DỮ LIỆU (CELL AUDIT LOG)"}]).to_excel(
                    writer, sheet_name="05_System_Audit_Log", index=False, header=False, startrow=cur_r5
                )
                df_au.to_excel(writer, sheet_name="05_System_Audit_Log", index=False, startrow=cur_r5 + 1)
                cur_r5 += len(df_au) + 4
            if cur_r5 == 0:
                pd.DataFrame([{"Trạng thái": "Chưa ghi nhận nhật ký hệ thống."}]).to_excel(
                    writer, sheet_name="05_System_Audit_Log", index=False
                )

        return output.getvalue()
