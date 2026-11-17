import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from schema_mapper import AutoSchemaMapper
from data_pipeline import (
    get_sample_marketing_data,
    get_messy_testcase_08_data,
    get_ecommerce_user_data,
    load_google_sheet_flexible,
    load_from_excel_flexible,
    read_csv_smart,
    normalize_raw_dataframe,
    DataCleaner,
)
from analytics_engine import MarketingAnalyticsEngine

# ==============================================================================
# CẤU HÌNH TRANG
# ==============================================================================
st.set_page_config(
    page_title="GrowthMetric — Marketing Campaign Analytics",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded",
)

ADMIN_NAME = "Vũ Ruy Hoàng"
ADMIN_INITIALS = "VH"

PAGES = [
    "Overview (Tổng quan)",
    "Kết Nối Google Sheets",
    "Data Cleaning & Audit",
    "Process Workflow (6 Bước)",
    "Phê Duyệt Exceptions",
    "Verification Suite",
    "Báo Cáo Reports & Export",
    "Cài Đặt Settings",
]

CHART_COLORS = ["#E21A3C", "#2563EB", "#F59E0B", "#7C3AED", "#10B981", "#06B6D4", "#FB7185"]

# ==============================================================================
# DESIGN SYSTEM (CSS)
# ==============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp, button, input, textarea, select {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

/* ---------- Nền & khung (Corporate Light Gray-White + Crimson Red Accent) ---------- */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: #F4F6FA !important;
    color: #0F172A;
}
header[data-testid="stHeader"] { display: none !important; }

.main .block-container, [data-testid="stMainBlockContainer"] {
    background: #F8FAFC;
    border-radius: 24px;
    border: 1px solid #E8ECF4;
    box-shadow: 0 12px 36px rgba(15, 23, 42, 0.04);
    padding: 20px 28px 34px 28px !important;
    margin: 14px auto 22px auto;
    max-width: 98% !important;
}

/* ---------- Hiệu ứng chuyển động mượt ---------- */
@keyframes fadeUp { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
[class*="st-key-card"], .kpi-card, .hero-glass, .phase-bar, .top-glass-bar { animation: fadeUp .28s ease-out both; }
@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }

/* ---------- Clean White Sidebar với Header Đỏ Đô & Banner Đỏ dưới đáy ---------- */
[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #EAECEF !important;
}
[data-testid="stSidebarContent"] {
    background: #FFFFFF !important;
    border-radius: 0;
    margin: 0;
    padding: 0 14px 18px 14px;
    border: none;
    box-shadow: none;
    color: #1E293B;
}
.brand-red-banner {
    background: linear-gradient(135deg, #E21A3C 0%, #B80C29 100%);
    margin: 0 -14px 14px -14px;
    padding: 20px 18px 18px 18px;
    color: #FFFFFF;
    border-bottom-right-radius: 18px;
    box-shadow: 0 8px 20px rgba(226, 26, 60, 0.22);
}
.brand-red-title { font-size: 21px; font-weight: 800; letter-spacing: -.4px; line-height: 1.05; color: #FFFFFF; }
.brand-red-sub { font-size: 11.5px; font-weight: 600; color: rgba(255,255,255,.88); margin-top: 3px; }
.nav-caption { font-size: 10px; font-weight: 800; letter-spacing: .9px; color: #94A3B8; margin: 6px 6px 8px 6px; }

/* ---------- Menu điều hướng: nút chữ nhật bo tròn, không icon, active hồng nhạt ---------- */
[data-testid="stSidebar"] [data-testid="stRadio"] > label { display: none !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] { gap: 6px !important; width: 100%; }
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label {
    background: #FFFFFF !important;
    border: 1px solid #EDF0F5 !important;
    border-radius: 14px !important;
    padding: 10px 15px !important;
    margin: 0 !important;
    width: 100% !important;
    box-sizing: border-box;
    cursor: pointer;
    color: #334155 !important;
    transition: background .18s ease, border-color .18s ease, transform .18s ease, box-shadow .18s ease;
}
[data-testid="stSidebar"] [data-testid="stRadio"] input[type="radio"],
[data-testid="stSidebar"] [data-testid="stRadio"] [class*="ex50key4"] { display: none !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {
    font-size: 13px !important; font-weight: 600 !important; color: inherit !important; margin: 0 !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:hover {
    background: #FFF1F3 !important; border-color: #FECDD3 !important; color: #E21A3C !important; transform: translateX(2px);
}
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
    background: #FFE4E8 !important;
    border: 1.5px solid #FDA4AF !important;
    color: #BE123C !important;
    box-shadow: 0 6px 16px rgba(226, 26, 60, 0.14);
    transform: translateX(2px);
}
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) p { font-weight: 700 !important; }

/* ---------- Tiến độ & Banner đỏ đáy sidebar ---------- */
.side-progress {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 12px 13px;
    margin-top: 14px;
}
.side-progress-title { font-size: 10px; font-weight: 800; letter-spacing: .8px; color: #64748B; margin-bottom: 8px; }
.side-row { display: flex; justify-content: space-between; align-items: center; font-size: 11.5px; font-weight: 600; color: #334155; margin-bottom: 6px; }
.side-promo-red {
    margin-top: 14px;
    border-radius: 16px;
    padding: 16px 16px;
    color: #FFFFFF;
    background: linear-gradient(135deg, #E21A3C 0%, #9F0B24 100%);
    box-shadow: 0 10px 24px rgba(226, 26, 60, 0.24);
}
.side-promo-title { font-size: 15px; font-weight: 800; line-height: 1.25; margin-bottom: 4px; }
.side-promo-sub { font-size: 11px; opacity: .88; }

.badge { font-size: 10px; font-weight: 700; padding: 2px 9px; border-radius: 20px; border: 1px solid; white-space: nowrap; }
.badge.ok { background: #DCFCE7; color: #15803D; border-color: #86EFAC; }
.badge.warn { background: #FEF3C7; color: #B45309; border-color: #FCD34D; }
.badge.fail { background: #FEE2E2; color: #B91C1C; border-color: #FCA5A5; }
.badge.idle { background: #F1F5F9; color: #475569; border-color: #CBD5E1; }

/* ---------- Top Header Bar (Tìm kiếm + Chuông + Admin) ---------- */
.top-glass-bar {
    display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;
    background: #FFFFFF;
    border: 1px solid #E8ECF4;
    border-radius: 16px;
    padding: 10px 18px;
    margin-bottom: 16px;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.03);
}
.top-search {
    flex: 1; min-width: 240px; max-width: 520px;
    background: #F1F5F9; border: 1px solid #E2E8F0; border-radius: 12px;
    padding: 8px 14px; font-size: 12.5px; color: #64748B;
}
.top-right { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.bell-wrap {
    position: relative; width: 34px; height: 34px; border-radius: 50%; background: #F8FAFC;
    border: 1px solid #E2E8F0; display: flex; align-items: center; justify-content: center; font-size: 15px;
}
.bell-dot {
    position: absolute; top: -4px; right: -4px; background: #E21A3C; color: #FFF;
    font-size: 9.5px; font-weight: 800; padding: 1px 5px; border-radius: 10px;
}
.page-header { display: flex; justify-content: space-between; align-items: center; gap: 14px; flex-wrap: wrap; margin-bottom: 14px; }
.page-greet { display: flex; align-items: center; gap: 12px; }
.greet-mark {
    width: 38px; height: 38px; border-radius: 12px; flex-shrink: 0;
    background: linear-gradient(135deg, #FB7185 0%, #E21A3C 100%);
    color: #FFF; font-weight: 800; font-size: 16px;
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 6px 14px rgba(226, 26, 60, 0.25);
}
.page-title { font-size: 22px; font-weight: 800; letter-spacing: -.4px; margin: 0; line-height: 1.15; color: #0F172A; }
.page-sub { font-size: 12.5px; color: #64748B; font-weight: 500; margin-top: 3px; max-width: 720px; }
.header-meta { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.source-chip {
    background: #FFF1F3; border: 1px solid #FECDD3; color: #BE123C; border-radius: 20px;
    padding: 5px 13px; font-size: 11.5px; font-weight: 700; max-width: 320px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.profile-chip { display: flex; align-items: center; gap: 8px; background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 24px; padding: 4px 12px 4px 4px; }
.avatar {
    width: 32px; height: 32px; border-radius: 50%; color: #FFF; font-weight: 800; font-size: 11.5px;
    background: linear-gradient(135deg, #E21A3C 0%, #B80C29 100%);
    display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(226,26,60,.25);
}
.p-name { font-size: 12px; font-weight: 800; color: #0F172A; line-height: 1.2; }
.p-role { font-size: 10px; font-weight: 600; color: #64748B; }

/* ---------- Nút Primary Đỏ Đô đặc trưng theo thiết kế mẫu ---------- */
button[kind="primary"], [data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #E21A3C 0%, #C8102E 100%) !important;
    border: none !important;
    border-radius: 12px !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    box-shadow: 0 6px 16px rgba(226, 26, 60, 0.24) !important;
}
button[kind="primary"]:hover, [data-testid="baseButton-primary"]:hover {
    filter: brightness(1.06);
    transform: translateY(-1px);
}
button[kind="secondary"], [data-testid="baseButton-secondary"] {
    border-radius: 12px !important;
    border: 1px solid #E2E8F0 !important;
    background: #FFFFFF !important;
    font-weight: 600 !important;
}

/* ---------- Thanh tiến trình 5 giai đoạn ---------- */
.phase-bar { display: flex; align-items: center; background: #FFFFFF; border: 1px solid #E8ECF4; border-radius: 14px; padding: 10px 16px; margin-bottom: 16px; gap: 6px; overflow-x: auto; }
.phase { display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 700; color: #94A3B8; white-space: nowrap; }
.phase-dot { width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 800; background: #FFFFFF; border: 2px solid #CBD5E1; color: #94A3B8; }
.phase.done { color: #047857; } .phase.done .phase-dot { background: #10B981; border-color: #10B981; color: #FFF; }
.phase.warn { color: #B45309; } .phase.warn .phase-dot { background: #F59E0B; border-color: #F59E0B; color: #FFF; }
.phase.fail { color: #B91C1C; } .phase.fail .phase-dot { background: #EF4444; border-color: #EF4444; color: #FFF; }
.phase-line { flex: 1; min-width: 18px; height: 2px; background: #E2E8F0; border-radius: 2px; }
.phase-line.done { background: #10B981; }

/* ---------- Card container (st.container key="card_...") ---------- */
[class*="st-key-card"] {
    background: #FFFFFF;
    border: 1px solid #E8ECF4;
    border-radius: 18px;
    padding: 20px 22px;
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.03);
}
.card-title { font-size: 15.5px; font-weight: 800; color: #0F172A; margin: 0; letter-spacing: -.2px; }
.card-sub { font-size: 12px; color: #64748B; margin: 3px 0 12px 0; }

/* ---------- Hero & Upload dashed zone ---------- */
.hero-glass {
    background: #FFFFFF;
    border: 1px solid #E8ECF4;
    border-radius: 18px;
    padding: 22px 24px;
    margin-bottom: 16px;
}
.hero-tag {
    display: inline-block; background: #FFF1F3; border: 1px solid #FECDD3; color: #BE123C;
    font-size: 11px; font-weight: 700; padding: 4px 12px; border-radius: 20px; margin-bottom: 10px;
}
.hero-h1 { font-size: 25px; font-weight: 800; color: #0F172A; line-height: 1.2; margin: 0 0 8px 0; letter-spacing: -.4px; }
.hero-h1 span { color: #E21A3C; }
.hero-desc { font-size: 13px; color: #475569; line-height: 1.6; margin: 0; }
.mini-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 12px; }
.mini-stat { background: #FFFFFF; border-radius: 14px; padding: 13px; border: 1.5px solid #E2E8F0; }
.mini-stat.green { border-color: #BBF7D0; background: #F0FDF4; }
.mini-stat.orange { border-color: #FECDD3; background: #FFF1F3; }
.mini-stat.amber { border-color: #BFDBFE; background: #EFF6FF; }
.mini-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; font-size: 10.5px; font-weight: 800; }
.mini-pill { padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: 800; }
.mini-stat.green .mini-pill { background: #DCFCE7; color: #15803D; }
.mini-stat.orange .mini-pill { background: #FFE4E8; color: #BE123C; }
.mini-stat.amber .mini-pill { background: #DBEAFE; color: #1D4ED8; }
.mini-lbl { font-size: 11px; font-weight: 700; color: #334155; }
.mini-num { font-size: 22px; font-weight: 800; color: #0F172A; margin: 3px 0 2px 0; line-height: 1.1; }
.mini-stat.orange .mini-num { color: #E21A3C; }
.mini-foot { font-size: 10.5px; font-weight: 600; color: #64748B; }
.hero-summary-bar {
    background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 14px; padding: 11px 14px;
    display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;
}
.hero-sum-val { font-size: 15px; font-weight: 800; color: #E21A3C; }
.hero-sum-right { font-size: 11.5px; font-weight: 800; color: #2563EB; text-align: right; }

/* ---------- KPI cards (Hồng nhạt, Xanh dương nhạt, Xanh lá nhạt, Tím nhạt giống ảnh mẫu) ---------- */
.kpi-card { border-radius: 16px; padding: 16px 18px; min-height: 108px; border: 1px solid; display: flex; align-items: center; gap: 14px; transition: transform .18s ease, box-shadow .18s ease; }
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(15,23,42,.05); }
.kpi-card.pink { background: #FFF1F3; border-color: #FFE4E8; }
.kpi-card.amber { background: #EFF6FF; border-color: #DBEAFE; }
.kpi-card.green { background: #ECFDF5; border-color: #D1FAE5; }
.kpi-card.purple { background: #F5F3FF; border-color: #EDE9FE; }
.kpi-ico { width: 42px; height: 42px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: 800; flex-shrink: 0; color: #FFF; }
.kpi-card.pink .kpi-ico { background: #E21A3C; }
.kpi-card.amber .kpi-ico { background: #2563EB; }
.kpi-card.green .kpi-ico { background: #10B981; }
.kpi-card.purple .kpi-ico { background: #7C3AED; }
.kpi-label { font-size: 11.5px; font-weight: 700; color: #475569; }
.kpi-val { font-size: 21px; font-weight: 800; letter-spacing: -.4px; margin: 2px 0; line-height: 1.15; color: #0F172A; }
.kpi-val.muted { font-size: 14px; color: #94A3B8 !important; }
.kpi-hint { font-size: 11px; font-weight: 600; color: #059669; }

/* ---------- Thanh tỷ trọng kênh ---------- */
.ch-row { margin-bottom: 14px; }
.ch-label { display: flex; justify-content: space-between; font-size: 12.5px; font-weight: 700; color: #1E293B; margin-bottom: 6px; }
.ch-bar { height: 9px; background: #F1F5F9; border-radius: 6px; overflow: hidden; }
.ch-fill { height: 100%; border-radius: 6px; transition: width .6s ease; }

/* ---------- Stepper 6 bước ---------- */
.stepper { display: flex; align-items: center; background: #F8FAFD; border: 1px solid #EEF2F7; border-radius: 20px; padding: 18px 22px; margin: 6px 0 22px 0; overflow-x: auto; }
.step { display: flex; flex-direction: column; align-items: center; min-width: 84px; font-size: 11.5px; font-weight: 700; color: #64748B; text-align: center; }
.step-badge { width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 13px; margin-bottom: 6px; background: #FFF; border: 2px solid #CBD5E1; color: #94A3B8; }
.step-badge.done { color: #FFF; border-color: transparent; }
.step-line { flex: 1; min-width: 16px; height: 3px; background: #E2E8F0; margin: 0 6px 18px 6px; border-radius: 3px; }
.step-line.done { background: linear-gradient(90deg, #6366F1, #EC4899); }

/* ---------- Banner kết quả ---------- */
.result-banner { border-radius: 18px; padding: 16px 20px; margin-bottom: 18px; border: 1.5px solid; display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
.result-banner.pass { background: linear-gradient(135deg, #ECFDF5, #D1FAE5); border-color: #10B981; color: #065F46; }
.result-banner.fail { background: linear-gradient(135deg, #FEF2F2, #FEE2E2); border-color: #EF4444; color: #991B1B; }
.result-banner b { font-size: 15px; }
.result-banner small { display: block; font-size: 12.5px; margin-top: 3px; font-weight: 500; }
.pill-count { background: rgba(255,255,255,.7); font-weight: 800; padding: 6px 14px; border-radius: 999px; font-size: 12.5px; }

/* ---------- Widget Streamlit ---------- */
.stButton > button, .stDownloadButton > button {
    border-radius: 14px !important; font-weight: 700 !important; font-size: 13px !important;
    padding: 9px 18px !important; border: 1px solid #E2E8F0 !important; background: #FFFFFF !important; color: #1E293B !important;
    transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    border-color: #A5B4FC !important; color: #4F46E5 !important; transform: translateY(-1px); box-shadow: 0 6px 16px rgba(99,102,241,.14);
}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 55%, #EC4899 100%) !important;
    color: #FFFFFF !important; border: none !important; box-shadow: 0 8px 20px rgba(99,102,241,.30);
}
.stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover { color: #FFF !important; box-shadow: 0 10px 26px rgba(99,102,241,.40); }
.stButton > button:disabled { opacity: .55; transform: none !important; }

[data-testid="stMetric"] { background: #F8FAFD; border: 1px solid #E2E8F0; border-radius: 18px; padding: 14px 16px; }
[data-testid="stMetricLabel"] p { font-size: 12px !important; font-weight: 700 !important; color: #64748B !important; }
[data-testid="stMetricValue"] { font-size: 22px !important; font-weight: 800 !important; color: #1E293B !important; }

[data-testid="stDataFrame"] { border-radius: 14px; overflow: hidden; border: 1px solid #EEF2F7; }
[data-testid="stExpander"] details { border-radius: 16px !important; border: 1px solid #E2E8F0 !important; }
[data-testid="stTextInput"] input { border-radius: 12px !important; }
[data-testid="stAlert"] { border-radius: 14px !important; }
.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] { border-radius: 12px 12px 0 0; font-weight: 700; }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# TIỆN ÍCH GIAO DIỆN
# ==============================================================================
def html(markup: str) -> None:
    """Render HTML an toàn: bỏ thụt lề & dòng trống để Markdown không biến thành code block."""
    clean = "\n".join(line.strip() for line in markup.splitlines() if line.strip())
    st.markdown(clean, unsafe_allow_html=True)


def fmt_vnd(value) -> str:
    try:
        return f"{float(value):,.0f} đ"
    except (TypeError, ValueError):
        return "—"


def card_header(title: str, subtitle: str = "") -> None:
    sub = f'<div class="card-sub">{subtitle}</div>' if subtitle else '<div style="height:10px"></div>'
    html(f'<div class="card-title">{title}</div>{sub}')


def go_to(page: str) -> None:
    st.session_state.nav_page = page


def next_step(label: str, page: str, key: str) -> None:
    st.button(label, type="primary", on_click=go_to, args=(page,), key=key)


def queue_toast(message: str, icon: str = "✅") -> None:
    st.session_state.pending_toast = (message, icon)


def style_chart(fig, height: int = 320):
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans", color="#1E293B", size=12),
        margin=dict(l=8, r=8, t=8, b=8),
        height=height,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=None),
        hoverlabel=dict(bgcolor="#FFFFFF", font_size=12, bordercolor="#E2E8F0"),
    )
    fig.update_xaxes(showgrid=False, title=None)
    fig.update_yaxes(gridcolor="#F1F5F9", title=None)
    return fig


def sanitize_df_for_display(df: pd.DataFrame) -> pd.DataFrame:
    """Làm sạch DataFrame trước khi đưa vào st.dataframe để tránh hoàn toàn ArrowTypeError."""
    if df is None or df.empty:
        return df
    out = df.copy()
    for col in out.columns:
        if out[col].dtype == "object":
            out[col] = out[col].apply(
                lambda v: ", ".join(map(str, v)) if isinstance(v, (list, tuple, set))
                else (str(v) if isinstance(v, dict) else ("" if (v is None or (isinstance(v, float) and pd.isna(v))) else str(v)))
            )
    return out


def show_df_preview(df: pd.DataFrame, max_rows: int = 500, **kwargs) -> None:
    """Hiển thị tối đa max_rows dòng (đã sanitize PyArrow) để tránh lag và lỗi hiển thị."""
    if df is None:
        return
    total = len(df)
    view_df = sanitize_df_for_display(df.head(max_rows) if total > max_rows else df)
    if total > max_rows:
        st.caption(f"Đang hiển thị {max_rows:,} / {total:,} dòng đầu tiên để tối ưu hiệu năng trình duyệt.")
    st.dataframe(view_df, **kwargs)


VI_STATUS_MAP = {
    "NOT_STARTED": "CHƯA XỬ LÝ",
    "PROCESSING": "ĐANG XỬ LÝ",
    "SUCCESS": "ĐẠT CHUẨN",
    "WARNING": "CẢNH BÁO",
    "NEEDS_APPROVAL": "CHỜ PHÊ DUYỆT",
    "FAILED": "LỖI CHẶN",
}


def vi_status(code: str) -> str:
    return VI_STATUS_MAP.get(str(code), str(code))


# ==============================================================================
# SESSION STATE & LOGIC ĐIỀU PHỐI (giữ nguyên backend)
# ==============================================================================
DEFAULT_CHAT_GREETING = {
    "role": "assistant",
    "content": (
        "Xin chào! Tôi là **Trợ lý AI GrowthMetric**. Tôi có thể giúp bạn:\n"
        "- Tư vấn **bước tiếp theo** bạn cần làm trong quy trình.\n"
        "- Tóm tắt **doanh thu, lợi nhuận, kênh bán, sản phẩm & chiến dịch** theo dữ liệu thực tế.\n"
        "- Giải thích **lỗi làm sạch & ngoại lệ cần phê duyệt**."
    ),
}

DEFAULTS = {
    "nav_page": PAGES[0],
    "data_status": "NOT_CONNECTED",    # NOT_CONNECTED | CONNECTED | FAILED
    "cleaning_status": "NOT_STARTED",  # NOT_STARTED | PROCESSING | SUCCESS | WARNING | NEEDS_APPROVAL | FAILED
    "can_proceed_process": False,
    "process_status": "NOT_STARTED",   # NOT_STARTED | COMPLETED | FAILED
    "verification_status": "NOT_RUN",  # NOT_RUN | PASS | FAIL
    "raw_tabs": None,
    "source_name": "Chưa có nguồn dữ liệu",
    "classification_info": None,
    "normalized_data": None,
    "quality_summary": None,
    "cleaning_errors": [],
    "exceptions_list": [],
    "audit_log": [],
    "tab_statuses": [],
    "cleaning_error_detail": None,
    "engine": None,
    "process_result": None,
    "verification_result": None,
    "return_window": 30,
    "reconciliation_table": None,
    "cleaned_excel": None,
    "uploaded_file_id": None,
    "pending_toast": None,
    "chat_history": [dict(DEFAULT_CHAT_GREETING)],
}
for _k, _v in DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = list(_v) if isinstance(_v, list) else _v

if st.session_state.nav_page not in PAGES:
    st.session_state.nav_page = PAGES[0]


def reset_pipeline() -> None:
    """Xóa toàn bộ kết quả cũ khi nạp nguồn dữ liệu mới, tránh hiển thị số liệu lỗi thời."""
    for key in [
        "normalized_data", "quality_summary", "engine", "process_result",
        "verification_result", "reconciliation_table", "cleaned_excel", "cleaning_error_detail",
    ]:
        st.session_state[key] = None
    st.session_state.cleaning_errors = []
    st.session_state.exceptions_list = []
    st.session_state.audit_log = []
    st.session_state.tab_statuses = []
    st.session_state.can_proceed_process = False
    st.session_state.cleaning_status = "NOT_STARTED"
    st.session_state.process_status = "NOT_STARTED"
    st.session_state.verification_status = "NOT_RUN"


def load_dataset(tabs: dict, source_name: str, class_info=None) -> None:
    reset_pipeline()
    st.session_state.raw_tabs = tabs
    st.session_state.source_name = source_name
    st.session_state.classification_info = class_info
    st.session_state.data_status = "CONNECTED"
    queue_toast(f"Đã nạp dữ liệu: {source_name}")


def load_sample(kind: str) -> None:
    if kind == "messy":
        load_dataset(get_messy_testcase_08_data(), "GiaHoa_Raw_Messy_TestCase_08")
    elif kind == "ecommerce":
        load_dataset(get_ecommerce_user_data(), "E-Commerce 12 cột (Net_Sales, Cost, Profit)")
    else:
        load_dataset(get_sample_marketing_data(), "Bộ 3 tabs chuẩn doanh nghiệp")


def run_cleaning() -> None:
    import traceback
    st.session_state.cleaning_status = "PROCESSING"
    st.session_state.cleaning_error_detail = None
    try:
        cleaner = DataCleaner(
            st.session_state.raw_tabs,
            tab_classification=st.session_state.classification_info,
        )
        can_proc, norm_data, q_sum, errs, excs = cleaner.clean_and_normalize()
        st.session_state.normalized_data = norm_data
        st.session_state.quality_summary = q_sum
        st.session_state.cleaning_errors = errs
        st.session_state.exceptions_list = excs
        st.session_state.audit_log = cleaner.audit_log
        st.session_state.tab_statuses = list(cleaner.tab_statuses.values())
        st.session_state.reconciliation_table = cleaner.reconciliation_table
        st.session_state.can_proceed_process = bool(can_proc)
        st.session_state.cleaning_status = q_sum.get("Status", "SUCCESS" if can_proc else "FAILED")
        # Kết quả xử lý cũ không còn hợp lệ sau khi làm sạch lại
        st.session_state.process_result = None
        st.session_state.process_status = "NOT_STARTED"
        st.session_state.verification_result = None
        st.session_state.verification_status = "NOT_RUN"
        st.session_state.engine = MarketingAnalyticsEngine(
            norm_data, initial_exceptions=excs, return_window_days=st.session_state.return_window
        )
        try:
            st.session_state.cleaned_excel = cleaner.export_cleaned_data_excel()
        except Exception:
            st.session_state.cleaned_excel = None
    except Exception as exc:
        st.session_state.can_proceed_process = False
        st.session_state.cleaning_status = "FAILED"
        st.session_state.cleaning_error_detail = f"{type(exc).__name__}: {exc}\n\n{traceback.format_exc()}"


def run_process() -> dict:
    if st.session_state.engine is None:
        st.session_state.engine = MarketingAnalyticsEngine(
            st.session_state.normalized_data,
            initial_exceptions=st.session_state.exceptions_list,
            return_window_days=st.session_state.return_window,
        )
    res = st.session_state.engine.run_process_workflow()
    st.session_state.process_result = res
    st.session_state.process_status = "COMPLETED" if res.get("status") == "COMPLETED" else "FAILED"
    st.session_state.exceptions_list = st.session_state.engine.exceptions_view
    st.session_state.verification_result = None
    st.session_state.verification_status = "NOT_RUN"
    return res


def has_report() -> bool:
    eng = st.session_state.engine
    return eng is not None and eng.report_result is not None and st.session_state.process_status == "COMPLETED"


def pending_exceptions() -> list:
    return [e for e in st.session_state.exceptions_list if e.get("Approval_Status") == "PENDING_REVIEW"]


# ==============================================================================
# THÀNH PHẦN CHUNG
# ==============================================================================
def phase_states() -> list:
    s = st.session_state
    data = "done" if s.data_status == "CONNECTED" else ("fail" if s.data_status == "FAILED" else "")
    if s.cleaning_status == "SUCCESS":
        clean = "done"
    elif s.cleaning_status in ("WARNING", "NEEDS_APPROVAL"):
        clean = "warn" if not s.can_proceed_process else "done"
    elif s.cleaning_status == "FAILED":
        clean = "fail"
    else:
        clean = ""
    proc = "done" if s.process_status == "COMPLETED" else ("fail" if s.process_status == "FAILED" else "")
    if s.process_status == "COMPLETED":
        appr = "warn" if pending_exceptions() else "done"
    else:
        appr = ""
    verify = "done" if s.verification_status == "PASS" else ("fail" if s.verification_status == "FAIL" else "")
    return [
        ("Nạp dữ liệu", data), ("Làm sạch", clean), ("Xử lý 6 bước", proc),
        ("Phê duyệt", appr), ("Kiểm chứng", verify),
    ]


def _build_live_context_summary() -> str:
    s = st.session_state
    lines = [
        f"- Nguồn dữ liệu: {s.source_name if s.data_status == 'CONNECTED' else 'Chưa kết nối'}",
        f"- Trạng thái làm sạch: {vi_status(s.cleaning_status)}",
        f"- Quy trình 6 bước: {s.process_status}",
        f"- Kiểm toán Verification: {s.verification_status}",
    ]
    q = s.quality_summary or {}
    if q:
        lines.append(
            f"- Chất lượng dữ liệu: {q.get('Data_Quality_Score', '—')}% "
            f"({q.get('Normalized_Transactions_Count', 0)} giao dịch chuẩn hóa, "
            f"{q.get('Auto_Fixed_Count', 0)} tự sửa, {q.get('Exceptions_Count', 0)} ngoại lệ)"
        )
    eng = s.engine
    if eng is not None and eng.report_result is not None and s.process_status == "COMPLETED":
        rep = eng.report_result
        lines.append(
            f"- Tổng doanh thu phân bổ: {fmt_vnd(rep['Attributed_Revenue'].sum())} | "
            f"Net Sales: {fmt_vnd(rep['Net_Sales'].sum())}"
        )
    return "\n".join(lines)


def generate_ai_reply(question: str) -> str:
    """Trả lời câu hỏi người dùng dựa trên trạng thái và số liệu thực tế trong phiên."""
    import os
    s = st.session_state
    q_text = (question or "").strip().lower()
    q_sum = s.quality_summary or {}
    pend = pending_exceptions()
    eng = s.engine
    rep = eng.report_result if (eng is not None and s.process_status == "COMPLETED") else None
    active_df = eng.get_active_transactions_df() if eng is not None else (
        (s.normalized_data or {}).get("Normalized_Transactions") if s.normalized_data else None
    )

    # 1. Hỏi bước tiếp theo / hướng dẫn
    if any(k in q_text for k in ["tiếp theo", "làm gì", "hướng dẫn", "bắt đầu", "cần gì", "muốn gì", "quy trình"]):
        if s.data_status != "CONNECTED":
            return (
                "**Bạn chưa nạp dữ liệu.** Hãy chọn một trong hai cách:\n"
                "1. Bấm **⚡ Nạp Bộ 3 Tabs Chuẩn** (hoặc các bộ mẫu bên dưới) để trải nghiệm ngay.\n"
                "2. Vào mục **Kết Nối Google Sheets** để dán link Google Sheets hoặc tải file `.csv` / `.xlsx` của bạn."
            )
        if not q_sum:
            return (
                f"Bạn đã nạp nguồn **{s.source_name}**. Bước tiếp theo:\n"
                "- Bấm **Làm sạch & chạy phân tích ngay** ngay tại trang Tổng quan, hoặc vào **Data Cleaning & Audit** để kiểm tra chi tiết trước khi chạy."
            )
        if not s.can_proceed_process:
            return (
                f"Dữ liệu đang ở trạng thái **{vi_status(s.cleaning_status)}** và còn lỗi chặn.\n"
                "- Hãy mở **Data Cleaning & Audit → Nhật ký lỗi** để xem nguyên nhân và kiểm tra lại cấu trúc bảng nguồn."
            )
        if s.process_status != "COMPLETED":
            return "Dữ liệu đã làm sạch xong! Bạn hãy vào **Process Workflow (6 Bước)** và bấm **Chạy toàn bộ 6 bước** để phân bổ doanh thu và tính Net Contribution."
        if pend:
            return (
                f"Quy trình 6 bước đã hoàn tất, nhưng còn **{len(pend)} ngoại lệ đang chờ duyệt**.\n"
                "- Hãy sang trang **Phê Duyệt Exceptions** để Trưởng phòng Marketing / Quản trị viên chọn **Chấp thuận** hoặc **Từ chối**, sau đó chạy **Verification Suite**."
            )
        if s.verification_status != "PASS":
            return "Tất cả ngoại lệ đã được xử lý! Hãy vào **Verification Suite** và bấm chạy 7 phép kiểm toán để mở khóa **Xuất báo cáo HTML Standalone**."
        return "Toàn bộ quy trình đã **ĐẠT CHUẨN 100%**! Bạn có thể vào **Báo Cáo Reports & Export** để xem bảng chi tiết và tải file HTML hoặc Excel."

    # 2. Hỏi về ngoại lệ / lỗi dữ liệu / làm sạch
    if any(k in q_text for k in ["ngoại lệ", "lỗi", "làm sạch", "duyệt", "trùng", "chất lượng"]):
        if not q_sum:
            return "Hiện chưa chạy bước **Làm sạch & Kiểm toán**. Sau khi nạp dữ liệu, hãy bấm làm sạch để tôi phân tích các lỗi và ngoại lệ cho bạn."
        detail_lines = [
            f"- **Trạng thái làm sạch:** {vi_status(q_sum.get('Status', s.cleaning_status))} (Điểm chất lượng: **{q_sum.get('Data_Quality_Score', '—')}%**)",
            f"- **Số dòng kiểm tra / chuẩn hóa:** {q_sum.get('Total_Raw_Records', 0)} / {q_sum.get('Normalized_Transactions_Count', 0)}",
            f"- **Tự sửa an toàn:** {q_sum.get('Auto_Fixed_Count', 0)} ô | **Trùng lặp:** {q_sum.get('Duplicate_Rows_Count', 0)} | **Thiếu:** {q_sum.get('Missing_Fields_Count', 0)}",
            f"- **Ngoại lệ chờ duyệt:** **{len(pend)}** / {len(s.exceptions_list)}",
        ]
        if pend:
            top_p = "; ".join(f"`{e.get('Order_ID')}` ({e.get('Error_Type')})" for e in pend[:3])
            detail_lines.append(f"- **Ví dụ ngoại lệ đang chờ:** {top_p}. Vào trang **Phê Duyệt Exceptions** để xử lý.")
        return "\n".join(detail_lines)

    # 3. Hỏi về doanh thu / lợi nhuận / kênh / sản phẩm / chiến dịch / tốt nhất
    if any(k in q_text for k in ["doanh thu", "lợi nhuận", "kpi", "kênh", "sản phẩm", "chiến dịch", "tốt nhất", "cao nhất", "tóm tắt"]):
        if rep is None or rep.empty:
            return "Chưa có kết quả phân tích 6 bước. Hãy nạp dữ liệu và bấm **Làm sạch & chạy phân tích ngay** (hoặc chạy ở **Process Workflow**) để tôi tổng hợp số liệu chính xác cho bạn."
        total_rev = rep["Attributed_Revenue"].sum()
        total_net = rep["Net_Sales"].sum()
        ans = [
            f"**Tóm tắt số liệu thực tế ({s.source_name}):**",
            f"- **Tổng Doanh thu phân bổ:** {fmt_vnd(total_rev)}",
            f"- **Net Sales (sau đối soát hoàn trả):** {fmt_vnd(total_net)}",
        ]
        if "Total_Cost" in rep.columns and rep["Total_Cost"].notna().any():
            ans.append(f"- **Chi phí ABC:** {fmt_vnd(rep['Total_Cost'].sum())}")
        if "Net_Contribution" in rep.columns and rep["Net_Contribution"].notna().any():
            ans.append(f"- **Net Contribution:** {fmt_vnd(rep['Net_Contribution'].sum())}")
        elif active_df is not None and "Source_Profit" in active_df.columns:
            prof = pd.to_numeric(active_df["Source_Profit"], errors="coerce").dropna().sum()
            ans.append(f"- **Lợi nhuận gộp nguồn:** {fmt_vnd(prof)}")

        if active_df is not None and not active_df.empty and "Channel" in active_df.columns and "Order_Value" in active_df.columns:
            ch_df = active_df[["Channel", "Order_Value"]].copy()
            ch_df["Order_Value"] = pd.to_numeric(ch_df["Order_Value"], errors="coerce").fillna(0)
            by_ch = ch_df.groupby("Channel")["Order_Value"].sum()
            by_ch = by_ch[by_ch > 0].sort_values(ascending=False)
            if not by_ch.empty:
                top_ch = by_ch.index[0]
                pct = by_ch.iloc[0] / by_ch.sum() * 100
                ans.append(f"- **Kênh dẫn đầu:** `{top_ch}` ({fmt_vnd(by_ch.iloc[0])} — {pct:.1f}%)")

        if active_df is not None and not active_df.empty and "Product_Name" in active_df.columns and active_df["Product_Name"].notna().any():
            pr_df = active_df[["Product_Name", "Order_Value"]].dropna(subset=["Product_Name"]).copy()
            pr_df["Order_Value"] = pd.to_numeric(pr_df["Order_Value"], errors="coerce").fillna(0)
            by_pr = pr_df.groupby("Product_Name")["Order_Value"].sum().sort_values(ascending=False)
            if not by_pr.empty:
                ans.append(f"- **Sản phẩm doanh thu cao nhất:** `{by_pr.index[0]}` ({fmt_vnd(by_pr.iloc[0])})")
        elif not rep.empty:
            top_c = rep.sort_values("Net_Sales", ascending=False).iloc[0]
            ans.append(f"- **Nhóm chiến dịch dẫn đầu:** `{top_c['Campaign_Name']}` ({fmt_vnd(top_c['Net_Sales'])})")
        return "\n".join(ans)

    # 4. Câu hỏi tự do: thử Gemini nếu có GEMINI_API_KEY, ngược lại trả tóm tắt ngữ cảnh thông minh
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    ctx = _build_live_context_summary()
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            prompt = (
                "Bạn là Trợ lý AI của hệ thống GrowthMetric Marketing Analytics. "
                "Trả lời ngắn gọn, dễ hiểu bằng tiếng Việt dựa ĐÚNG trên trạng thái thực tế sau (không bịa số liệu):\n"
                f"{ctx}\n\nCâu hỏi người dùng: {question}"
            )
            resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            if resp and getattr(resp, "text", None):
                return resp.text.strip()
        except Exception:
            pass

    return (
        f"**Trạng thái phiên làm việc hiện tại:**\n{ctx}\n\n"
        "Bạn có thể hỏi tôi cụ thể về:\n"
        "- *“Tôi cần làm gì tiếp theo?”*\n"
        "- *“Tóm tắt doanh thu & lợi nhuận”*\n"
        "- *“Giải thích ngoại lệ cần duyệt”*"
    )


def render_header(title: str, subtitle: str, show_chatbot: bool = False) -> None:
    source = st.session_state.source_name if st.session_state.data_status == "CONNECTED" else "Chưa kết nối nguồn dữ liệu"
    n_pend = len(pending_exceptions())
    bell_badge = f'<span class="bell-dot">{n_pend}</span>' if n_pend else ""
    bar_html = f"""
    <div class="top-glass-bar" style="margin-bottom:0;">
        <div class="top-search">🔍 Tìm kiếm dữ liệu, dự án, chiến dịch, mã đơn...</div>
        <div class="top-right">
            <span class="source-chip" title="{source}">Nguồn: {source}</span>
            <div class="bell-wrap" title="Ngoại lệ chờ duyệt">🔔{bell_badge}</div>
            <div class="profile-chip">
                <div class="avatar">{ADMIN_INITIALS}</div>
                <div><div class="p-name">{ADMIN_NAME}</div><div class="p-role">Admin account</div></div>
            </div>
        </div>
    </div>
    """
    if show_chatbot:
        c_bar, c_bot = st.columns([4.4, 1.15], vertical_alignment="center")
        with c_bar:
            html(bar_html)
        with c_bot:
            with st.popover("🤖 Trợ lý AI", width="stretch"):
                st.markdown("**Trợ lý AI GrowthMetric**")
                st.caption(f"Nguồn: {source} • {vi_status(st.session_state.cleaning_status)}")
                q1, q2 = st.columns(2)
                q3, q4 = st.columns(2)
                quick_prompts = [
                    (q1, "Bước tiếp theo?", "Tôi cần làm gì tiếp theo?", "ai_q1"),
                    (q2, "Tóm tắt KPI", "Tóm tắt doanh thu & lợi nhuận", "ai_q2"),
                    (q3, "Xem ngoại lệ", "Giải thích ngoại lệ cần duyệt", "ai_q3"),
                    (q4, "Kênh / SP tốt", "Kênh / chiến dịch nào tốt nhất?", "ai_q4"),
                ]
                for col_w, btn_lbl, full_q, k_btn in quick_prompts:
                    if col_w.button(btn_lbl, key=k_btn, width="stretch"):
                        st.session_state.chat_history.append({"role": "user", "content": full_q})
                        st.session_state.chat_history.append({"role": "assistant", "content": generate_ai_reply(full_q)})
                        st.rerun()

                with st.container(height=260):
                    for msg in st.session_state.chat_history:
                        with st.chat_message(msg["role"]):
                            st.markdown(msg["content"])

                with st.form("ai_chat_form", clear_on_submit=True, border=False):
                    user_q = st.text_input("Hỏi Trợ lý AI...", placeholder="VD: Tôi cần làm gì tiếp theo?", label_visibility="collapsed")
                    send_clicked = st.form_submit_button("Gửi câu hỏi", type="primary", width="stretch")
                if send_clicked and user_q.strip():
                    st.session_state.chat_history.append({"role": "user", "content": user_q.strip()})
                    st.session_state.chat_history.append({"role": "assistant", "content": generate_ai_reply(user_q.strip())})
                    st.rerun()
                if st.button("Làm mới hội thoại", key="ai_clear", width="stretch"):
                    st.session_state.chat_history = [dict(DEFAULT_CHAT_GREETING)]
                    st.rerun()
        st.write("")
    else:
        html(bar_html)
        st.write("")

    html(f"""
    <div class="page-header">
        <div class="page-greet">
            <div class="greet-mark">GM</div>
            <div>
                <h1 class="page-title">{title}</h1>
                <div class="page-sub">{subtitle}</div>
            </div>
        </div>
    </div>
    """)
    parts = []
    states = phase_states()
    for i, (label, state) in enumerate(states):
        mark = "✓" if state == "done" else ("!" if state in ("warn", "fail") else str(i + 1))
        parts.append(f'<div class="phase {state}"><div class="phase-dot">{mark}</div>{label}</div>')
        if i < len(states) - 1:
            parts.append(f'<div class="phase-line {"done" if state == "done" else ""}"></div>')
    html(f'<div class="phase-bar">{"".join(parts)}</div>')


def badge(state: str, text: str) -> str:
    return f'<span class="badge {state}">{text}</span>'


def empty_state(message: str, button_label: str, page: str, key: str) -> None:
    with st.container(key=f"card_empty_{key}"):
        st.info(message)
        next_step(button_label, page, key=f"btn_empty_{key}")


# ==============================================================================
# SIDEBAR
# ==============================================================================
with st.sidebar:
    html("""
    <div class="brand-red-banner">
        <div class="brand-red-title">GrowthMetric</div>
        <div class="brand-red-sub">solutions • Marketing AI</div>
    </div>
    <div class="nav-caption">ĐIỀU HƯỚNG HỆ THỐNG</div>
    """)
    st.radio("Điều hướng", PAGES, key="nav_page", label_visibility="collapsed")

    s = st.session_state
    ds = badge("ok", "ĐÃ KẾT NỐI") if s.data_status == "CONNECTED" else (badge("fail", "LỖI") if s.data_status == "FAILED" else badge("idle", "CHƯA KẾT NỐI"))
    if s.cleaning_status == "SUCCESS":
        cl = badge("ok", vi_status("SUCCESS"))
    elif s.cleaning_status == "WARNING":
        cl = badge("warn", vi_status("WARNING"))
    elif s.cleaning_status == "NEEDS_APPROVAL":
        cl = badge("warn", vi_status("NEEDS_APPROVAL"))
    elif s.cleaning_status == "PROCESSING":
        cl = badge("idle", vi_status("PROCESSING"))
    elif s.cleaning_status == "FAILED":
        cl = badge("fail", vi_status("FAILED"))
    else:
        cl = badge("idle", vi_status("NOT_STARTED"))
    pr = badge("ok", "HOÀN TẤT") if s.process_status == "COMPLETED" else (badge("fail", "THẤT BẠI") if s.process_status == "FAILED" else badge("idle", "CHƯA CHẠY"))
    n_pending = len(pending_exceptions())
    if s.process_status == "COMPLETED":
        ap = badge("warn", f"CHỜ DUYỆT ({n_pending})") if n_pending else badge("ok", "ĐÃ DUYỆT ĐỦ")
    else:
        ap = badge("idle", "CHƯA PHÁT SINH")
    vr = badge("ok", "PASS") if s.verification_status == "PASS" else (badge("fail", "CHƯA ĐẠT") if s.verification_status == "FAIL" else badge("idle", "CHƯA CHẠY"))
    html(f"""
    <div class="side-progress">
        <div class="side-progress-title">TIẾN ĐỘ WORKFLOW</div>
        <div class="side-row"><span>Nguồn dữ liệu</span>{ds}</div>
        <div class="side-row"><span>Làm sạch</span>{cl}</div>
        <div class="side-row"><span>Process 6 bước</span>{pr}</div>
        <div class="side-row"><span>Phê duyệt</span>{ap}</div>
        <div class="side-row"><span>Verification</span>{vr}</div>
    </div>
    <div class="side-promo-red">
        <div class="side-promo-title">Kiến tạo<br>giá trị số</div>
        <div class="side-promo-sub">cùng GrowthMetric AI • {ADMIN_NAME}</div>
    </div>
    """)

# Thông báo toast sau khi thao tác (hiển thị một lần)
if st.session_state.pending_toast:
    _msg, _icon = st.session_state.pending_toast
    st.toast(_msg, icon=_icon)
    st.session_state.pending_toast = None

page = st.session_state.nav_page


# ==============================================================================
# TRANG 1: TỔNG QUAN
# ==============================================================================
if page == PAGES[0]:
    render_header("Chào mừng bạn trở lại!", "Quản lý và khai thác dữ liệu Marketing thông minh cùng GrowthMetric AI.", show_chatbot=True)

    if st.session_state.data_status != "CONNECTED":
        with st.container(key="card_hero_glass"):
            h_left, h_right = st.columns([1.15, 1.0], gap="large")
            with h_left:
                html("""
                <div class="hero-tag">✨ Spatial Intelligence • Quy trình chuẩn 6 bước</div>
                <div class="hero-h1">Trung Tâm Điều Hành<br><span>GrowthMetric Analytics</span></div>
                <p class="hero-desc">
                    Tự động làm sạch dữ liệu Google Sheets đa tab, phân bổ doanh thu đa điểm chạm,
                    đối soát hoàn trả, tính chi phí ABC và kiểm toán 7 bất biến tài chính trước khi xuất báo cáo.
                </p>
                """)
                st.write("")
                b1, b2 = st.columns(2)
                b1.button("⚡ Nạp Bộ 3 Tabs Chuẩn", type="primary", width="stretch",
                          on_click=load_sample, args=("standard",), key="qs_std")
                b2.button("Kết nối Google Sheets / File →", width="stretch",
                          on_click=go_to, args=(PAGES[1],), key="qs_connect")
            with h_right:
                html("""
                <div class="mini-grid">
                    <div class="mini-stat green">
                        <div class="mini-top"><span>✓</span><span class="mini-pill">Auto</span></div>
                        <div class="mini-lbl">Làm Sạch Tự Động</div>
                        <div class="mini-num">6 Bước</div>
                        <div class="mini-foot">Bảo toàn Raw Data</div>
                    </div>
                    <div class="mini-stat orange">
                        <div class="mini-top"><span>!</span><span class="mini-pill">Review</span></div>
                        <div class="mini-lbl">Phê Duyệt Ngoại Lệ</div>
                        <div class="mini-num">0</div>
                        <div class="mini-foot">Chưa nạp dữ liệu</div>
                    </div>
                    <div class="mini-stat amber">
                        <div class="mini-top"><span>⚑</span><span class="mini-pill">Audit</span></div>
                        <div class="mini-lbl">Kiểm Toán Suite</div>
                        <div class="mini-num">7 Tests</div>
                        <div class="mini-foot">Đối soát bất biến</div>
                    </div>
                </div>
                <div class="hero-summary-bar">
                    <div>
                        <div style="font-size:11px;font-weight:700;color:#64748B;">Trạng thái hệ thống</div>
                        <div class="hero-sum-val">Sẵn sàng nhận dữ liệu</div>
                    </div>
                    <div class="hero-sum-right">Multi-Tab Google Sheets<br><span style="color:#64748B;font-weight:600;">Excel / CSV / Dữ liệu mẫu</span></div>
                </div>
                """)

        with st.container(key="card_quickstart"):
            card_header("Nạp dữ liệu đầu vào nhanh", "Chọn nhanh bộ dữ liệu kiểm thử hoặc kết nối Google Sheets ở trên để bắt đầu.")
            c1, c2 = st.columns(2)
            c1.button("GiaHoa TestCase_08 (dữ liệu lộn xộn)", width="stretch",
                      on_click=load_sample, args=("messy",), key="qs_messy")
            c2.button("E-Commerce 12 cột (Net Sales, COGS, Profit)", width="stretch",
                      on_click=load_sample, args=("ecommerce",), key="qs_ecom")

    elif not has_report():
        with st.container(key="card_ready"):
            card_header("Dữ liệu đã sẵn sàng", f"Nguồn: {st.session_state.source_name}. Bấm một lần để làm sạch dữ liệu và chạy toàn bộ quy trình 6 bước.")
            if st.button("Làm sạch & chạy phân tích ngay", type="primary", key="ov_run_all"):
                with st.spinner("Đang làm sạch dữ liệu và chạy quy trình 6 bước..."):
                    run_cleaning()
                    if st.session_state.can_proceed_process:
                        res = run_process()
                        if res.get("status") == "COMPLETED":
                            queue_toast("Đã hoàn tất làm sạch và quy trình 6 bước")
                        else:
                            queue_toast(f"Quy trình dừng ở {res.get('failed_step')}: {res.get('message')}", "⚠️")
                    else:
                        queue_toast("Dữ liệu còn lỗi chặn — xem chi tiết ở trang Data Cleaning", "⚠️")
                st.rerun()

        # Nếu đã chạy Data Cleaning nhưng chưa chạy Process 6 bước -> hiển thị biểu đồ chất lượng dữ liệu
        q = st.session_state.quality_summary
        if q:
            st.write("")
            qc1, qc2 = st.columns(2)
            with qc1:
                with st.container(key="card_ov_clean_summary"):
                    card_header("Tổng quan Làm sạch Dữ liệu", f"Trạng thái: {q.get('Status', '—')} • Điểm chất lượng: {q.get('Data_Quality_Score', 0)}%")
                    clean_metrics = pd.DataFrame({
                        "Hạng mục": ["Tự sửa an toàn", "Trùng lặp", "Trường thiếu", "Ngoại lệ", "Lỗi ghi nhận"],
                        "Số lượng": [
                            q.get("Auto_Fixed_Count", 0),
                            q.get("Duplicate_Rows_Count", 0),
                            q.get("Missing_Fields_Count", 0),
                            q.get("Exceptions_Count", 0),
                            q.get("Total_Errors_Count", 0),
                        ],
                    })
                    fig_cl = px.bar(clean_metrics, x="Hạng mục", y="Số lượng", color="Hạng mục",
                                    color_discrete_sequence=["#10B981", "#F59E0B", "#3B82F6", "#EC4899", "#EF4444"])
                    fig_cl.update_layout(showlegend=False)
                    fig_cl.update_traces(marker_line_width=0)
                    st.plotly_chart(style_chart(fig_cl, height=260), width="stretch", config={"displayModeBar": False})
            with qc2:
                with st.container(key="card_ov_tab_status"):
                    card_header("Trạng thái xử lý từng Tab", f"{q.get('Tabs_Processed_Count', 0)}/{q.get('Total_Tabs_Count', 0)} tab đã kiểm tra")
                    t_stats = q.get("Tab_Statuses") or st.session_state.tab_statuses
                    if t_stats:
                        df_ts = pd.DataFrame(t_stats)
                        fig_ts = px.pie(df_ts, names="Status", hole=0.55,
                                        color="Status",
                                        color_discrete_map={
                                            "SUCCESS": "#10B981", "WARNING": "#F59E0B",
                                            "NEEDS_APPROVAL": "#EC4899", "FAILED": "#EF4444",
                                        })
                        fig_ts.update_traces(textinfo="label+value")
                        st.plotly_chart(style_chart(fig_ts, height=260), width="stretch", config={"displayModeBar": False})

    else:
        rep = st.session_state.engine.report_result
        total_rev = rep["Attributed_Revenue"].sum()
        total_net = rep["Net_Sales"].sum()
        has_costs = "Total_Cost" in rep.columns and rep["Total_Cost"].notna().any()
        total_cost = rep["Total_Cost"].sum() if has_costs else None
        total_nc = rep["Net_Contribution"].sum() if has_costs and "Net_Contribution" in rep.columns else None
        n_campaigns = len(rep)
        q = st.session_state.quality_summary or {}

        cost_html = f'<div class="kpi-val">{fmt_vnd(total_cost)}</div>' if total_cost is not None else '<div class="kpi-val muted">Chưa có dữ liệu chi phí</div>'
        nc_html = f'<div class="kpi-val">{fmt_vnd(total_nc)}</div>' if total_nc is not None else '<div class="kpi-val muted">Cần tab Campaign_Costs</div>'

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            html(f'<div class="kpi-card pink"><div class="kpi-ico">₫</div><div><div class="kpi-label">Doanh thu phân bổ</div><div class="kpi-val">{fmt_vnd(total_rev)}</div><div class="kpi-hint">↑ {n_campaigns} nhóm chiến dịch</div></div></div>')
        with k2:
            html(f'<div class="kpi-card amber"><div class="kpi-ico">📊</div><div><div class="kpi-label">Net Sales</div><div class="kpi-val">{fmt_vnd(total_net)}</div><div class="kpi-hint">↑ Đối soát {st.session_state.return_window} ngày</div></div></div>')
        with k3:
            html(f'<div class="kpi-card green"><div class="kpi-ico">✓</div><div><div class="kpi-label">Chất lượng dữ liệu</div><div class="kpi-val">{q.get("Data_Quality_Score", "—")}%</div><div class="kpi-hint">{vi_status(q.get("Status", st.session_state.cleaning_status))}</div></div></div>')
        with k4:
            nc_display = fmt_vnd(total_nc) if total_nc is not None else (fmt_vnd(total_cost) if total_cost is not None else f"{len(pending_exceptions())} chờ duyệt")
            nc_label = "Net Contribution" if total_nc is not None else ("Chi phí ABC" if total_cost is not None else "Ngoại lệ chờ duyệt")
            html(f'<div class="kpi-card purple"><div class="kpi-ico">⚡</div><div><div class="kpi-label">{nc_label}</div><div class="kpi-val">{nc_display}</div><div class="kpi-hint">Chi phí ABC: {fmt_vnd(total_cost) if total_cost is not None else "Chưa có"}</div></div></div>')

        st.write("")
        norm_tx = st.session_state.engine.get_active_transactions_df()
        missing_cmp = (
            norm_tx is not None and "Campaign_Data_Status" in norm_tx.columns
            and (norm_tx["Campaign_Data_Status"] == "MISSING_SOURCE_DATA").all()
        )
        has_product = (
            norm_tx is not None and "Product_Name" in norm_tx.columns
            and norm_tx["Product_Name"].dropna().astype(str).str.strip().ne("").any()
        )

        # Hàng biểu đồ 1: Doanh thu theo Sản phẩm (nếu thiếu mã chiến dịch) hoặc Chiến dịch & Tỷ trọng theo kênh
        col_a, col_b = st.columns([3, 2])
        with col_a:
            with st.container(key="card_campaign_chart"):
                if missing_cmp and has_product:
                    card_header("Doanh thu & Lợi nhuận gộp theo Sản phẩm", "Tổng hợp từ các bản ghi hợp lệ sau xử lý")
                    p_df = norm_tx[["Product_Name", "Order_Value", "Source_Profit"]].dropna(subset=["Product_Name"]).copy()
                    p_df["Order_Value"] = pd.to_numeric(p_df["Order_Value"], errors="coerce").fillna(0)
                    p_df["Source_Profit"] = pd.to_numeric(p_df["Source_Profit"], errors="coerce").fillna(0)
                    by_prod = p_df.groupby("Product_Name", as_index=False)[["Order_Value", "Source_Profit"]].sum()
                    melt_prod = by_prod.melt(id_vars="Product_Name", var_name="Chỉ tiêu", value_name="VNĐ").replace({
                        "Order_Value": "Doanh thu thuần",
                        "Source_Profit": "Lợi nhuận gộp",
                    })
                    fig = px.bar(melt_prod, x="Product_Name", y="VNĐ", color="Chỉ tiêu", barmode="group",
                                 color_discrete_sequence=["#E21A3C", "#2563EB"])
                    fig.update_traces(marker_line_width=0, hovertemplate="%{x}<br>%{y:,.0f} đ<extra></extra>")
                    st.plotly_chart(style_chart(fig), width="stretch", config={"displayModeBar": False})
                else:
                    card_header("Doanh thu theo chiến dịch", "So sánh doanh thu phân bổ và Net Sales sau hoàn trả")
                    chart_df = rep[["Campaign_Name", "Attributed_Revenue", "Net_Sales"]].melt(
                        id_vars="Campaign_Name", var_name="Chỉ số", value_name="VNĐ"
                    ).replace({"Attributed_Revenue": "Doanh thu phân bổ", "Net_Sales": "Net Sales"})
                    fig = px.bar(chart_df, x="Campaign_Name", y="VNĐ", color="Chỉ số", barmode="group",
                                 color_discrete_sequence=["#E21A3C", "#FB7185"])
                    fig.update_traces(marker_line_width=0, hovertemplate="%{x}<br>%{y:,.0f} đ<extra></extra>")
                    st.plotly_chart(style_chart(fig), width="stretch", config={"displayModeBar": False})

        with col_b:
            with st.container(key="card_channel"):
                card_header("Tỷ trọng doanh thu theo kênh", "Tính từ giá trị đơn hàng đã chuẩn hóa")
                if norm_tx is not None and len(norm_tx) and "Channel" in norm_tx.columns and "Order_Value" in norm_tx.columns:
                    tmp = norm_tx[["Channel", "Order_Value"]].copy()
                    tmp["Channel"] = tmp["Channel"].fillna("Chưa xác định").astype(str).replace({"": "Chưa xác định", "None": "Chưa xác định"})
                    tmp["Order_Value"] = pd.to_numeric(tmp["Order_Value"], errors="coerce").fillna(0)
                    by_ch = tmp.groupby("Channel")["Order_Value"].sum()
                    by_ch = by_ch[by_ch > 0].sort_values(ascending=False)
                    total = by_ch.sum()
                    if total > 0:
                        rows = []
                        for i, (ch, val) in enumerate(by_ch.head(6).items()):
                            pct = val / total * 100
                            color = CHART_COLORS[i % len(CHART_COLORS)]
                            rows.append(
                                f'<div class="ch-row"><div class="ch-label"><span>{ch}</span><span style="color:{color}">{pct:.1f}%</span></div>'
                                f'<div class="ch-bar"><div class="ch-fill" style="width:{pct:.1f}%;background:{color}"></div></div></div>'
                            )
                        html("".join(rows))
                    else:
                        st.caption("Chưa có giá trị đơn hàng hợp lệ để tính tỷ trọng.")
                else:
                    st.caption("Nguồn dữ liệu không có cột kênh bán (Channel).")

        # Hàng biểu đồ 2 (Tự thích ứng theo từng báo cáo đã xử lý):
        # - Trái: Chi phí ABC & Net Contribution (nếu có Costs) HOẶC Cơ cấu Doanh thu - COGS - Lợi nhuận gộp
        # - Phải: Xu hướng doanh thu theo ngày (nếu có Order_Date) HOẶC Doanh thu theo Phương thức thanh toán
        st.write("")
        col_c, col_d = st.columns(2)
        with col_c:
            with st.container(key="card_ov_profit_cost"):
                if has_costs and "Net_Contribution" in rep.columns:
                    card_header("Hiệu quả Chi phí ABC & Net Contribution", "So sánh Net Sales, Chi phí ABC và Lợi nhuận ròng theo chiến dịch")
                    fin_df = rep[["Campaign_Name", "Net_Sales", "Total_Cost", "Net_Contribution"]].melt(
                        id_vars="Campaign_Name", var_name="Chỉ tiêu", value_name="VNĐ"
                    ).replace({
                        "Net_Sales": "Net Sales",
                        "Total_Cost": "Chi phí ABC",
                        "Net_Contribution": "Net Contribution",
                    })
                    fig_fin = px.bar(fin_df, x="Campaign_Name", y="VNĐ", color="Chỉ tiêu", barmode="group",
                                     color_discrete_sequence=["#3B82F6", "#8B5CF6", "#10B981"])
                    fig_fin.update_traces(marker_line_width=0, hovertemplate="%{x}<br>%{y:,.0f} đ<extra></extra>")
                    st.plotly_chart(style_chart(fig_fin, height=290), width="stretch", config={"displayModeBar": False})
                elif norm_tx is not None and len(norm_tx):
                    card_header("Cơ cấu Doanh thu — Giá vốn — Lợi nhuận", "Tổng hợp từ bảng giao dịch đã chuẩn hóa")
                    net_s = float(pd.to_numeric(norm_tx.get("Order_Value", 0), errors="coerce").fillna(0).sum())
                    cogs_s = float(pd.to_numeric(norm_tx.get("COGS", 0), errors="coerce").fillna(0).sum())
                    prof_s = float(pd.to_numeric(norm_tx.get("Source_Profit", 0), errors="coerce").fillna(0).sum())
                    disc_s = float(pd.to_numeric(norm_tx.get("Discount_Amount", 0), errors="coerce").fillna(0).sum())
                    struct_df = pd.DataFrame({
                        "Thành phần": ["Net Sales", "Giá vốn (COGS)", "Lợi nhuận gộp", "Giảm giá"],
                        "Giá trị": [net_s, cogs_s, prof_s, disc_s],
                    })
                    fig_st = px.bar(struct_df, x="Thành phần", y="Giá trị", color="Thành phần",
                                    color_discrete_sequence=["#3B82F6", "#F59E0B", "#10B981", "#EC4899"])
                    fig_st.update_layout(showlegend=False)
                    fig_st.update_traces(marker_line_width=0, hovertemplate="%{x}: %{y:,.0f} đ<extra></extra>")
                    st.plotly_chart(style_chart(fig_st, height=290), width="stretch", config={"displayModeBar": False})

        with col_d:
            with st.container(key="card_ov_trend_or_payment"):
                has_dates = (
                    norm_tx is not None and "Order_Date" in norm_tx.columns
                    and norm_tx["Order_Date"].dropna().astype(str).str.strip().ne("").any()
                )
                distinct_pay = 0
                if norm_tx is not None and "Payment_Method" in norm_tx.columns:
                    distinct_pay = norm_tx["Payment_Method"].dropna().astype(str).str.strip().nunique()
                if has_dates:
                    card_header("Xu hướng Doanh thu & Lợi nhuận theo Tháng/Ngày", "Diễn biến doanh thu và lợi nhuận gộp từ các đơn hợp lệ")
                    t_df = norm_tx[["Order_Date", "Order_Value", "Source_Profit"]].dropna(subset=["Order_Date"]).copy()
                    t_df["Order_Date"] = t_df["Order_Date"].astype(str)
                    t_df = t_df[t_df["Order_Date"].str.strip().ne("") & t_df["Order_Date"].ne("None") & t_df["Order_Date"].ne("nan")]
                    t_df["Order_Value"] = pd.to_numeric(t_df["Order_Value"], errors="coerce").fillna(0)
                    t_df["Source_Profit"] = pd.to_numeric(t_df["Source_Profit"], errors="coerce").fillna(0)
                    if not t_df.empty:
                        daily = t_df.groupby("Order_Date", as_index=False)[["Order_Value", "Source_Profit"]].sum().sort_values("Order_Date")
                        melt_daily = daily.melt(id_vars="Order_Date", var_name="Chỉ tiêu", value_name="VNĐ").replace({
                            "Order_Value": "Doanh thu thuần",
                            "Source_Profit": "Lợi nhuận gộp",
                        })
                        fig_tr = px.line(melt_daily, x="Order_Date", y="VNĐ", color="Chỉ tiêu", markers=True,
                                         color_discrete_sequence=["#8B5CF6", "#10B981"])
                        fig_tr.update_traces(hovertemplate="%{x}<br>%{y:,.0f} đ<extra></extra>")
                        st.plotly_chart(style_chart(fig_tr, height=290), width="stretch", config={"displayModeBar": False})
                    else:
                        st.caption("Không có ngày hợp lệ để vẽ biểu đồ xu hướng.")
                elif norm_tx is not None and "Payment_Method" in norm_tx.columns and distinct_pay >= 2:
                    card_header("Doanh thu theo Phương thức Thanh toán", "Phân bổ giá trị đơn hàng theo hình thức thanh toán")
                    p_df = norm_tx[["Payment_Method", "Order_Value"]].copy()
                    p_df["Payment_Method"] = p_df["Payment_Method"].fillna("Khác").astype(str)
                    p_df["Order_Value"] = pd.to_numeric(p_df["Order_Value"], errors="coerce").fillna(0)
                    by_pay = p_df.groupby("Payment_Method", as_index=False)["Order_Value"].sum()
                    fig_pay = px.pie(by_pay, names="Payment_Method", values="Order_Value", hole=0.52,
                                     color_discrete_sequence=CHART_COLORS)
                    fig_pay.update_traces(textinfo="percent+label", hovertemplate="%{label}<br>%{value:,.0f} đ<extra></extra>")
                    st.plotly_chart(style_chart(fig_pay, height=290), width="stretch", config={"displayModeBar": False})
                else:
                    card_header("Phân bổ Doanh thu theo Chiến dịch", "Tỷ trọng đóng góp Net Sales của từng chiến dịch")
                    fig_pie = px.pie(rep, names="Campaign_Name", values="Net_Sales", hole=0.52,
                                     color_discrete_sequence=CHART_COLORS)
                    fig_pie.update_traces(textinfo="percent+label")
                    st.plotly_chart(style_chart(fig_pie, height=290), width="stretch", config={"displayModeBar": False})

        # Hàng biểu đồ 3: Khu vực / Hoàn trả / Quyết định & Kiểm toán Verification / Cleaning
        st.write("")
        col_e, col_f = st.columns(2)
        with col_e:
            with st.container(key="card_ov_decisions_returns"):
                has_region = (
                    norm_tx is not None and "Region" in norm_tx.columns
                    and norm_tx["Region"].dropna().astype(str).str.strip().ne("").any()
                )
                has_returns = "Return_Amount" in rep.columns and rep["Return_Amount"].sum() > 0
                if has_region:
                    card_header("Doanh thu & Lợi nhuận theo Khu vực", "So sánh đóng góp theo vùng miền từ các đơn hợp lệ")
                    reg_df = norm_tx[["Region", "Order_Value", "Source_Profit"]].dropna(subset=["Region"]).copy()
                    reg_df["Order_Value"] = pd.to_numeric(reg_df["Order_Value"], errors="coerce").fillna(0)
                    reg_df["Source_Profit"] = pd.to_numeric(reg_df["Source_Profit"], errors="coerce").fillna(0)
                    by_reg = reg_df.groupby("Region", as_index=False)[["Order_Value", "Source_Profit"]].sum()
                    melt_reg = by_reg.melt(id_vars="Region", var_name="Chỉ tiêu", value_name="VNĐ").replace({
                        "Order_Value": "Doanh thu thuần",
                        "Source_Profit": "Lợi nhuận gộp",
                    })
                    fig_reg = px.bar(melt_reg, x="Region", y="VNĐ", color="Chỉ tiêu", barmode="group",
                                     color_discrete_sequence=["#3B82F6", "#10B981"])
                    fig_reg.update_traces(marker_line_width=0, hovertemplate="%{x}<br>%{y:,.0f} đ<extra></extra>")
                    st.plotly_chart(style_chart(fig_reg, height=270), width="stretch", config={"displayModeBar": False})
                elif has_returns:
                    card_header("Tác động Hoàn trả theo Chiến dịch", "Doanh thu phân bổ, giá trị hoàn trả và Net Sales thực nhận")
                    ret_df = rep[["Campaign_Name", "Attributed_Revenue", "Return_Amount", "Net_Sales"]].melt(
                        id_vars="Campaign_Name", var_name="Thành phần", value_name="VNĐ"
                    ).replace({
                        "Attributed_Revenue": "Doanh thu phân bổ",
                        "Return_Amount": "Khấu trừ hoàn trả",
                        "Net_Sales": "Net Sales",
                    })
                    fig_ret = px.bar(ret_df, x="Campaign_Name", y="VNĐ", color="Thành phần", barmode="group",
                                     color_discrete_sequence=["#6366F1", "#EF4444", "#10B981"])
                    fig_ret.update_traces(marker_line_width=0, hovertemplate="%{x}<br>%{y:,.0f} đ<extra></extra>")
                    st.plotly_chart(style_chart(fig_ret, height=270), width="stretch", config={"displayModeBar": False})
                elif "Decision" in rep.columns:
                    card_header("Phân bổ Quyết định Marketing", "Tổng Net Sales theo nhóm khuyến nghị hành động")
                    dec_df = rep.groupby("Decision", as_index=False)["Net_Sales"].sum()
                    fig_dec = px.bar(dec_df, x="Decision", y="Net_Sales", color="Decision",
                                     color_discrete_sequence=CHART_COLORS)
                    fig_dec.update_layout(showlegend=False)
                    fig_dec.update_traces(marker_line_width=0, hovertemplate="%{x}: %{y:,.0f} đ<extra></extra>")
                    st.plotly_chart(style_chart(fig_dec, height=270), width="stretch", config={"displayModeBar": False})

        with col_f:
            with st.container(key="card_ov_audit_verify"):
                ver_res = st.session_state.verification_result
                if ver_res and ver_res.get("tests"):
                    card_header("Kết quả Kiểm toán Verification Suite", f"Trạng thái: {ver_res.get('overall_status')} • {ver_res.get('pass_count')} Pass / {ver_res.get('na_count')} N/A / {ver_res.get('fail_count')} Fail")
                    v_counts = pd.DataFrame(ver_res["tests"])["status"].value_counts().reset_index()
                    v_counts.columns = ["Trạng thái", "Số bài test"]
                    fig_v = px.pie(v_counts, names="Trạng thái", values="Số bài test", hole=0.55,
                                   color="Trạng thái",
                                   color_discrete_map={"PASS": "#10B981", "NOT_APPLICABLE": "#94A3B8", "FAIL": "#EF4444"})
                    fig_v.update_traces(textinfo="label+value")
                    st.plotly_chart(style_chart(fig_v, height=270), width="stretch", config={"displayModeBar": False})
                else:
                    card_header("Tổng hợp Kiểm toán & Làm sạch", f"Điểm chất lượng: {q.get('Data_Quality_Score', '—')}% • {q.get('Tabs_Processed_Count', 1)}/{q.get('Total_Tabs_Count', 1)} tab")
                    audit_df = pd.DataFrame({
                        "Hạng mục": ["Tự sửa an toàn", "Audit Log", "Ngoại lệ", "Cảnh báo/Lỗi"],
                        "Số lượng": [
                            q.get("Auto_Fixed_Count", 0),
                            q.get("Audit_Log_Count", len(st.session_state.audit_log)),
                            q.get("Exceptions_Count", 0),
                            q.get("Total_Errors_Count", 0),
                        ],
                    })
                    fig_au = px.bar(audit_df, x="Hạng mục", y="Số lượng", color="Hạng mục",
                                    color_discrete_sequence=["#10B981", "#3B82F6", "#EC4899", "#F59E0B"])
                    fig_au.update_layout(showlegend=False)
                    fig_au.update_traces(marker_line_width=0)
                    st.plotly_chart(style_chart(fig_au, height=270), width="stretch", config={"displayModeBar": False})

        with st.container(key="card_recent_tx"):
            card_header("Đơn hàng gần nhất", "8 bản ghi đầu tiên sau chuẩn hóa")
            norm_tx = (st.session_state.normalized_data or {}).get("Normalized_Transactions")
            if norm_tx is not None and len(norm_tx):
                cols = [c for c in ["Order_ID", "Order_Value", "Channel", "Campaign_List_Str", "Return_Status", "Order_Date"] if c in norm_tx.columns]
                view = norm_tx[cols].head(8).copy()
                if "Order_Value" in view.columns:
                    view["Order_Value"] = view["Order_Value"].apply(fmt_vnd)
                view = view.rename(columns={
                    "Order_ID": "Mã đơn", "Order_Value": "Giá trị", "Channel": "Kênh",
                    "Campaign_List_Str": "Chiến dịch", "Return_Status": "Hoàn trả", "Order_Date": "Ngày",
                })
                st.dataframe(view, width="stretch", hide_index=True)
            else:
                st.caption("Chưa có đơn hàng.")

        n_pending = len(pending_exceptions())
        if n_pending:
            st.warning(f"Còn {n_pending} ngoại lệ chờ phê duyệt trước khi kiểm chứng và xuất báo cáo.")
            next_step("Đi tới Phê duyệt ngoại lệ →", PAGES[4], "ov_next_approve")
        elif st.session_state.verification_status != "PASS":
            next_step("Đi tới Verification Suite →", PAGES[5], "ov_next_verify")
        else:
            next_step("Xuất báo cáo HTML →", PAGES[6], "ov_next_report")


# ==============================================================================
# TRANG 2: KẾT NỐI DỮ LIỆU
# ==============================================================================
elif page == PAGES[1]:
    render_header("Kết nối dữ liệu", "Dán link Google Sheets hoặc tải file Excel/CSV. Hệ thống tự nhận diện tab, tên cột tiếng Việt/tiếng Anh và ánh xạ về schema chuẩn.")

    tab_gs, tab_file, tab_sample = st.tabs(["Google Sheets", "Tải file Excel / CSV", "Dữ liệu mẫu"])

    with tab_gs:
        with st.container(key="card_gsheet"):
            card_header("Liên kết Google Sheets", "Bảng tính cần bật quyền “Bất kỳ ai có đường liên kết đều có thể xem”.")
            with st.form("gsheet_form", border=False):
                url = st.text_input("Đường dẫn Google Sheets", placeholder="https://docs.google.com/spreadsheets/d/.../edit")
                submitted = st.form_submit_button("Kiểm tra & kết nối", type="primary")
            if submitted:
                if not url.strip():
                    st.error("Vui lòng nhập đường dẫn Google Sheets.")
                else:
                    try:
                        with st.spinner("Đang kết nối và quét các tab..."):
                            ok, tabs_dict, class_info, msg = load_google_sheet_flexible(url.strip())
                        if ok:
                            load_dataset(tabs_dict, f"Google Sheets ({len(tabs_dict)} tab)", class_info)
                            st.rerun()
                        else:
                            st.session_state.data_status = "FAILED"
                            st.error(msg)
                    except Exception as exc:
                        st.session_state.data_status = "FAILED"
                        st.error(f"Không thể kết nối Google Sheets: {exc}")

    with tab_file:
        with st.container(key="card_upload"):
            card_header("Tải file từ máy tính", "Hỗ trợ .xlsx, .xls, .csv")
            uploaded = st.file_uploader("Chọn file", type=["xlsx", "xls", "csv"], label_visibility="collapsed")
            if uploaded is not None:
                file_id = f"{uploaded.name}-{uploaded.size}"
                # Chỉ nạp một lần cho mỗi file, tránh reset trạng thái ở mỗi lần rerun
                if st.session_state.uploaded_file_id != file_id:
                    try:
                        if uploaded.name.lower().endswith(".csv"):
                            df_csv = read_csv_smart(uploaded)
                            if df_csv is None or df_csv.empty:
                                st.error("File CSV không có dữ liệu hợp lệ.")
                            else:
                                load_dataset({"Untitled": df_csv}, f"File CSV: {uploaded.name}")
                                st.session_state.uploaded_file_id = file_id
                                st.rerun()
                        else:
                            ok, tabs_dict, class_info, msg = load_from_excel_flexible(uploaded)
                            if ok:
                                load_dataset(tabs_dict, f"File Excel: {uploaded.name}", class_info)
                                st.session_state.uploaded_file_id = file_id
                                st.rerun()
                            else:
                                st.error(msg)
                    except Exception as exc:
                        st.error(f"Lỗi khi đọc file '{uploaded.name}': {exc}")
                else:
                    st.success(f"Đang sử dụng file: {uploaded.name}")

    with tab_sample:
        with st.container(key="card_samples"):
            card_header("Bộ dữ liệu mẫu", "Dùng để kiểm thử nhanh toàn bộ quy trình")
            c1, c2, c3 = st.columns(3)
            c1.button("GiaHoa TestCase_08", type="primary", width="stretch", on_click=load_sample, args=("messy",), key="sp_messy")
            c2.button("E-Commerce 12 cột", width="stretch", on_click=load_sample, args=("ecommerce",), key="sp_ecom")
            c3.button("Bộ 3 tabs chuẩn", width="stretch", on_click=load_sample, args=("standard",), key="sp_std")

    if st.session_state.raw_tabs:
        st.write("")
        with st.container(key="card_mapping"):
            card_header("Nhận diện cột & ánh xạ schema", f"Nguồn hiện tại: {st.session_state.source_name}")
            mapper = AutoSchemaMapper()
            for t_name, df_tab in st.session_state.raw_tabs.items():
                with st.expander(f"Tab “{t_name}” — {len(df_tab)} bản ghi, {len(df_tab.columns)} cột", expanded=True):
                    map_res = mapper.map_columns(list(df_tab.columns), target_tab="Transactions")
                    if map_res["mapping_table"]:
                        view = pd.DataFrame(map_res["mapping_table"])[
                            ["Original_Column", "Mapped_Field", "Field_Description", "Confidence_Score", "Match_Type", "Status"]
                        ]
                        view.columns = ["Cột gốc", "Trường chuẩn", "Ý nghĩa", "Độ tin cậy", "Kiểu khớp", "Trạng thái"]
                        st.dataframe(view, width="stretch", hide_index=True)
                    if map_res["unmapped_columns"]:
                        st.caption("Cột chưa ánh xạ (vẫn được giữ lại để đối chiếu): " + ", ".join(map_res["unmapped_columns"]))
        next_step("Tiếp tục: Làm sạch dữ liệu →", PAGES[2], "conn_next")


# ==============================================================================
# TRANG 3: DATA CLEANING
# ==============================================================================
elif page == PAGES[2]:
    render_header("Làm sạch & Kiểm toán Dữ liệu", "Chuẩn hóa tiền tệ, tách mã chiến dịch, phát hiện ngoại lệ và đối chiếu 5 bất biến tài chính trước/sau.")

    if not st.session_state.raw_tabs:
        empty_state("Chưa có dữ liệu để làm sạch.", "Đi tới Kết nối dữ liệu →", PAGES[1], "clean")
    else:
        label = "Làm sạch lại dữ liệu" if st.session_state.quality_summary else "Bắt đầu làm sạch & chuẩn hóa"
        if st.button(label, type="primary", key="btn_clean"):
            with st.spinner("Đang làm sạch và chuẩn hóa toàn bộ các tab..."):
                run_cleaning()
            if st.session_state.cleaning_error_detail:
                queue_toast("Phát sinh lỗi trong quá trình làm sạch — xem chi tiết bên dưới", "⚠️")
            else:
                q = st.session_state.quality_summary
                queue_toast(f"Làm sạch xong ({vi_status(q['Status'])}) — chất lượng {q['Data_Quality_Score']}%, {len(st.session_state.exceptions_list)} ngoại lệ")
            st.rerun()

        if st.session_state.cleaning_error_detail:
            st.error("Đã phát sinh lỗi khi làm sạch dữ liệu (hệ thống đã giữ nguyên Dữ liệu gốc). Chi tiết kỹ thuật:")
            st.code(st.session_state.cleaning_error_detail)

        q = st.session_state.quality_summary
        if q:
            st.write("")
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Bảng đã xử lý", f"{q.get('Tabs_Processed_Count', 1)}/{q.get('Total_Tabs_Count', 1)}")
            m2.metric("Dòng kiểm tra", f"{q['Total_Raw_Records']}")
            m3.metric("Dòng chuẩn hóa", f"{q.get('Normalized_Rows_Count', q['Normalized_Transactions_Count'])}")
            m4.metric("Tự sửa an toàn", f"{q['Auto_Fixed_Count']}")
            m5.metric("Điểm chất lượng", f"{q['Data_Quality_Score']}%")

            n1, n2, n3, n4, n5 = st.columns(5)
            n1.metric("Lỗi phát hiện", f"{q.get('Total_Errors_Count', len(st.session_state.cleaning_errors))}")
            n2.metric("Trùng lặp", f"{q.get('Duplicate_Rows_Count', 0)}")
            n3.metric("Trường bị thiếu", f"{q.get('Missing_Fields_Count', 0)}")
            n4.metric("Ngoại lệ cần duyệt", f"{q['Exceptions_Count']}")
            n5.metric("Trạng thái", vi_status(q.get("Status", st.session_state.cleaning_status)))

            if st.session_state.cleaning_status == "FAILED" or not st.session_state.can_proceed_process:
                st.error("Dữ liệu còn lỗi chặn nên chưa thể chạy quy trình 6 bước. Xem nhật ký lỗi và trạng thái từng bảng bên dưới để biết chi tiết.")
            elif st.session_state.cleaning_status == "NEEDS_APPROVAL":
                st.warning(f"Đã chuẩn hóa dữ liệu ({q['Data_Quality_Score']}%) nhưng còn {q['Exceptions_Count']} ngoại lệ cần xem xét/phê duyệt.")

            st.write("")
            t_tabs, t_rec, t_cmp, t_log, t_audit = st.tabs([
                "Trạng thái các bảng", "Đối chiếu bất biến", "Trước & sau", "Nhật ký lỗi", "Nhật ký thay đổi"
            ])
            with t_tabs:
                if st.session_state.tab_statuses:
                    df_ts = pd.DataFrame(st.session_state.tab_statuses).copy()
                    if "Status" in df_ts.columns:
                        df_ts["Status"] = df_ts["Status"].map(vi_status)
                    df_ts = df_ts.rename(columns={
                        "Tab": "Tên bảng", "Role": "Vai trò", "Status": "Trạng thái",
                        "Raw_Rows": "Dòng gốc", "Cleaned_Rows": "Dòng chuẩn hóa",
                        "Auto_Fixed": "Tự sửa", "Errors": "Lỗi", "Exceptions": "Ngoại lệ",
                        "Message": "Chi tiết",
                    })
                    st.dataframe(df_ts, width="stretch", hide_index=True)
                else:
                    st.caption("Chưa có thông tin trạng thái bảng.")
            with t_rec:
                if st.session_state.reconciliation_table:
                    df_rec = pd.DataFrame(st.session_state.reconciliation_table)
                    df_rec.columns = ["Chỉ số kiểm toán", "Trường nguồn", "Giá trị nguồn", "Trường chuẩn", "Giá trị chuẩn", "Độ lệch", "Trạng thái"]
                    st.caption("Không được làm mất doanh thu thuần, giá vốn, lợi nhuận gộp hay số bản ghi.")
                    st.dataframe(df_rec, width="stretch", hide_index=True)
                else:
                    st.caption("Nguồn dữ liệu không có các cột tài chính để đối chiếu.")
            with t_cmp:
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Dữ liệu thô (Dữ liệu gốc được bảo toàn)**")
                    show_df_preview(list(st.session_state.raw_tabs.values())[0].head(10), width="stretch", hide_index=True)
                with c2:
                    st.markdown("**Dữ liệu đã chuẩn hóa**")
                    norm_tx = (st.session_state.normalized_data or {}).get("Normalized_Transactions")
                    if norm_tx is not None and not norm_tx.empty:
                        priority = [
                            "Order_ID", "Order_Value", "Gross_Sales", "COGS", "Source_Profit", "Quantity", "Unit_Price",
                            "Discount_Rate", "Discount_Amount", "Campaign_List_Str", "Campaign_Data_Status", "Channel",
                            "Return_Status", "Shipping_Days", "Payment_Method", "Customer_Satisfaction", "Order_Date",
                        ]
                        hidden = {"Has_Exception", "Run_ID", "Campaign_List", "Campaign_Count"}
                        cols = [c for c in priority if c in norm_tx.columns] + [
                            c for c in norm_tx.columns if c not in priority and not c.startswith("Raw_") and c not in hidden
                        ]
                        view_norm = norm_tx[cols].head(10).copy()
                        if "Campaign_Data_Status" in view_norm.columns:
                            view_norm["Campaign_Data_Status"] = view_norm["Campaign_Data_Status"].replace({
                                "AVAILABLE": "Có dữ liệu", "MISSING_SOURCE_DATA": "Thiếu ở nguồn",
                            })
                        view_norm = view_norm.rename(columns={
                            "Order_ID": "Mã đơn hàng", "Order_Value": "Doanh thu thuần", "Gross_Sales": "Doanh thu gộp",
                            "COGS": "Giá vốn (COGS)", "Source_Profit": "Lợi nhuận gộp", "Quantity": "Số lượng",
                            "Unit_Price": "Đơn giá", "Discount_Rate": "Tỷ lệ giảm", "Discount_Amount": "Tiền giảm giá",
                            "Campaign_List_Str": "Danh sách chiến dịch", "Campaign_Data_Status": "Trạng thái chiến dịch",
                            "Channel": "Kênh bán", "Return_Status": "Hoàn trả", "Shipping_Days": "Số ngày giao",
                            "Payment_Method": "Thanh toán", "Customer_Satisfaction": "Hài lòng KH", "Order_Date": "Ngày đặt hàng",
                        })
                        show_df_preview(view_norm, width="stretch", hide_index=True)
                    else:
                        st.caption("Chưa có bảng dữ liệu chuẩn hóa hợp lệ.")
            with t_log:
                if st.session_state.cleaning_errors:
                    df_err = pd.DataFrame(st.session_state.cleaning_errors).rename(columns={
                        "Tab": "Tên bảng", "Row_Index": "Dòng", "Order_ID": "Mã đơn",
                        "Field": "Trường dữ liệu", "Error_Type": "Loại lỗi", "Severity": "Mức độ",
                        "Raw_Value": "Giá trị gốc", "Action_Taken": "Xử lý", "Description": "Mô tả chi tiết",
                    })
                    show_df_preview(df_err, width="stretch", hide_index=True)
                else:
                    st.success("Không ghi nhận cảnh báo nào.")
            with t_audit:
                if st.session_state.audit_log:
                    df_au = pd.DataFrame(st.session_state.audit_log).rename(columns={
                        "Tab": "Tên bảng", "Column": "Cột", "Row_Index": "Dòng",
                        "Record_ID": "Mã bản ghi", "Raw_Value": "Giá trị ban đầu",
                        "Cleaned_Value": "Giá trị sau xử lý", "Reason": "Lý do thay đổi",
                        "Method": "Phương pháp", "Timestamp": "Thời điểm",
                    })
                    show_df_preview(df_au, width="stretch", hide_index=True)
                else:
                    st.caption("Không có thay đổi tự động nào được ghi nhận.")

            st.write("")
            c_dl, c_next = st.columns([1, 1])
            with c_dl:
                if st.session_state.cleaned_excel:
                    st.download_button(
                        "Tải dữ liệu sạch (.xlsx)",
                        data=st.session_state.cleaned_excel,
                        file_name=f"Cleaned_Data_{datetime.datetime.now():%Y%m%d_%H%M%S}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
            with c_next:
                if st.session_state.can_proceed_process:
                    next_step("Tiếp tục: Chạy quy trình 6 bước →", PAGES[3], "clean_next")


# ==============================================================================
# TRANG 4: PROCESS 6 BƯỚC
# ==============================================================================
elif page == PAGES[3]:
    render_header("Process Workflow — 6 bước", "Tập trung dữ liệu → phân bổ doanh thu đa điểm chạm → đối soát hoàn trả → phân bổ chi phí ABC → Net Contribution → quyết định.")

    if not st.session_state.normalized_data:
        empty_state("Cần làm sạch dữ liệu trước khi chạy quy trình.", "Đi tới Data Cleaning →", PAGES[2], "proc")
    elif not st.session_state.can_proceed_process:
        empty_state("Dữ liệu còn lỗi chặn. Hãy xử lý ở bước làm sạch.", "Xem Data Cleaning →", PAGES[2], "proc_fail")
    else:
        label = "Chạy lại 6 bước" if st.session_state.process_status == "COMPLETED" else "Chạy toàn bộ 6 bước"
        if st.button(label, type="primary", key="btn_process"):
            with st.spinner("Đang thực thi 6 bước..."):
                res = run_process()
            if res.get("status") == "COMPLETED":
                queue_toast("Đã hoàn tất 6 bước xử lý")
            else:
                queue_toast(f"Dừng ở {res.get('failed_step')}: {res.get('message')}", "⚠️")
            st.rerun()

        done = st.session_state.process_status == "COMPLETED"
        steps = ["Tập trung dữ liệu", "Phân bổ doanh thu", "Đối soát hoàn trả", "Chi phí ABC", "Net Contribution", "Quyết định"]
        colors = ["#3B82F6", "#8B5CF6", "#EC4899", "#F59E0B", "#10B981", "#06B6D4"]
        parts = []
        for i, (name, color) in enumerate(zip(steps, colors)):
            style = f' style="background:{color}"' if done else ""
            parts.append(f'<div class="step"><div class="step-badge {"done" if done else ""}"{style}>{i + 1}</div>{name}</div>')
            if i < len(steps) - 1:
                parts.append(f'<div class="step-line {"done" if done else ""}"></div>')
        html(f'<div class="stepper">{"".join(parts)}</div>')

        if st.session_state.process_status == "FAILED" and st.session_state.process_result:
            r = st.session_state.process_result
            st.error(f"Quy trình dừng ở {r.get('failed_step')}: {r.get('message')}")

        eng = st.session_state.engine
        if done and eng is not None:
            t_rep, t_det = st.tabs(["Kết quả theo chiến dịch", "Chi tiết phân bổ từng đơn"])
            with t_rep:
                st.dataframe(eng.report_result, width="stretch", hide_index=True)
            with t_det:
                if eng.detailed_attributed_df is not None:
                    show_df_preview(eng.detailed_attributed_df, width="stretch", hide_index=True)
            st.write("")
            if pending_exceptions():
                next_step("Tiếp tục: Phê duyệt ngoại lệ →", PAGES[4], "proc_next_appr")
            else:
                next_step("Tiếp tục: Verification →", PAGES[5], "proc_next_ver")


# ==============================================================================
# TRANG 5: PHÊ DUYỆT NGOẠI LỆ
# ==============================================================================
elif page == PAGES[4]:
    render_header("Phê duyệt ngoại lệ", "Human-in-the-loop: chỉ người có thẩm quyền mới được chấp thuận hoặc từ chối ngoại lệ. Mọi quyết định đều được lưu vết.")

    exceptions = st.session_state.exceptions_list
    if not exceptions:
        if st.session_state.quality_summary is None:
            empty_state("Chưa có dữ liệu được làm sạch nên chưa phát sinh ngoại lệ.", "Đi tới Data Cleaning →", PAGES[2], "exc")
        else:
            st.success("Không có ngoại lệ nào cần xử lý.")
            next_step("Tiếp tục: Verification →", PAGES[5], "exc_none_next")
    else:
        pending = pending_exceptions()
        approved = [e for e in exceptions if e.get("Approval_Status") == "APPROVED"]
        rejected = [e for e in exceptions if e.get("Approval_Status") == "REJECTED"]
        m1, m2, m3 = st.columns(3)
        m1.metric("Chờ duyệt", len(pending))
        m2.metric("Đã chấp thuận", len(approved))
        m3.metric("Từ chối / yêu cầu sửa", len(rejected))

        st.write("")
        col_form, col_list = st.columns([2, 3])
        with col_form:
            with st.container(key="card_approve_form"):
                card_header("Ra quyết định", "Chọn ngoại lệ và hành động")
                if pending:
                    options = {f"{e['Order_ID']} — {e['Error_Type']}": (e["Order_ID"], e["Error_Type"]) for e in pending}
                    with st.form("approve_form", border=False):
                        choice = st.selectbox("Ngoại lệ", list(options.keys()))
                        action = st.radio("Hành động", ["Chấp thuận", "Từ chối / loại trừ", "Yêu cầu làm rõ"], horizontal=True)
                        role = st.selectbox("Vai trò người duyệt", [
                            "Trưởng phòng Marketing", "Trưởng phòng Marketing & Tài chính", "Quản trị viên",
                            "Ban Giám Đốc", "Nhân viên bán hàng (Không có quyền duyệt)",
                        ])
                        reviewer = st.text_input("Tên người duyệt", value=ADMIN_NAME)
                        note = st.text_area("Ghi chú / lý do", placeholder="Đã đối soát với chứng từ gốc...", height=80)
                        submit = st.form_submit_button("Xác nhận quyết định", type="primary", width="stretch")
                    if submit:
                        code = {"Chấp thuận": "APPROVE", "Từ chối / loại trừ": "REJECT"}.get(action, "REQUEST_CORRECTION")
                        oid_sel, etype_sel = options[choice]
                        ok, msg = st.session_state.engine.resolve_exception(oid_sel, code, role, reviewer, note, error_type=etype_sel)
                        if ok:
                            st.session_state.exceptions_list = st.session_state.engine.exceptions_view
                            # Kết quả kiểm chứng cũ không còn đúng sau khi thay đổi phê duyệt
                            st.session_state.verification_result = None
                            st.session_state.verification_status = "NOT_RUN"
                            queue_toast(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                else:
                    st.success("Tất cả ngoại lệ đã được xử lý.")
                    next_step("Tiếp tục: Verification →", PAGES[5], "exc_next")
        with col_list:
            with st.container(key="card_exc_list"):
                card_header("Danh sách ngoại lệ", f"{len(exceptions)} mục")
                show_df_preview(pd.DataFrame(exceptions), width="stretch", hide_index=True, height=420)


# ==============================================================================
# TRANG 6: VERIFICATION
# ==============================================================================
elif page == PAGES[5]:
    render_header("Verification Suite", "7 phép kiểm toán tự động: schema, tính duy nhất, tiền tệ, đối soát doanh thu, hoàn trả, phê duyệt và chi phí.")

    if not has_report():
        empty_state("Cần hoàn tất quy trình 6 bước trước khi kiểm chứng.", "Đi tới Process Workflow →", PAGES[3], "ver")
    else:
        n_pending = len(pending_exceptions())
        if n_pending:
            st.warning(f"Còn {n_pending} ngoại lệ chờ duyệt — phép kiểm phê duyệt sẽ chưa đạt.")
        if st.button("Chạy 7 phép kiểm toán", type="primary", key="btn_verify"):
            with st.spinner("Đang kiểm toán..."):
                vr = st.session_state.engine.run_verification()
            st.session_state.verification_result = vr
            st.session_state.verification_status = vr["overall_status"]
            queue_toast("Kiểm chứng đạt — đã mở khóa báo cáo" if vr["overall_status"] == "PASS" else "Kiểm chứng chưa đạt",
                        "✅" if vr["overall_status"] == "PASS" else "⚠️")
            st.rerun()

        vr = st.session_state.verification_result
        if vr:
            st.write("")
            if vr["overall_status"] == "PASS":
                html(f"""<div class="result-banner pass"><div><b>Verification PASS</b>
                <small>Tất cả phép kiểm áp dụng được đều đạt. Báo cáo HTML đã được mở khóa.</small></div>
                <span class="pill-count">{vr['pass_count']} đạt • {vr.get('na_count', 0)} không áp dụng</span></div>""")
            else:
                html(f"""<div class="result-banner fail"><div><b>Verification chưa đạt</b>
                <small>Có {vr.get('fail_count', 0)} phép kiểm chưa đạt. Xử lý ngoại lệ hoặc dữ liệu rồi chạy lại.</small></div>
                <span class="pill-count">{vr['pass_count']} đạt • {vr.get('fail_count', 0)} chưa đạt</span></div>""")
            df_tests = pd.DataFrame(vr["tests"])[["code", "name", "condition", "expected", "actual", "status", "impact"]]
            df_tests.columns = ["Mã", "Phép kiểm", "Điều kiện", "Kỳ vọng", "Thực tế", "Trạng thái", "Tác động"]
            st.dataframe(df_tests, width="stretch", hide_index=True)
            if vr["overall_status"] == "PASS":
                next_step("Tiếp tục: Xuất báo cáo →", PAGES[6], "ver_next")
            elif n_pending:
                next_step("Đi tới Phê duyệt ngoại lệ →", PAGES[4], "ver_back")


# ==============================================================================
# TRANG 7: BÁO CÁO
# ==============================================================================
elif page == PAGES[6]:
    render_header("Báo cáo & Xuất file", "Báo cáo HTML độc lập, sẵn sàng gửi Ban Giám đốc. Chỉ mở khóa khi Verification đạt PASS.")

    if st.session_state.verification_status != "PASS" or not has_report():
        empty_state("Báo cáo đang khóa: cần Verification đạt PASS.", "Đi tới Verification Suite →", PAGES[5], "rep")
    else:
        report_html = st.session_state.engine.generate_html_report()
        st.download_button(
            "Tải báo cáo HTML",
            data=report_html,
            file_name=f"Marketing_Campaign_Report_{datetime.datetime.now():%Y%m%d_%H%M%S}.html",
            mime="text/html",
            type="primary",
        )
        st.write("")
        with st.container(key="card_report_preview"):
            card_header("Xem trước báo cáo")
            st.components.v1.html(report_html, height=760, scrolling=True)


# ==============================================================================
# TRANG 8: CÀI ĐẶT
# ==============================================================================
elif page == PAGES[7]:
    render_header("Cài đặt", "Tham số nghiệp vụ dùng cho các lần chạy quy trình tiếp theo.")

    with st.container(key="card_settings"):
        card_header("Return Window", "Số ngày tối đa để một đơn hoàn trả được trừ vào doanh thu")
        new_window = st.slider("Số ngày", min_value=15, max_value=30, value=st.session_state.return_window, step=1)
        if new_window != st.session_state.return_window:
            st.session_state.return_window = new_window
            if st.session_state.normalized_data:
                st.info("Đã lưu. Hãy chạy lại Data Cleaning và quy trình 6 bước để áp dụng giá trị mới.")
            else:
                st.success(f"Đã cập nhật Return Window = {new_window} ngày.")

    st.write("")
    with st.container(key="card_roles"):
        card_header("Vai trò có thẩm quyền phê duyệt ngoại lệ")
        html("".join(f'<span class="badge ok" style="display:inline-block;margin:0 6px 8px 0;font-size:11.5px;padding:5px 12px">{r}</span>'
                     for r in MarketingAnalyticsEngine.AUTHORIZED_ROLES))

    st.write("")
    with st.container(key="card_reset"):
        card_header("Làm mới phiên làm việc", "Xóa dữ liệu đã nạp và toàn bộ kết quả hiện tại")
        if st.button("Xóa dữ liệu & bắt đầu lại", key="btn_reset"):
            reset_pipeline()
            st.session_state.raw_tabs = None
            st.session_state.data_status = "NOT_CONNECTED"
            st.session_state.source_name = "Chưa có nguồn dữ liệu"
            st.session_state.uploaded_file_id = None
            queue_toast("Đã làm mới phiên làm việc", "🔄")
            st.rerun()
