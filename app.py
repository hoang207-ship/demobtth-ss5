import datetime
import html as _html
import re
import time
import uuid

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from schema_mapper import AutoSchemaMapper
from data_pipeline import (
    MAX_ROW_LIMIT,
    get_sample_marketing_data,
    get_messy_testcase_08_data,
    get_ecommerce_user_data,
    load_google_sheet_flexible,
    load_from_excel_flexible,
    read_csv_smart,
    normalize_raw_dataframe,
    parse_currency_value,
    parse_campaign_list,
    DataCleaner,
)
from analytics_engine import (
    MarketingAnalyticsEngine,
    build_enterprise_report_narratives,
    ENTERPRISE_NARRATIVE_CSS,
    safe_float,
)

# ==============================================================================
# CẤU HÌNH TRANG & CHẶN DỊCH MÁY TRÌNH DUYỆT (NATIVE I18N)
# ==============================================================================
st.set_page_config(
    page_title="Data Forge — Hệ thống Phân tích & Kiểm toán Dữ liệu Doanh nghiệp",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

ADMIN_NAME = "Vũ Ruy Hoàng"
ADMIN_INITIALS = "VH"

PAGES = [
    "Overview (Tổng quan)",
    "Kết Nối Google Sheets",
    "Data Cleaning & Audit",
    "Process Workflow (6 Bước)",
    "Phê Duyệt Exceptions",
    "Verification Suite",
    "Xuất Báo cáo Quản trị (Reports & Export)",
    "Cấu hình Hệ thống & Định mức (Settings)",
]

NAV_SHORT_LABELS = {
    PAGES[0]: "Tổng quan",
    PAGES[1]: "Kết nối dữ liệu",
    PAGES[2]: "Làm sạch",
    PAGES[3]: "Quy trình 6 bước",
    PAGES[4]: "Phê duyệt HITL",
    PAGES[5]: "Kiểm chứng",
    PAGES[6]: "Báo cáo & Xuất",
    PAGES[7]: "Cấu hình",
}

CHART_COLORS = ["#C21F20", "#258B86", "#5277A6", "#8B6A9C", "#D69A3B", "#7C1F27", "#E9A096"]

# Con trỏ chuột tùy chỉnh (Thanh kiếm tím pixel 32×32 + hiệu ứng phát sáng khi hover)
_CURSOR_SWORD_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAABOElEQVR42t2WrU4DQRRGzza8wEpI+UtgRcMbFEUQpAmCkAZM"
    "FQa9oqnDkgqwGDyIWiRVKCxBlATa0J8EQR9hEd1LsjcdNkA3s9OjNjNjvjN371yPmMraUcQU7rq3HhlSwDILTzfjCKDeOAXg"
    "LLwEoN97n5xoEWVpwr4BvSDJi6vLAJwchpmasG7AkxoQpBbKpR0Advf2E2auWxcz/TvsG5APWybyY8CWifwZmLUJ/cbo/fwa"
    "+K8JQc49PN87aiDNxJJfBGB9MUgkleRvow4Aw3HfcQNpJgSTEVOfyN88kIZOrKt98NqOVwJHJ6K0u9d9QO5Yqr28sgHA47eI"
    "eTGgkeTN86upNVINNgHodl5+fBPc7YRbx773m/5wsF0D4ONzkDDoTg3oxKZ9bUKQ5O5MRH/FZMBkzLqBL7Cls7bFPdGtAAAA"
    "AElFTkSuQmCC"
)
_CURSOR_SWORD_HOVER_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAABRklEQVR42t2XMUoDQRSGv5FcwEoNEgzqFl4h2FiFWIuCnUWw"
    "C3gAA95ASJFKsEsOYEgVi2AhFnYWEU0KNbHyCGuxecI+shnQldnJXy1vpvm/+efNW8NUlY3DkBnqjNqGf9QSjpWbdMMQ4OT0"
    "CIDrdguAl/5ntKNBCHAzjOrGGLNYBHRBnG/urgBwziUA+8WIkBBbLadDwjkBI45EkoXSzh4A1Xo1RuaiUUv1drgnIB+uSGSH"
    "gCsS2SOQNgn9xuj17BL4KwmR7Lt76nlKwEYiv7wOQHEtiDkV58PxAICPrzfPCdhIiJKIJPWJ7M0DNmnHOu3vr7fTSuDpRGQ7"
    "e90H5Iwl7aXCFgAPPyQWhYCWOL9qtmZm5CDYBmA0eJ77JvjbCfVUbOsPZ8d1AO4f+zGC/mTA9h8g65qESJz7MxH9VkkEkog5"
    "J/ANj6Kz5XVhR3AAAAAASUVORK5CYII="
)

# ==============================================================================
# DESIGN SYSTEM (CSS) — DATA FORGE ENTERPRISE BI & SAAS (BURGUNDY & WARM CREAM)
# Đỏ rượu vang (#6D1B29 / #7C1F27) • Đỏ thương hiệu (#C21F20) • Kem sáng (#FFF8F0 / #FFFFFF)
# Bổ trợ: Teal (#258B86) • Xanh dương (#5277A6) • Cam vàng (#D69A3B) • Tím (#8B6A9C) • Xanh lá (#27845E)
# Font: Plus Jakarta Sans (hiển thị & KPI) • Inter (nội dung & dữ liệu chuẩn tiếng Việt)
# ==============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');

:root {
    --df-brand-red: #C21F20;
    --df-brand-hover: #8C2E2E;
    --df-wine: #7B1E36;
    --df-sidebar: #6B172E;
    --df-sidebar-deep: #480E20;
    --df-accent: #8E233F;
    --df-rose-tint: #FBE9ED;
    --df-growth-pink: #E9A096;
    --df-bg: #F9EAEB;
    --df-surface: #FFFFFF;
    --df-surface-sub: #F6E4E6;
    --df-ai-bg: #FFF1E8;
    --df-border: rgba(123, 30, 54, 0.18);
    --df-text: #292326;
    --df-text-muted: #766A68;
    --df-teal: #258B86;
    --df-blue: #5277A6;
    --df-amber: #D69A3B;
    --df-purple: #8B6A9C;
    --df-green: #27845E;
    /* Compatibility aliases */
    --sb-primary: #C21F20;
    --sb-primary-dk: #8C2E2E;
    --sb-secondary: #D69A3B;
    --sb-dark: #292326;
    --sb-green: #27845E;
    --sb-cream: #F9EAEB;
    --sb-cream2: #F6E4E6;
    --sb-light: #F6E4E6;
    --sb-shadow: 0 6px 24px rgba(88, 18, 38, 0.09);
    --sb-shadow-lg: 0 14px 36px rgba(107, 23, 46, 0.16);
    --sb-ease: cubic-bezier(0.22, 1, 0.36, 1);
    --font-display: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-body: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

html, body, [class*="css"], .stApp,
[data-testid="stMarkdownContainer"],
[data-testid="stCaptionContainer"],
[data-testid="stWidgetLabel"],
[data-testid="stAlert"],
input, textarea, select {
    font-family: var(--font-body) !important;
}
h1, h2, h3, h4, h5, h6,
button, button p,
[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stMarkdownContainer"] p,
[class*="st-key-top_pill_nav"] [data-testid="stRadioOption"] [data-testid="stMarkdownContainer"] p,
.stTabs [data-baseweb="tab"], .stTabs [data-baseweb="tab"] p {
    font-family: var(--font-display) !important;
}
h1, h2, h3, h4, h5 { color: var(--df-text); }
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-thumb { background: var(--df-wine); border-radius: 10px; }

/* ---------- Nền Đỏ mận loang loang (Diffused Plum Mesh) toàn giao diện chính ---------- */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background:
        radial-gradient(ellipse 58% 50% at 0% 10%, rgba(107, 23, 46, 0.38) 0%, rgba(123, 30, 54, 0.18) 42%, transparent 74%),
        radial-gradient(ellipse 52% 48% at 96% 8%, rgba(142, 30, 62, 0.30) 0%, rgba(194, 31, 58, 0.12) 45%, transparent 74%),
        radial-gradient(ellipse 50% 52% at 68% 54%, rgba(123, 30, 54, 0.18) 0%, rgba(226, 146, 158, 0.16) 46%, transparent 76%),
        radial-gradient(ellipse 54% 48% at 14% 94%, rgba(88, 16, 40, 0.32) 0%, rgba(123, 30, 54, 0.14) 48%, transparent 76%),
        radial-gradient(ellipse 48% 44% at 92% 92%, rgba(154, 36, 68, 0.24) 0%, transparent 72%),
        linear-gradient(135deg, #FBECEF 0%, #F4DCE0 38%, #FCF0F1 68%, #F0D1D8 100%) !important;
    background-attachment: fixed !important;
    color: var(--df-text);
}
header[data-testid="stHeader"] { display: none !important; }

.main .block-container, [data-testid="stMainBlockContainer"] {
    background: transparent !important;
    padding: 0 30px 44px 30px !important;
    max-width: 100% !important;
}
/* Cắt khoảng trống thừa trên cùng do các container chỉ chứa <style>/<meta> tạo flex gap */
[data-testid="stMainBlockContainer"] [data-testid="stElementContainer"]:has(.stMarkdown style),
[data-testid="stMainBlockContainer"] [data-testid="stElementContainer"]:has(.stMarkdown meta) {
    display: none !important;
}

/* ---------- Hiệu ứng xuất hiện nhẹ nhàng ---------- */
@keyframes fadeUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
@keyframes fsh { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-18px); } }
@keyframes fltc { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-7px); } }
@keyframes mqrun { from { transform: translateX(0); } to { transform: translateX(-50%); } }
[class*="st-key-card"], .kpi-card, .kpi-card-ent, .phase-bar, .pulse-pill, .camp-health-card, .ent-card {
    animation: fadeUp .45s var(--sb-ease) both;
}

/* ---------- TOP BAR (Đỏ mận loang đậm) ---------- */
.sb-topbar {
    background: linear-gradient(90deg, #430D1E 0%, #6B172E 38%, #821F3B 72%, #4A0F22 100%);
    color: #F6DDE2; font-size: 12px;
    margin: 0 -30px 0 -30px; padding: 8px 30px;
    display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;
    border-bottom: 1px solid rgba(255, 240, 244, 0.14);
}
.sb-topbar span { margin-right: 16px; }
.sb-topbar span b { color: var(--df-growth-pink); margin-right: 5px; font-weight: 700; }
.sb-ttag { font-family: var(--font-display); background: var(--df-brand-red); color: #FFF !important; padding: 2px 11px; border-radius: 20px; font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: .5px; }
.sb-tsoc { display: flex; gap: 6px; }
.sb-tsoc i {
    width: 26px; height: 26px; border-radius: 50%; background: rgba(255, 248, 240, 0.10);
    display: inline-flex; align-items: center; justify-content: center; color: #F7EAE6; font-family: var(--font-display); font-size: 10.5px; font-weight: 700; font-style: normal;
    transition: background-color .25s ease, color .25s ease;
}
.sb-tsoc i:hover { background: var(--df-brand-red); color: #FFF; }

/* ---------- MARQUEE điểm nhấn kiểm toán ---------- */
.sb-marquee {
    background: linear-gradient(90deg, #5B1328 0%, #821F3B 50%, #5B1328 100%);
    margin: 12px -30px 20px -30px; padding: 10px 0; overflow: hidden;
    border-top: 1px solid rgba(255,255,255,0.12); border-bottom: 1px solid rgba(255,255,255,0.12);
}
.sb-mqtrack { display: flex; gap: 38px; white-space: nowrap; width: max-content; animation: mqrun 28s linear infinite; }
.sb-mqitem { display: inline-flex; align-items: center; gap: 10px; color: #FFF8F0; font-size: 12.5px; font-weight: 500; }
.sb-mqitem i { color: var(--df-growth-pink); font-size: 9px; font-style: normal; }

/* ---------- KHU VỰC TRÁI: SIDEBAR ĐỎ MẬN LOANG ĐẬM (#741B35 → #3E0B1B) ---------- */
@media (min-width: 960px) {
    [data-testid="stSidebar"][aria-expanded="true"] {
        min-width: 258px !important;
        max-width: 268px !important;
        width: 262px !important;
    }
}
[data-testid="stSidebar"] {
    background:
        radial-gradient(ellipse 68% 45% at 86% 12%, rgba(168, 42, 74, 0.42) 0%, transparent 56%),
        radial-gradient(ellipse 64% 44% at 14% 58%, rgba(142, 30, 62, 0.34) 0%, transparent 58%),
        radial-gradient(ellipse 70% 48% at 20% 90%, rgba(226, 130, 150, 0.16) 0%, transparent 56%),
        linear-gradient(175deg, #741B35 0%, #5B1328 52%, #3E0B1B 100%) !important;
    border-right: 1px solid rgba(255, 240, 244, 0.16) !important;
    box-shadow: 4px 0 28px rgba(62, 11, 27, 0.26);
}
[data-testid="stSidebarContent"] { background: transparent !important; padding: 14px 14px 20px 14px; color: #FFF8F0; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] { color: #FFF8F0 !important; }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 6px !important; }
.brand-red-banner {
    display: flex; align-items: center; gap: 12px;
    background: transparent; margin: 4px 2px 14px 2px; padding: 4px 4px 14px 4px;
    border-bottom: 1px solid rgba(255, 248, 240, 0.14); color: #FFFFFF;
}
.brand-svg-mark {
    width: 42px; height: 42px; flex-shrink: 0; display: flex; align-items: center; justify-content: center;
    transition: transform .35s var(--sb-ease);
}
.brand-red-banner:hover .brand-svg-mark { transform: scale(1.06) rotate(-4deg); }
.brand-red-title {
    font-family: var(--font-display); font-size: 20px; font-weight: 800; color: #FFFFFF;
    line-height: 1.05; letter-spacing: 0.6px;
}
.brand-red-sub {
    font-size: 9.5px; text-transform: uppercase; letter-spacing: 1.2px;
    color: rgba(255, 248, 240, 0.68); margin-top: 3px; line-height: 1.3; font-weight: 600;
}
.nav-caption {
    font-family: var(--font-display); font-size: 11px; color: rgba(255, 248, 240, 0.60);
    margin: 4px 8px 4px 8px; letter-spacing: 1.2px; font-weight: 700; text-transform: uppercase;
}

/* Tiến độ, thẻ giới thiệu & tài khoản cuối sidebar */
.side-progress {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 248, 240, 0.14);
    border-radius: 14px; padding: 13px 14px; margin-top: 12px;
    backdrop-filter: blur(8px);
}
.side-progress-title {
    font-family: var(--font-display); font-size: 12px; color: var(--df-growth-pink);
    margin-bottom: 8px; letter-spacing: 0.8px; font-weight: 700; text-transform: uppercase;
}
.side-row {
    display: flex; justify-content: space-between; align-items: center;
    font-size: 11.5px; font-weight: 500; color: rgba(255, 248, 240, 0.88); margin-bottom: 6px;
}
.side-row:last-child { margin-bottom: 0; }
.side-progress .badge.ok { background: rgba(39, 132, 94, 0.28); color: #8EF0C4; border: 1px solid rgba(142, 240, 196, 0.28); }
.side-progress .badge.warn { background: rgba(214, 154, 59, 0.26); color: #FAD692; border: 1px solid rgba(250, 214, 146, 0.28); }
.side-progress .badge.fail { background: rgba(194, 31, 32, 0.36); color: #FFC6C6; border: 1px solid rgba(255, 198, 198, 0.30); }
.side-progress .badge.idle { background: rgba(255, 255, 255, 0.11); color: rgba(255, 248, 240, 0.72); }

.side-promo-red {
    position: relative; overflow: hidden; margin-top: 12px; border-radius: 16px; padding: 16px 15px; color: #FFFFFF;
    background: linear-gradient(145deg, rgba(194, 31, 32, 0.34) 0%, rgba(75, 17, 29, 0.86) 100%);
    border: 1px solid rgba(255, 248, 240, 0.16);
    box-shadow: 0 10px 26px rgba(32, 6, 12, 0.26);
    transition: transform .3s var(--sb-ease), border-color .25s ease;
}
.side-promo-red:hover { transform: translateY(-2px); border-color: rgba(233, 160, 150, 0.42); }
.side-promo-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }
.side-promo-title { font-family: var(--font-display); font-size: 15px; font-weight: 800; line-height: 1.32; color: #FFFFFF; margin-bottom: 6px; }
.side-promo-sub { font-size: 11px; color: rgba(255, 248, 240, 0.78); line-height: 1.45; }

.side-account-card {
    display: flex; align-items: center; gap: 10px;
    margin-top: 14px; padding: 12px 6px 2px 6px;
    border-top: 1px solid rgba(255, 248, 240, 0.14);
}
.side-acc-ava {
    width: 36px; height: 36px; border-radius: 50%; flex-shrink: 0;
    background: linear-gradient(135deg, var(--df-brand-red), var(--df-accent));
    border: 2px solid rgba(255, 248, 240, 0.45);
    color: #FFFFFF; font-family: var(--font-display); font-size: 12px; font-weight: 800;
    display: flex; align-items: center; justify-content: center;
}
.side-acc-name { font-family: var(--font-display); font-size: 13px; font-weight: 700; color: #FFFFFF; line-height: 1.2; }
.side-acc-role { font-size: 11px; color: rgba(255, 248, 240, 0.68); margin-top: 2px; }

.badge { font-family: var(--font-display); font-size: 10.5px; font-weight: 700; padding: 3px 10px; border-radius: 8px; border: none; white-space: nowrap; transition: transform .2s ease; }
.badge:hover { transform: scale(1.04); }
.badge.ok { background: #E6F5EE; color: var(--df-green); }
.badge.warn { background: #FDF4E3; color: #A66E14; }
.badge.fail { background: var(--df-rose-tint); color: var(--df-brand-red); }
.badge.idle { background: var(--df-surface-sub); color: var(--df-text-muted); }

/* ---------- Header & thanh tìm kiếm trên Main Workspace ---------- */
.top-glass-bar {
    display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;
    background: rgba(255, 250, 251, 0.84); backdrop-filter: blur(14px);
    border: 1px solid var(--df-border); border-radius: 16px;
    padding: 9px 16px; margin: 12px 0 4px 0;
    box-shadow: 0 4px 18px rgba(88, 18, 38, 0.06); transition: box-shadow .3s ease, border-color .25s ease;
}
.top-glass-bar:hover { border-color: rgba(123, 30, 54, 0.34); box-shadow: 0 8px 24px rgba(88, 18, 38, 0.11); }
.top-search {
    flex: 1; min-width: 240px; max-width: 560px; background: var(--df-surface-sub); border: 1.5px solid var(--df-border);
    border-radius: 999px; padding: 8px 16px; font-size: 12.5px; color: var(--df-text-muted); font-weight: 500;
    display: flex; align-items: center; justify-content: space-between; gap: 8px;
    transition: border-color .25s ease, background-color .25s ease;
}
.top-search:hover { border-color: var(--df-brand-red); background: #FFFFFF; color: var(--df-text); }
.top-search-kbd {
    font-family: var(--font-display); font-size: 10.5px; font-weight: 600; color: var(--df-text-muted);
    background: #FFFFFF; border: 1px solid var(--df-border); padding: 1px 8px; border-radius: 6px;
}
.top-right { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.bell-wrap {
    position: relative; width: 36px; height: 36px; border-radius: 50%; background: var(--df-surface-sub); border: 1px solid var(--df-border);
    display: flex; align-items: center; justify-content: center; font-size: 15px; transition: transform .25s ease, border-color .25s ease;
}
.bell-wrap:hover { transform: scale(1.08); border-color: var(--df-brand-red); }
.bell-dot { position: absolute; top: -4px; right: -4px; background: var(--df-brand-red); color: #FFF; font-size: 9.5px; font-weight: 700; padding: 1px 6px; border-radius: 50px; }
.source-chip {
    background: var(--df-surface-sub); color: var(--df-wine); border: 1px solid var(--df-border); border-radius: 50px; padding: 5px 13px; font-size: 11.5px; font-weight: 600;
    max-width: 280px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.profile-chip { display: flex; align-items: center; gap: 8px; background: var(--df-surface-sub); border: 1px solid var(--df-border); border-radius: 50px; padding: 3px 13px 3px 4px; transition: transform .25s ease, border-color .25s ease; }
.profile-chip:hover { transform: translateY(-1px); border-color: var(--df-brand-red); }
.avatar {
    width: 30px; height: 30px; border-radius: 50%; color: #FFF; font-weight: 700; font-size: 11px;
    background: linear-gradient(135deg, var(--df-sidebar), var(--df-brand-red));
    display: flex; align-items: center; justify-content: center; box-shadow: 0 3px 10px rgba(109, 27, 41, 0.28);
}
.p-name { font-family: var(--font-display); font-size: 12px; font-weight: 700; color: var(--df-text); line-height: 1.2; }
.p-role { font-size: 10px; color: var(--df-text-muted); text-transform: uppercase; letter-spacing: .6px; }

/* ---------- Tiêu đề trang ---------- */
.page-header { display: flex; justify-content: center; align-items: center; text-align: center; margin: 14px 0 8px 0; }
.page-greet { display: flex; flex-direction: column; align-items: center; gap: 0; }
.greet-mark { display: none; }
.page-header .page-greet > div::before {
    content: "Data Forge Analytics"; display: block;
    font-family: var(--font-display); font-size: 14px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; color: var(--df-brand-red); margin-bottom: 2px;
}
.page-title {
    font-family: var(--font-display) !important; font-size: clamp(24px, 3vw, 36px); font-weight: 800;
    color: var(--df-text); margin: 0; line-height: 1.2;
}
.page-header [data-testid="stHeaderActionElements"] { display: none !important; }
.page-title::after {
    content: ""; display: block; width: 58px; height: 4px; border-radius: 4px; margin: 10px auto 8px auto;
    background: linear-gradient(90deg, var(--df-brand-red), var(--df-amber));
}
.page-sub { font-size: 13px; color: var(--df-text-muted); line-height: 1.7; max-width: 720px; margin: 0 auto; }
.header-meta { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
[class*="st-key-btn_toggle_theme"] button {
    padding: 8px 11px !important;
    font-size: 12.5px !important;
    white-space: nowrap !important;
}

/* ---------- Thanh điều hướng nghiệp vụ (Floating Pill Navbar) ---------- */
[class*="st-key-top_pill_nav"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 8px 0 12px 0 !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    width: 100% !important;
}
[class*="st-key-top_pill_nav"] [data-testid="stRadio"] {
    display: flex !important;
    justify-content: center !important;
    width: 100% !important;
}
[class*="st-key-top_pill_nav"] [data-testid="stRadio"] > label {
    display: none !important;
}
[class*="st-key-top_pill_nav"] [data-testid="stRadio"] div[role="radiogroup"] {
    display: inline-flex !important;
    flex-direction: row !important;
    flex-wrap: wrap !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 4px !important;
    background: rgba(255, 250, 251, 0.86) !important;
    backdrop-filter: blur(14px) !important;
    border: 1px solid var(--df-border) !important;
    border-radius: 999px !important;
    padding: 5px 8px !important;
    box-shadow: 0 6px 20px rgba(88, 18, 38, 0.08) !important;
    width: fit-content !important;
    max-width: 100% !important;
    margin: 0 auto !important;
}
[class*="st-key-top_pill_nav"] [data-testid="stRadioOption"] {
    position: relative !important;
    background: transparent !important;
    border: none !important;
    border-radius: 999px !important;
    padding: 8px 14px !important;
    margin: 0 !important;
    cursor: var(--cursor-pointer) !important;
    color: var(--df-text) !important;
    white-space: nowrap !important;
    transition: background-color 0.25s ease, color 0.22s ease, transform 0.25s ease, box-shadow 0.25s ease !important;
}
[class*="st-key-top_pill_nav"] [data-testid="stRadioOption"] input[type="radio"],
[class*="st-key-top_pill_nav"] [data-testid="stRadioOption"] > div > div:not([data-testid="stMarkdownContainer"]) {
    display: none !important;
}
[class*="st-key-top_pill_nav"] [data-testid="stRadioOption"] > div {
    gap: 0 !important; padding: 0 !important; margin: 0 !important;
}
[class*="st-key-top_pill_nav"] [data-testid="stRadioOption"] [data-testid="stMarkdownContainer"] {
    background: transparent !important;
}
[class*="st-key-top_pill_nav"] [data-testid="stRadioOption"] [data-testid="stMarkdownContainer"] p {
    font-family: var(--font-display) !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    color: inherit !important;
    margin: 0 !important;
    line-height: 1.2 !important;
    white-space: nowrap !important;
}
[class*="st-key-top_pill_nav"] [data-testid="stRadioOption"]:hover {
    background: var(--df-rose-tint) !important;
    color: var(--df-brand-hover) !important;
    transform: translateY(-1px) !important;
}
[class*="st-key-top_pill_nav"] [data-testid="stRadioOption"][data-selected="true"],
[class*="st-key-top_pill_nav"] [data-testid="stRadioOption"]:has(input:checked) {
    background: var(--df-brand-red) !important;
    color: #FFFFFF !important;
    box-shadow: 0 6px 16px rgba(194, 31, 32, 0.28) !important;
}
[class*="st-key-top_pill_nav"] [data-testid="stRadioOption"][data-selected="true"]:hover,
[class*="st-key-top_pill_nav"] [data-testid="stRadioOption"]:has(input:checked):hover {
    background: var(--df-brand-hover) !important;
    color: #FFFFFF !important;
    box-shadow: 0 8px 20px rgba(140, 46, 46, 0.34) !important;
}
[class*="st-key-top_pill_nav"] [data-testid="stRadioOption"][data-selected="true"] [data-testid="stMarkdownContainer"] p,
[class*="st-key-top_pill_nav"] [data-testid="stRadioOption"]:has(input:checked) [data-testid="stMarkdownContainer"] p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}
@media (max-width: 960px) {
    [class*="st-key-top_pill_nav"] [data-testid="stRadio"] div[role="radiogroup"] {
        border-radius: 18px !important;
    }
}

/* ---------- Thanh 5 giai đoạn ---------- */
.phase-bar {
    display: flex; align-items: center; background: var(--df-surface); border: 1px solid var(--df-border); border-radius: 14px;
    padding: 11px 20px; margin-bottom: 18px; gap: 8px; overflow-x: auto; box-shadow: 0 2px 12px rgba(41, 35, 38, 0.04);
}
.phase { display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 600; color: var(--df-text-muted); white-space: nowrap; }
.phase-dot { font-family: var(--font-display); width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11.5px; font-weight: 700; background: var(--df-surface-sub); border: 1.5px solid var(--df-border); color: var(--df-text-muted); }
.phase.done { color: var(--df-green); } .phase.done .phase-dot { background: var(--df-green); border-color: var(--df-green); color: #FFF; }
.phase.warn { color: #A66E14; } .phase.warn .phase-dot { background: var(--df-amber); border-color: var(--df-amber); color: #FFF; }
.phase.fail { color: var(--df-brand-red); } .phase.fail .phase-dot { background: var(--df-brand-red); border-color: var(--df-brand-red); color: #FFF; }
.phase-line { flex: 1; min-width: 18px; height: 2.5px; background: var(--df-border); border-radius: 4px; }
.phase-line.done { background: linear-gradient(90deg, var(--df-green), var(--df-teal)); }

/* ---------- Card nền kính mờ phớt đỏ mận + border dịu ---------- */
[class*="st-key-card"] {
    background: linear-gradient(145deg, rgba(255, 252, 252, 0.88) 0%, rgba(253, 243, 245, 0.82) 100%);
    backdrop-filter: blur(14px);
    border: 1px solid var(--df-border); border-radius: 18px !important; padding: 20px 22px;
    box-shadow: var(--sb-shadow);
    transition: transform .3s var(--sb-ease), box-shadow .3s ease, border-color .25s ease !important;
}
[class*="st-key-card"]:hover { transform: translateY(-3px); box-shadow: 0 12px 30px rgba(88, 18, 38, 0.14) !important; border-color: rgba(123, 30, 54, 0.34) !important; }
.card-title { font-family: var(--font-display); font-size: 17.5px; font-weight: 700; color: var(--df-text); margin: 0; }
.card-title::before { content: "• "; color: var(--df-brand-red); }
.card-sub { font-size: 12.5px; color: var(--df-text-muted); margin: 3px 0 12px 0; line-height: 1.55; }

/* ---------- BANNER DATA FORGE (Gradient Đỏ rượu vang + Hồng kem sang trọng) ---------- */
[class*="st-key-card_hero_banner"] {
    position: relative;
    overflow: hidden;
    background:
        radial-gradient(circle at 82% 24%, rgba(255, 224, 212, 0.22) 0%, transparent 42%),
        linear-gradient(115deg, #FBF0EC 0%, #F6D8CE 34%, #B52A32 68%, #6D1B29 100%) !important;
    border: 1px solid var(--df-border) !important;
    border-radius: 20px !important;
    padding: 24px 26px !important;
    min-height: 256px;
    box-shadow: 0 10px 30px rgba(109, 27, 41, 0.12) !important;
}
[class*="st-key-card_hero_banner"]:hover { transform: translateY(-2px) !important; border-color: rgba(194, 31, 32, 0.35) !important; }
.df-banner-eyebrow {
    font-family: var(--font-display); font-size: 11px; font-weight: 700; letter-spacing: 1.6px;
    text-transform: uppercase; color: var(--df-wine); margin-bottom: 6px;
}
.df-banner-title {
    font-family: var(--font-display); font-size: clamp(28px, 2.8vw, 38px); font-weight: 800;
    color: var(--df-sidebar); line-height: 1.08; margin: 0 0 10px 0; letter-spacing: -0.4px;
}
.df-banner-sub {
    font-size: 14px; font-weight: 500; color: var(--df-text); line-height: 1.55;
    max-width: 340px; margin: 0 0 16px 0;
}
.df-banner-art {
    display: flex; align-items: center; justify-content: center; width: 100%; height: 100%; min-height: 196px;
}

/* ---------- TRỢ LÝ DATA FORGE AI ĐỘC LẬP (#FFF1E8 cam kem riêng biệt) ---------- */
[class*="st-key-card_hero_ai"] {
    background: var(--df-ai-bg) !important;
    border: 1.5px solid #F0D2C2 !important;
    border-radius: 20px !important;
    padding: 18px 20px !important;
    min-height: 256px;
    box-shadow: 0 8px 24px rgba(140, 41, 36, 0.07) !important;
}
[class*="st-key-card_hero_ai"]:hover {
    transform: translateY(-2px) !important;
    border-color: #E2B69E !important;
}
.df-ai-head {
    display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 10px;
}
.df-ai-title {
    font-family: var(--font-display); font-size: 15.5px; font-weight: 800; color: var(--df-text);
    display: flex; align-items: center; gap: 7px;
}
.df-ai-online {
    display: inline-flex; align-items: center; gap: 5px;
    font-family: var(--font-display); font-size: 11px; font-weight: 700;
    color: var(--df-green); background: #E6F5EE; border: 1px solid #BCE3D1;
    padding: 3px 10px; border-radius: 999px; white-space: nowrap;
}
.df-ai-body {
    display: flex; align-items: center; gap: 12px; margin-bottom: 10px;
}
.df-ai-bubble {
    flex: 1; background: #FFFFFF; border: 1px solid var(--df-border); border-radius: 14px;
    padding: 10px 13px; font-size: 12px; color: var(--df-text); line-height: 1.5;
    box-shadow: 0 3px 10px rgba(41, 35, 38, 0.04);
}
.df-ai-bubble b { font-family: var(--font-display); color: var(--df-text); display: block; margin-bottom: 4px; font-size: 12.2px; }
.df-ai-bubble ul { margin: 0; padding-left: 0; list-style: none; color: var(--df-text-muted); font-size: 11.5px; }
.df-ai-bubble li { margin-bottom: 2px; }
.df-ai-bubble li span { color: var(--df-green); font-weight: 700; margin-right: 4px; }
.df-ai-reply-chip {
    background: #FFFFFF; border: 1px solid var(--df-border); border-left: 3px solid var(--df-brand-red);
    border-radius: 10px; padding: 8px 11px; margin-bottom: 8px; font-size: 11.8px; color: var(--df-text);
    max-height: 76px; overflow-y: auto;
}
[class*="st-key-card_hero_ai"] [data-testid="stTextInput"] input {
    background: #FFFFFF !important; border: 1px solid var(--df-border) !important;
    border-radius: 12px !important; font-size: 12.5px !important; padding: 8px 12px !important;
}

/* ---------- NÂNG CẤP 4 THẺ KPI NỀN TRẮNG + ICON ĐA MÀU + SPARKLINE ---------- */
.kpi-grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 6px 0 18px 0; }
@media (max-width: 1080px) { .kpi-grid-4 { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 600px) { .kpi-grid-4 { grid-template-columns: 1fr; } }
.kpi-card-ent {
    background: linear-gradient(145deg, rgba(255, 252, 252, 0.90) 0%, rgba(252, 240, 243, 0.84) 100%);
    backdrop-filter: blur(12px);
    border: 1px solid var(--df-border); border-radius: 18px;
    padding: 16px 18px 14px 18px; box-shadow: var(--sb-shadow);
    display: flex; flex-direction: column; justify-content: space-between; gap: 10px;
    transition: transform .28s var(--sb-ease), box-shadow .28s ease, border-color .25s ease;
    cursor: var(--cursor-pointer);
}
.kpi-card-ent:hover { transform: translateY(-4px); box-shadow: 0 12px 28px rgba(88, 18, 38, 0.14); border-color: rgba(123, 30, 54, 0.34); }
.kpi-ent-top { display: flex; align-items: center; gap: 11px; }
.kpi-ent-ico {
    width: 42px; height: 42px; border-radius: 12px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
}
.kpi-ent-ico.red { background: var(--df-rose-tint); color: var(--df-brand-red); }
.kpi-ent-ico.amber { background: #FDF4E3; color: var(--df-amber); }
.kpi-ent-ico.purple { background: #F3EEF6; color: var(--df-purple); }
.kpi-ent-ico.teal { background: #E6F4F2; color: var(--df-teal); }
.kpi-ent-lbl { font-size: 12px; font-weight: 600; color: var(--df-text-muted); line-height: 1.25; }
.kpi-ent-val {
    font-family: var(--font-display); font-size: 21px; font-weight: 800; color: var(--df-text);
    line-height: 1.15; margin-top: 2px; font-variant-numeric: tabular-nums;
}
.kpi-ent-bottom { display: flex; justify-content: space-between; align-items: flex-end; gap: 8px; }
.kpi-ent-delta { font-size: 11.5px; font-weight: 600; line-height: 1.3; }
.kpi-ent-delta.pos { color: var(--df-green); }
.kpi-ent-delta.neg { color: var(--df-brand-red); }
.kpi-ent-delta.neu { color: var(--df-text-muted); }
.kpi-ent-delta small { display: block; font-weight: 400; color: var(--df-text-muted); font-size: 11px; margin-top: 1px; }
.kpi-spark { width: 88px; height: 32px; flex-shrink: 0; }

/* ---------- THẺ INSIGHT QUAN TRỌNG ---------- */
.df-insight-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.df-insight-title { font-family: var(--font-display); font-size: 16.5px; font-weight: 800; color: var(--df-text); display: flex; align-items: center; gap: 8px; }
.df-insight-list { display: flex; flex-direction: column; gap: 10px; }
.df-insight-item {
    display: flex; align-items: flex-start; gap: 12px; padding: 12px 14px;
    background: #FFFDFB; border: 1px solid var(--df-border); border-radius: 14px;
    transition: transform .22s ease, border-color .22s ease, background-color .22s ease;
}
.df-insight-item:hover { transform: translateX(3px); border-color: #D8C4B8; background: #FFF8F4; }
.df-ins-ico {
    width: 36px; height: 36px; border-radius: 10px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center; font-size: 15px; font-weight: 700;
}
.df-ins-ico.red { background: var(--df-rose-tint); color: var(--df-brand-red); }
.df-ins-ico.amber { background: #FDF4E3; color: var(--df-amber); }
.df-ins-ico.purple { background: #F3EEF6; color: var(--df-purple); }
.df-ins-ico.teal { background: #E6F4F2; color: var(--df-teal); }
.df-ins-h { font-family: var(--font-display); font-size: 13.5px; font-weight: 700; color: var(--df-text); line-height: 1.3; }
.df-ins-p { font-size: 12px; color: var(--df-text-muted); margin-top: 3px; line-height: 1.45; }
.df-ins-metric {
    display: inline-block; margin-top: 5px; font-family: var(--font-display); font-size: 11px; font-weight: 700;
    padding: 2px 9px; border-radius: 999px; background: var(--df-surface-sub); color: var(--df-wine);
}

/* Bộ lọc thời gian nhỏ gọn cho biểu đồ chính */
[class*="st-key-ov_period_filter"] [data-testid="stRadio"] > label { display: none !important; }
[class*="st-key-ov_period_filter"] div[role="radiogroup"] { gap: 4px !important; flex-wrap: wrap !important; }
[class*="st-key-ov_period_filter"] [data-testid="stRadioOption"] {
    padding: 5px 12px !important; border-radius: 999px !important;
    background: var(--df-surface-sub) !important; border: 1px solid var(--df-border) !important;
    color: var(--df-text) !important;
}
[class*="st-key-ov_period_filter"] [data-testid="stRadioOption"] input[type="radio"],
[class*="st-key-ov_period_filter"] [data-testid="stRadioOption"] > div > div:not([data-testid="stMarkdownContainer"]) {
    display: none !important;
}
[class*="st-key-ov_period_filter"] [data-testid="stRadioOption"] > div { gap: 0 !important; }
[class*="st-key-ov_period_filter"] [data-testid="stRadioOption"] p {
    font-family: var(--font-display) !important; font-size: 12px !important; font-weight: 600 !important; margin: 0 !important;
}
[class*="st-key-ov_period_filter"] [data-testid="stRadioOption"][data-selected="true"],
[class*="st-key-ov_period_filter"] [data-testid="stRadioOption"]:has(input:checked) {
    background: var(--df-brand-red) !important; border-color: var(--df-brand-red) !important; color: #FFFFFF !important;
}
[class*="st-key-ov_period_filter"] [data-testid="stRadioOption"][data-selected="true"] p,
[class*="st-key-ov_period_filter"] [data-testid="stRadioOption"]:has(input:checked) p {
    color: #FFFFFF !important;
}

/* ---------- HERO phụ (Khu vực Orbit DF Data Forge — Đỏ mận loang sang trọng) ---------- */
.hero-glass { background: var(--df-bg); border-radius: 18px; padding: 24px; margin-bottom: 16px; }
[class*="st-key-card_hero_glass"] {
    position: relative; overflow: hidden;
    background:
        radial-gradient(circle at 6% 12%, rgba(123, 30, 54, 0.14) 0%, transparent 46%),
        radial-gradient(circle at 92% 86%, rgba(142, 30, 62, 0.16) 0%, transparent 50%),
        radial-gradient(circle at 54% 18%, rgba(226, 146, 158, 0.18) 0%, transparent 46%),
        linear-gradient(135deg, rgba(255, 251, 252, 0.90) 0%, rgba(251, 237, 240, 0.84) 52%, rgba(246, 224, 230, 0.88) 100%) !important;
    backdrop-filter: blur(16px);
    box-shadow: var(--sb-shadow) !important; border: 1px solid var(--df-border) !important; padding: 30px 32px !important;
}
[class*="st-key-card_hero_glass"]:hover { transform: none !important; }
[class*="st-key-card_hero_glass"]::before {
    content: "DATA FORGE"; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
    font-family: var(--font-display); font-weight: 800; font-size: 12vw; color: rgba(123, 30, 54, 0.045);
    pointer-events: none; white-space: nowrap; z-index: 0;
}
[class*="st-key-card_hero_glass"]::after {
    content: ""; position: absolute; width: 420px; height: 420px; top: -110px; right: -90px; border-radius: 50%;
    background: radial-gradient(circle, rgba(142, 30, 62, 0.14), transparent 70%); animation: fsh 8s ease-in-out infinite; z-index: 0;
}
[class*="st-key-card_hero_glass"] > div { position: relative; z-index: 1; }
.hero-tag {
    font-family: var(--font-display); display: inline-flex; align-items: center; gap: 8px; background: var(--df-surface-sub); border: 1px solid var(--df-border); border-radius: 30px; padding: 5px 15px 5px 5px;
    margin-bottom: 16px; font-size: 12px; font-weight: 600; color: var(--df-text);
}
.hero-tag::before {
    content: "★"; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
    background: linear-gradient(135deg, var(--df-brand-red), var(--df-wine)); color: #FFF; font-size: 11px;
}
.hero-h1 { font-family: var(--font-display); font-size: clamp(28px, 3.8vw, 46px); font-weight: 800; color: var(--df-text); line-height: 1.14; letter-spacing: -0.3px; margin: 0 0 14px 0; }
.hero-h1 span { color: var(--df-brand-red); position: relative; display: inline-block; font-size: .64em; line-height: 1.25; }
.hero-h1 span::before { content: ""; position: absolute; left: 0; right: 0; bottom: 3px; height: 8px; background: rgba(194, 31, 32, 0.12); border-radius: 4px; z-index: -1; }
.hero-desc { font-size: 13.5px; color: var(--df-text-muted); line-height: 1.7; max-width: 500px; margin: 0; }
/* ---------- Khối Orbit xoay quanh Logo DF Data Force (Enterprise SaaS Motion) ---------- */
.orbit-stage {
    position: relative;
    width: 100%;
    max-width: 480px;
    height: 400px;
    margin: 4px auto 26px auto;
    overflow: visible;
}

/* LỚP 1: Đường quỹ đạo tròn 310px (bán kính R = 155px) đứng yên, căn chính xác theo tâm Logo */
.orbit-ring {
    width: 310px;
    height: 310px;
    border-radius: 50%;
    position: absolute;
    left: 50%;
    top: 50%;
    margin-left: -155px;
    margin-top: -155px;
    border: 1.5px dashed rgba(232, 40, 26, 0.35);
    background: radial-gradient(circle, rgba(232, 40, 26, 0.02) 0%, rgba(2, 132, 199, 0.02) 100%);
    box-shadow: 0 0 35px rgba(232, 40, 26, 0.08), inset 0 0 25px rgba(2, 132, 199, 0.06);
    pointer-events: none;
    z-index: 1;
}

/* Điểm sáng nhỏ chạy nhẹ trên quỹ đạo */
.orbit-mote-track {
    position: absolute;
    width: 310px;
    height: 310px;
    border-radius: 50%;
    left: 50%;
    top: 50%;
    margin-left: -155px;
    margin-top: -155px;
    pointer-events: none;
    z-index: 2;
    animation: spinTrack 28s linear infinite;
}
@keyframes spinTrack {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
.orbit-dot {
    position: absolute;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    box-shadow: 0 0 10px currentColor;
}
.orbit-dot.d1 {
    top: -3.5px;
    left: 50%;
    margin-left: -3.5px;
    background: #E8281A;
    color: #E8281A;
}
.orbit-dot.d2 {
    bottom: -3.5px;
    left: 50%;
    margin-left: -3.5px;
    background: #0284C7;
    color: #0284C7;
}

/* LOGO DF DATA FORCE: Cố định tâm tuyệt đối (Pixel Margin) không rung lắc, không xoay */
.hero-circle {
    width: 240px;
    height: 240px;
    border-radius: 50%;
    position: absolute;
    left: 50%;
    top: 50%;
    margin-left: -120px;
    margin-top: -120px;
    background: radial-gradient(circle at 45% 42%, #FFFDFB 0%, #FFF5EC 55%, #FEDBB7 100%);
    border: 1.5px solid rgba(232, 40, 26, 0.22);
    box-shadow: 0 16px 50px rgba(232, 40, 26, 0.14), 0 0 30px rgba(2, 132, 199, 0.08), inset 0 0 25px rgba(255, 255, 255, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    z-index: 3;
    pointer-events: auto;
}
.hero-circle .hc-num {
    font-family: var(--font-display);
    font-weight: 800;
    font-size: 56px;
    color: var(--sb-primary);
    line-height: 1;
    letter-spacing: 0.5px;
    text-shadow: 0 2px 12px rgba(232, 40, 26, 0.18);
}
.hero-circle .hc-lbl {
    font-family: var(--font-display);
    font-size: 23px;
    color: var(--sb-dark);
    font-weight: 700;
    letter-spacing: 0.4px;
    margin-top: 2px;
}
.hero-circle .hc-sub {
    font-family: var(--font-body);
    font-size: 9px;
    color: #777;
    text-transform: uppercase;
    letter-spacing: 1.4px;
    margin-top: 3px;
    font-weight: 700;
}

/* LỚP 2: ORBIT ROTATOR — Một wrapper độc lập quay 360 độ liên tục trong 30s */
@keyframes orbitSpin360 {
    from {
        transform: rotate(0deg);
    }
    to {
        transform: rotate(360deg);
    }
}
.orbit-rotator {
    position: absolute;
    left: 50%;
    top: 50%;
    width: 0;
    height: 0;
    margin: 0;
    padding: 0;
    pointer-events: none;
    z-index: 6;
    animation: orbitSpin360 30s linear infinite;
    will-change: transform;
}

/* LỚP 3: BA ORBIT ITEMS — Phân bố chính xác trên quỹ đạo R = 155px, cách nhau 120 độ */
.orbit-item {
    position: absolute;
    width: 0;
    height: 0;
    pointer-events: none;
}
/* Item 1: Auto-Clean (góc -150 độ, phía trên bên trái: x = -134px, y = -78px) */
.orbit-item.item-1 {
    left: -134px;
    top: -78px;
}
/* Item 2: 7 Audit Tests (góc -30 độ, phía trên bên phải: x = +134px, y = -78px) */
.orbit-item.item-2 {
    left: 134px;
    top: -78px;
}
/* Item 3: HITL Guardrail (góc +90 độ, phía dưới chính giữa: x = 0, y = +155px) */
.orbit-item.item-3 {
    left: 0px;
    top: 155px;
}

/* LỚP 4: COUNTER ROTATION — Bù góc quay để chữ và icon luôn nằm ngang thẳng đứng */
@keyframes orbitCounterSpin360 {
    from {
        transform: translate(-50%, -50%) rotate(0deg);
    }
    to {
        transform: translate(-50%, -50%) rotate(-360deg);
    }
}
.orbit-counter {
    position: absolute;
    left: 0;
    top: 0;
    transform: translate(-50%, -50%);
    pointer-events: auto;
    animation: orbitCounterSpin360 30s linear infinite;
    will-change: transform;
}

/* Tạm dừng chuyển động khi rê chuột để người dùng đọc thông tin */
.orbit-rotator:hover,
.orbit-rotator:hover .orbit-counter {
    animation-play-state: paused !important;
}

/* Thẻ Floating Badge */
.fcard {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 8px 14px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08), 0 2px 6px rgba(0, 0, 0, 0.04);
    display: flex;
    align-items: center;
    gap: 9px;
    text-align: left;
    white-space: nowrap;
    border: 1.5px solid rgba(254, 240, 220, 0.95);
    cursor: pointer;
    transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1),
                box-shadow 0.25s ease,
                border-color 0.25s ease;
    user-select: none;
}
.fcard:hover {
    transform: scale(1.06);
    box-shadow: 0 16px 36px rgba(232, 40, 26, 0.22), 0 4px 14px rgba(2, 132, 199, 0.14) !important;
    border-color: rgba(232, 40, 26, 0.5) !important;
}

.fcoi { width: 34px; height: 34px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 15px; }
.fcoi.r { background: rgba(232, 40, 26, 0.11); color: var(--sb-primary); }
.fcoi.y { background: rgba(246, 166, 35, 0.14); color: var(--sb-secondary); }
.fcoi.g { background: rgba(45, 106, 79, 0.11); color: var(--sb-green); }
.fcnum { font-family: var(--font-display); font-weight: 700; font-size: 14px; color: var(--sb-dark); display: block; line-height: 1.1; }
.fcsm { font-family: var(--font-body); font-size: 10px; color: #999; }
.hstats { display: flex; gap: 22px; flex-wrap: wrap; margin-top: 28px; align-items: center; }
.hstat .snum { font-family: var(--font-display); font-size: 30px; font-weight: 800; color: var(--sb-dark); display: block; line-height: 1; font-variant-numeric: tabular-nums; transition: transform 0.35s var(--sb-ease); }
.hstat .snum .hstat-val { display: inline-block; font-variant-numeric: tabular-nums; will-change: transform, opacity; transition: color 0.25s ease, text-shadow 0.25s ease; }
.hstat .snum em { color: var(--sb-primary); font-style: normal; }
.hstat small { font-size: 10.5px; color: #AAA; text-transform: uppercase; letter-spacing: 1px; }
.hstat.is-counting .snum { transform: translateY(-2px); }
.hstat.is-counting .snum .hstat-val { color: var(--df-wine); text-shadow: 0 4px 14px rgba(194, 31, 32, 0.22); }
@keyframes hstatSettlePop {
    0% { transform: scale(1) translateY(0); }
    45% { transform: scale(1.12) translateY(-3px); color: var(--df-brand-red); }
    100% { transform: scale(1) translateY(0); color: var(--sb-dark); }
}
.hstat.is-settled .snum .hstat-val { animation: hstatSettlePop 0.52s cubic-bezier(0.22, 1, 0.36, 1) forwards; }
[data-testid="stElementContainer"]:has(iframe[height="0"]) {
    height: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
    position: absolute !important;
}
.sdiv { width: 1px; background: #DDD; height: 38px; }

/* ---------- 3 Ô Mini-Stat chuyển động lên xuống trục Y (Phased Vertical Float) ---------- */
@keyframes floatBobbingY {
    0%, 100% {
        transform: translateY(0px);
    }
    50% {
        transform: translateY(-8px);
    }
}

.mini-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 16px;
}

/* Lớp bọc ngoài: chịu trách nhiệm chuyển động float trục Y đều đặn, chu kỳ 4.5s */
.mini-float {
    animation: floatBobbingY 4.5s ease-in-out infinite;
    will-change: transform;
}
.mini-float.mf-1 {
    animation-delay: 0s;
}
.mini-float.mf-2 {
    animation-delay: 0.5s;
}
.mini-float.mf-3 {
    animation-delay: 1.0s;
}

/* Card bên trong: chịu trách nhiệm style, hover lift + border gradient + shadow không bị xung đột */
.mini-stat {
    background: #FFFFFF;
    border-radius: 18px;
    padding: 24px 16px;
    text-align: center;
    border: 1.5px solid rgba(0, 0, 0, 0.06);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.05);
    cursor: pointer;
    transition: transform 250ms cubic-bezier(0.16, 1, 0.3, 1), 
                box-shadow 250ms ease, 
                border-color 250ms ease;
    will-change: transform, box-shadow;
    position: relative;
}

.mini-stat:hover {
    transform: translateY(-5px);
    box-shadow: 0 18px 42px rgba(232, 40, 26, 0.16), 0 4px 16px rgba(2, 132, 199, 0.12) !important;
    border-color: rgba(232, 40, 26, 0.6) !important;
}

.mini-top {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
}
.mini-top > span:first-child {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    font-weight: 700;
    transition: transform 250ms var(--sb-ease);
}
.mini-stat:hover .mini-top > span:first-child {
    transform: scale(1.12) rotate(-6deg);
}

.mini-stat.green .mini-top > span:first-child {
    background: #E8F5E9;
    color: #2D6A4F;
    border: 1.5px solid #C8E6C9;
}
.mini-stat.orange .mini-top > span:first-child {
    background: #FFEBEE;
    color: #E8281A;
    border: 1.5px solid #FFCDD2;
}
.mini-stat.amber .mini-top > span:first-child {
    background: #FFF8E1;
    color: #F6A623;
    border: 1.5px solid #FFE082;
}

.mini-pill {
    font-family: var(--font-display);
    padding: 3px 12px;
    border-radius: 8px;
    font-size: 10.5px;
    font-weight: 700;
    color: #FFF;
    letter-spacing: 0.5px;
}
.mini-stat.green .mini-pill {
    background: #2D6A4F;
}
.mini-stat.orange .mini-pill {
    background: #E8281A;
}
.mini-stat.amber .mini-pill {
    background: #F6A623;
    color: #FFF;
}

.mini-lbl {
    font-family: var(--font-display);
    font-size: 14px;
    font-weight: 700;
    color: var(--sb-dark);
}
.mini-num {
    font-family: var(--font-display);
    font-size: 27px;
    font-weight: 800;
    color: var(--sb-dark);
    margin: 5px 0 3px 0;
    line-height: 1.1;
}
.mini-stat.orange .mini-num {
    color: #E8281A;
}
.mini-foot {
    font-family: var(--font-body);
    font-size: 11px;
    color: #888;
}

/* Responsive điều chỉnh kích thước cho màn hình di động */
@media (max-width: 600px) {
    .orbit-stage {
        max-width: 360px;
        height: 330px;
    }
    .hero-circle {
        width: 190px;
        height: 190px;
        margin-left: -95px;
        margin-top: -95px;
    }
    .hero-circle .hc-num {
        font-size: 42px;
    }
    .orbit-ring, .orbit-mote-track {
        width: 250px;
        height: 250px;
        margin-left: -125px;
        margin-top: -125px;
    }
    .orbit-item.item-1 { left: -108px; top: -62px; }
    .orbit-item.item-2 { left: 108px; top: -62px; }
    .orbit-item.item-3 { left: 0px; top: 125px; }
    .fcard {
        padding: 6px 10px;
    }
    .fcnum { font-size: 11.5px; }
    .fcsm { font-size: 9px; }
    .mini-grid {
        grid-template-columns: 1fr;
    }
}
.hero-summary-bar {
    background: var(--df-sidebar); border-radius: 15px; padding: 14px 20px; color: #FFF8F0;
    display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;
}
.hero-summary-bar div[style] { color: var(--df-growth-pink) !important; }
.hero-sum-val { font-family: var(--font-display); font-size: 17px; font-weight: 700; color: #FFFFFF; }
.hero-sum-right { font-size: 12px; font-weight: 600; color: #FFF8F0; text-align: right; }

/* ---------- KPI Cards legacy fallback (đồng bộ tông sáng mới) ---------- */
.kpi-card {
    background: var(--df-surface) !important; border-radius: 18px; padding: 18px 20px; min-height: 112px; border: 1px solid var(--df-border) !important;
    display: flex; align-items: center; gap: 15px; cursor: var(--cursor-pointer); box-shadow: var(--sb-shadow);
    position: relative; overflow: hidden; transition: transform .3s var(--sb-ease), box-shadow .3s ease, border-color .25s ease;
}
.kpi-card::after { content: ""; position: absolute; left: 0; bottom: 0; height: 3px; width: 0; background: var(--df-brand-red); transition: width .35s var(--sb-ease); }
.kpi-card:hover { transform: translateY(-4px); box-shadow: 0 12px 28px rgba(41, 35, 38, 0.09); border-color: #D8C4B8 !important; }
.kpi-card:hover::after { width: 100%; }
.kpi-ico { width: 48px; height: 48px; border-radius: 13px; display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: 700; flex-shrink: 0; transition: transform .3s var(--sb-ease); }
.kpi-card:hover .kpi-ico { transform: scale(1.08); }
.kpi-card.pink .kpi-ico { background: var(--df-rose-tint); color: var(--df-brand-red); }
.kpi-card.amber .kpi-ico { background: #FDF4E3; color: var(--df-amber); }
.kpi-card.green .kpi-ico { background: #E6F4F2; color: var(--df-teal); }
.kpi-card.purple .kpi-ico { background: #F3EEF6; color: var(--df-purple); }
.kpi-label { font-size: 11px; font-weight: 600; color: var(--df-text-muted); text-transform: uppercase; letter-spacing: 0.8px; }
.kpi-val { font-family: var(--font-display); font-size: 22px; font-weight: 800; margin: 3px 0; line-height: 1.15; color: var(--df-text); font-variant-numeric: tabular-nums; }
.kpi-val.muted { font-family: var(--font-body); font-size: 13.5px; font-weight: 500; color: var(--df-text-muted) !important; }
.kpi-hint { font-size: 11px; color: var(--df-text-muted); }

/* ---------- Pulse & thẻ chiến dịch ---------- */
.pulse-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 16px 0 18px 0; }
@media (max-width: 960px) { .pulse-grid { grid-template-columns: repeat(2, 1fr); } }
.pulse-pill {
    background: var(--df-surface); border: 1px solid var(--df-border); border-left: 4px solid var(--df-brand-red); border-radius: 14px; padding: 14px 16px;
    box-shadow: var(--sb-shadow); cursor: var(--cursor-pointer); transition: transform .3s var(--sb-ease), box-shadow .3s ease;
}
.pulse-pill:nth-child(2) { border-left-color: var(--df-amber); }
.pulse-pill:nth-child(3) { border-left-color: var(--df-teal); }
.pulse-pill:nth-child(4) { border-left-color: var(--df-purple); }
.pulse-pill:hover { transform: translateY(-4px); box-shadow: 0 10px 26px rgba(41, 35, 38, 0.09); }
.pulse-top { font-size: 11.5px; font-weight: 600; color: var(--df-text-muted); display: flex; justify-content: space-between; align-items: center; }
.pulse-val { font-family: var(--font-display); font-size: 20px; font-weight: 800; color: var(--df-text); margin: 5px 0 2px 0; font-variant-numeric: tabular-nums; }
.pulse-sub { font-size: 11px; color: var(--df-text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.camp-health-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 8px; }
@media (max-width: 1000px) { .camp-health-grid { grid-template-columns: 1fr; } }
.camp-health-card {
    position: relative; background: var(--df-surface); border: 1px solid var(--df-border); border-radius: 16px; padding: 0 0 15px 0; overflow: hidden;
    box-shadow: var(--sb-shadow); transition: transform .3s var(--sb-ease), box-shadow .3s ease;
}
.camp-health-card::before {
    content: ""; display: block; height: 58px; margin-bottom: 12px;
    background: linear-gradient(135deg, var(--df-surface-sub) 0%, #F7DFD5 100%);
    border-bottom: 1px solid var(--df-border);
}
.camp-health-card:hover { transform: translateY(-4px); box-shadow: 0 12px 30px rgba(41, 35, 38, 0.09); }
.camp-h-head, .camp-h-metrics, .camp-bar-track { margin-left: 16px !important; margin-right: 16px !important; }
.camp-h-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; margin-bottom: 8px; }
.camp-h-head .badge { position: absolute; top: 13px; left: 13px; background: var(--df-brand-red); color: #FFF; }
.camp-h-head .badge.ok { background: var(--df-green); color: #FFF; }
.camp-h-head .badge.warn { background: var(--df-amber); color: #FFF; }
.camp-h-name { font-family: var(--font-display); font-size: 15.5px; font-weight: 700; color: var(--df-text); line-height: 1.25; }
.camp-h-chan { font-size: 10.5px; color: var(--df-teal); font-weight: 600; text-transform: uppercase; letter-spacing: 0.9px; margin-top: 3px; }
.camp-h-metrics { display: flex; justify-content: space-between; font-size: 11.8px; color: var(--df-text-muted); margin: 8px 0 8px 0; padding-top: 10px; border-top: 1px dashed var(--df-border); }
.camp-bar-track { height: 7px; background: var(--df-surface-sub); border-radius: 4px; overflow: hidden; }
.camp-bar-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg, var(--df-brand-red), var(--df-teal)); transition: width .5s ease; }

/* ---------- Thanh tỷ trọng kênh ---------- */
.ch-row { margin-bottom: 11px; padding: 6px 10px; border-radius: 10px; transition: background .25s ease, transform .25s ease; }
.ch-row:hover { background: var(--df-surface-sub); transform: translateX(4px); }
.ch-label { font-family: var(--font-display); display: flex; justify-content: space-between; font-size: 13px; font-weight: 700; color: var(--df-text); margin-bottom: 6px; }
.ch-bar { height: 8px; background: var(--df-surface-sub); border-radius: 4px; overflow: hidden; }
.ch-fill { height: 100%; border-radius: 4px; transition: width .5s ease; }

/* ---------- Stepper 6 bước ---------- */
.stepper { display: flex; align-items: center; background: var(--df-surface); border: 1px solid var(--df-border); border-radius: 16px; padding: 20px 24px; margin: 6px 0 22px 0; overflow-x: auto; box-shadow: var(--sb-shadow); }
.step { display: flex; flex-direction: column; align-items: center; min-width: 88px; font-size: 12px; font-weight: 500; color: var(--df-text-muted); text-align: center; }
.step-badge { width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-family: var(--font-display); font-weight: 800; font-size: 14.5px; margin-bottom: 7px; background: var(--df-surface-sub); border: 1.5px solid var(--df-border); color: var(--df-brand-red); transition: transform .25s ease; }
.step-badge:hover { transform: scale(1.08); }
.step-badge.done { color: #FFF; border: none; }
.step-line { flex: 1; min-width: 16px; height: 2.5px; background: var(--df-border); margin: 0 6px 20px 6px; border-radius: 4px; }
.step-line.done { background: linear-gradient(90deg, var(--df-brand-red), var(--df-teal)); }

/* ---------- Banner kết quả ---------- */
.result-banner {
    border-radius: 15px; padding: 15px 20px; margin-bottom: 18px; border: 1px solid var(--df-border); border-left: 5px solid;
    display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;
    box-shadow: var(--sb-shadow); transition: transform .3s var(--sb-ease);
}
.result-banner:hover { transform: translateY(-2px); }
.result-banner.pass { background: #E6F5EE; border-color: var(--df-green); color: #195E42; }
.result-banner.fail { background: var(--df-rose-tint); border-color: var(--df-brand-red); color: var(--df-wine); }
.result-banner b { font-family: var(--font-display); font-size: 16.5px; font-weight: 700; }
.result-banner small { display: block; font-size: 12.5px; margin-top: 3px; font-weight: 400; }

/* ---------- Kiểm tra sơ bộ dữ liệu trước khi làm sạch ---------- */
.precheck-box {
    background: rgba(255, 252, 252, 0.88); border: 1px solid var(--df-border); border-left: 5px solid var(--df-brand-red);
    border-radius: 14px; padding: 14px 18px; margin: 12px 0 14px 0; box-shadow: var(--sb-shadow);
}
.precheck-box-title { font-family: var(--font-display); font-size: 14.5px; font-weight: 800; color: var(--df-text); margin-bottom: 8px; }
.precheck-row { display: flex; align-items: flex-start; gap: 10px; padding: 7px 0; border-bottom: 1px dashed var(--df-border); font-size: 13px; color: var(--df-text); line-height: 1.5; }
.precheck-row:last-child { border-bottom: none; }
.precheck-row small { display: block; color: var(--df-text-muted); font-size: 11.8px; margin-top: 1px; }
.precheck-tag { font-family: var(--font-display); font-size: 10.5px; font-weight: 800; padding: 2px 9px; border-radius: 999px; white-space: nowrap; flex-shrink: 0; margin-top: 1px; }
.precheck-tag.high { background: var(--df-rose-tint); color: var(--df-brand-red); border: 1px solid rgba(194, 31, 32, 0.28); }
.precheck-tag.med { background: #FDF4E3; color: #A66E14; border: 1px solid rgba(214, 154, 59, 0.35); }
.precheck-tag.info { background: #EAF1F8; color: var(--df-blue); border: 1px solid rgba(82, 119, 166, 0.30); }
.pill-count { font-family: var(--font-display); background: #FFF; font-weight: 700; padding: 5px 14px; border-radius: 50px; font-size: 12.5px; box-shadow: 0 2px 8px rgba(41,35,38,0.06); }

/* ---------- Nút bấm chuẩn Enterprise SaaS (Sắc nét, Hover mượt, Rõ trạng thái) ---------- */
.stButton > button, 
.stDownloadButton > button, 
button[kind="secondary"], 
[data-testid="baseButton-secondary"],
[data-testid="stPopover"] button {
    position: relative !important;
    overflow: hidden !important;
    border-radius: 999px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 9px 20px !important;
    border: 1.5px solid var(--df-border) !important;
    background: var(--df-surface) !important;
    color: var(--df-text) !important;
    box-shadow: 0 2px 6px rgba(41, 35, 38, 0.04) !important;
    transition: transform 0.28s cubic-bezier(0.16, 1, 0.3, 1),
                box-shadow 0.28s ease,
                background-color 0.22s ease,
                border-color 0.22s ease,
                color 0.22s ease !important;
    cursor: var(--cursor-pointer) !important;
}

.stButton > button:hover, 
.stDownloadButton > button:hover,
button[kind="secondary"]:hover,
[data-testid="baseButton-secondary"]:hover,
[data-testid="stPopover"] button:hover {
    background: var(--df-rose-tint) !important;
    border-color: var(--df-brand-red) !important;
    color: var(--df-brand-hover) !important;
    transform: translateY(-1.5px) !important;
    box-shadow: 0 6px 18px rgba(194, 31, 32, 0.14) !important;
}

.stButton > button:active, 
.stDownloadButton > button:active,
button[kind="secondary"]:active,
[data-testid="baseButton-secondary"]:active,
[data-testid="stPopover"] button:active {
    transform: translateY(0px) scale(0.985) !important;
    box-shadow: 0 2px 8px rgba(140, 46, 46, 0.14) !important;
    transition-duration: 0.1s !important;
}

/* Nút hành động chính (#C21F20, hover #8C2E2E) */
.stButton > button[kind="primary"], 
.stDownloadButton > button[kind="primary"], 
button[kind="primary"], 
[data-testid="baseButton-primary"],
[data-testid="stFormSubmitButton"] > button {
    position: relative !important;
    overflow: hidden !important;
    background: var(--df-brand-red) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 999px !important;
    padding: 10px 24px !important;
    font-weight: 700 !important;
    box-shadow: 0 6px 18px rgba(194, 31, 32, 0.26) !important;
    transition: transform 0.28s cubic-bezier(0.16, 1, 0.3, 1),
                box-shadow 0.28s ease,
                background-color 0.22s ease !important;
    cursor: var(--cursor-pointer) !important;
}

.stButton > button[kind="primary"]:hover, 
.stDownloadButton > button[kind="primary"]:hover, 
button[kind="primary"]:hover,
[data-testid="baseButton-primary"]:hover,
[data-testid="stFormSubmitButton"] > button:hover {
    background: var(--df-brand-hover) !important;
    color: #FFFFFF !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 24px rgba(140, 46, 46, 0.34) !important;
}

.stButton > button[kind="primary"]:active, 
.stDownloadButton > button[kind="primary"]:active, 
button[kind="primary"]:active,
[data-testid="baseButton-primary"]:active,
[data-testid="stFormSubmitButton"] > button:active {
    background: var(--df-wine) !important;
    transform: translateY(0px) scale(0.985) !important;
    box-shadow: 0 4px 12px rgba(124, 31, 39, 0.28) !important;
    transition-duration: 0.1s !important;
}

.stButton > button:disabled,
.stDownloadButton > button:disabled,
button:disabled {
    opacity: 0.52 !important;
    transform: none !important;
    box-shadow: none !important;
    cursor: not-allowed !important;
}

[class*="st-key-btn_toggle_theme"] button {
    padding: 8px 11px !important;
    font-size: 12.5px !important;
    white-space: nowrap !important;
}
[class*="st-key-card_hero_ai"] [data-testid="stFormSubmitButton"] > button {
    padding: 9px 10px !important;
    font-size: 12.5px !important;
    white-space: nowrap !important;
}
[class*="st-key-card_ov_insights"] .stButton > button {
    padding: 8px 10px !important;
    font-size: 12px !important;
    white-space: nowrap !important;
}

/* ---------- Nút điều hướng bên trong SIDEBAR ĐỎ RƯỢU VANG (ghi đè sạch style nút trắng) ---------- */
section[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    justify-content: flex-start !important;
    text-align: left !important;
    border-radius: 12px !important;
    padding: 9px 13px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    background: transparent !important;
    border: 1px solid transparent !important;
    color: #F7EAE6 !important;
    box-shadow: none !important;
    margin: 0 !important;
}
section[data-testid="stSidebar"] .stButton > button > div {
    justify-content: flex-start !important;
    width: 100% !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--df-brand-hover) !important;
    border-color: rgba(255, 248, 240, 0.16) !important;
    color: #FFFFFF !important;
    transform: translateX(3px) !important;
    box-shadow: 0 4px 12px rgba(38, 8, 14, 0.22) !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #C21F20 0%, #A91B1C 100%) !important;
    border: 1px solid rgba(255, 248, 240, 0.18) !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    box-shadow: 0 6px 18px rgba(194, 31, 32, 0.36) !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #C21F20 0%, #8C2E2E 100%) !important;
    transform: translateX(2px) !important;
}

/* ---------- Metric, bảng, expander, input, tab ---------- */
[data-testid="stMetric"] {
    background: var(--df-surface) !important; border: 1px solid var(--df-border) !important; border-top: 3px solid var(--df-brand-red) !important;
    border-radius: 14px !important; padding: 14px 16px !important; box-shadow: var(--sb-shadow);
    transition: transform .25s var(--sb-ease), box-shadow .25s ease !important;
}
[data-testid="stMetric"]:hover { transform: translateY(-3px); box-shadow: 0 10px 26px rgba(41, 35, 38, 0.08); }
[data-testid="stMetricLabel"] p { font-size: 11px !important; font-weight: 600 !important; color: var(--df-text-muted) !important; text-transform: uppercase; letter-spacing: 0.7px; }
[data-testid="stMetricValue"] { font-family: var(--font-display) !important; font-size: 22px !important; font-weight: 800 !important; color: var(--df-text) !important; font-variant-numeric: tabular-nums; }

[data-testid="stDataFrame"] { border-radius: 14px !important; overflow: hidden; border: 1px solid var(--df-border) !important; box-shadow: var(--sb-shadow); }
[data-testid="stExpander"] details { border-radius: 14px !important; border: 1px solid var(--df-border) !important; background: var(--df-surface) !important; transition: border-color .25s ease, box-shadow .25s ease; }
[data-testid="stExpander"] details:hover { border-color: var(--df-brand-red) !important; box-shadow: 0 8px 22px rgba(194, 31, 32, 0.08); }
[data-testid="stExpander"] summary p { font-family: var(--font-display); font-weight: 700 !important; font-size: 14.5px !important; color: var(--df-text); }
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input, [data-testid="stTextArea"] textarea, [data-baseweb="select"] > div {
    border-radius: 10px !important; border-color: var(--df-border) !important; background: var(--df-surface-sub) !important; color: var(--df-text) !important;
}
[data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus { border-color: var(--df-brand-red) !important; background: #FFFFFF !important; box-shadow: 0 0 0 3px rgba(194, 31, 32, 0.12) !important; }
[data-testid="stAlert"] { border-radius: 12px !important; }
.stTabs [data-baseweb="tab-list"] { gap: 6px; background: transparent; padding: 4px 0; border: none; flex-wrap: wrap; }
.stTabs [data-baseweb="tab"] {
    border-radius: 999px !important;
    font-weight: 600 !important;
    padding: 8px 18px !important;
    border: 1px solid var(--df-border) !important;
    background: var(--df-surface) !important;
    color: var(--df-text) !important;
    transition: transform 0.25s ease, box-shadow 0.25s ease, background-color 0.22s ease, border-color 0.22s ease, color 0.22s ease !important;
    cursor: var(--cursor-pointer) !important;
}
.stTabs [data-baseweb="tab"]:hover {
    border-color: var(--df-brand-red) !important;
    color: var(--df-brand-hover) !important;
    background: var(--df-rose-tint) !important;
    transform: translateY(-1px) !important;
}
.stTabs [aria-selected="true"] {
    background: var(--df-brand-red) !important;
    border-color: var(--df-brand-red) !important;
    color: #FFF !important;
    box-shadow: 0 6px 16px rgba(194, 31, 32, 0.26) !important;
}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none !important; }
[data-testid="stChatMessage"] { border-radius: 14px; background: var(--df-surface-sub); }

/* ---------- Bối cảnh doanh nghiệp (Business Context Card đồng bộ #EADDD5 & #258B86) ---------- */
[class*="st-key-card_biz_context"] {
    background: var(--df-surface) !important;
    border: 1.5px solid var(--df-border) !important;
    border-radius: 18px !important;
    padding: 22px 24px !important;
    margin-top: 16px !important;
    margin-bottom: 12px !important;
    box-shadow: var(--sb-shadow) !important;
}
[class*="st-key-card_biz_context"] input,
[class*="st-key-card_biz_context"] textarea {
    border-radius: 10px !important;
    border: 1.5px solid var(--df-border) !important;
    background: var(--df-surface-sub) !important;
    font-size: 13.5px !important;
}
[class*="st-key-card_biz_context"] input:focus,
[class*="st-key-card_biz_context"] textarea:focus {
    border-color: var(--df-teal) !important;
    background: #FFFFFF !important;
    box-shadow: 0 0 0 3px rgba(37, 139, 134, 0.14) !important;
}
.biz-head { display: flex; align-items: center; gap: 14px; margin-bottom: 14px; }
.biz-icon {
    width: 42px; height: 42px; border-radius: 10px;
    background: #E6F4F2; border: 1px solid #BCE0DC;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; color: var(--df-teal); flex-shrink: 0;
}
.biz-title { font-family: var(--font-display); font-size: 17px; font-weight: 700; color: var(--df-text); line-height: 1.25; }
.biz-sub { font-size: 13px; color: var(--df-text-muted); margin-top: 3px; }
[class*="st-key-card_biz_ai_bar"] {
    background: var(--df-ai-bg) !important;
    border: 1.5px solid #F0D2C2 !important;
    border-radius: 18px !important;
    padding: 16px 22px !important;
    margin-bottom: 18px !important;
    box-shadow: var(--sb-shadow) !important;
}
[class*="st-key-card_biz_ai_bar"] button {
    background: #FFFFFF !important;
    color: var(--df-brand-red) !important;
    border: 1.5px solid var(--df-brand-red) !important;
    border-radius: 999px !important;
    font-weight: 700 !important;
    font-size: 13.5px !important;
    padding: 8px 18px !important;
    transition: all 0.22s ease !important;
}
[class*="st-key-card_biz_ai_bar"] button:hover {
    background: var(--df-brand-red) !important;
    border-color: var(--df-brand-red) !important;
    color: #FFFFFF !important;
    transform: translateY(-1.5px) !important;
    box-shadow: 0 6px 16px rgba(194, 31, 32, 0.22) !important;
}
[class*="st-key-card_biz_ai_feedback"] {
    background: #FFFFFF !important;
    border: 1.5px solid var(--df-border) !important;
    border-left: 5px solid var(--df-brand-red) !important;
    border-radius: 16px !important;
    padding: 20px 24px !important;
    margin-bottom: 20px !important;
    box-shadow: var(--sb-shadow) !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown(f"<style>{ENTERPRISE_NARRATIVE_CSS}</style>", unsafe_allow_html=True)

# Ghi đè khối thuyết minh doanh nghiệp đồng bộ bảng màu Đỏ Rượu Vang & Kem Sáng
st.markdown("""
<style>
.ent-wrap { font-family: var(--font-body) !important; }
.ent-card { background: var(--df-surface) !important; backdrop-filter: none; border: 1px solid var(--df-border) !important; border-radius: 18px !important; box-shadow: var(--sb-shadow) !important; }
.ent-card:hover { border-color: #D8C4B8 !important; box-shadow: 0 12px 30px rgba(41,35,38,0.09) !important; transform: translateY(-3px) !important; }
.ent-card.brief { border-left: 5px solid var(--df-brand-red) !important; }
.ent-card.gov { border-left: 5px solid var(--df-teal) !important; }
.ent-card.control { border-left: 5px solid var(--df-amber) !important; }
.ent-head { border-bottom: 1px dashed var(--df-border) !important; }
.ent-title { font-family: var(--font-display); font-size: 16px !important; font-weight: 800 !important; text-transform: none !important; color: var(--df-text) !important; }
.ent-sub { color: var(--df-text-muted) !important; }
.ent-list { color: var(--df-text) !important; }
.ent-mono { color: var(--df-wine) !important; background: var(--df-surface-sub) !important; border: 1px solid var(--df-border) !important; border-radius: 7px !important; }
.ent-commentary { background: var(--df-surface-sub) !important; border: 1px solid var(--df-border) !important; border-left: 4px solid var(--df-amber) !important; border-radius: 13px !important; }
.ent-commentary:hover { box-shadow: 0 8px 22px rgba(214,154,59,0.16) !important; }
.ent-commentary-title { font-family: var(--font-display); font-size: 14px !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.4px !important; color: var(--df-brand-red) !important; }
.ent-mcard { border-radius: 16px !important; border: 1px solid var(--df-border) !important; box-shadow: var(--sb-shadow); background: var(--df-surface) !important; }
.ent-mcard.pos { border-top: 4px solid var(--df-green) !important; }
.ent-mcard.warn { border-top: 4px solid var(--df-amber) !important; }
.ent-mcard.neg { border-top: 4px solid var(--df-brand-red) !important; }
.ent-mcard-h { font-family: var(--font-display); font-size: 14.5px !important; font-weight: 700 !important; color: var(--df-text) !important; }
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<style>
:root {{
    --cursor-default: url("data:image/png;base64,{_CURSOR_SWORD_B64}") 2 2, auto;
    --cursor-pointer: url("data:image/png;base64,{_CURSOR_SWORD_HOVER_B64}") 2 2, pointer;
}}
html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stSidebar"],
[data-testid="stMarkdownContainer"],
input, textarea {{
    cursor: var(--cursor-default) !important;
}}
a, a *,
button:not(:disabled), button:not(:disabled) *,
[role="button"], [role="button"] *,
label, label *,
summary, summary *,
select,
[data-testid="stRadioOption"], [data-testid="stRadioOption"] *,
[data-baseweb="tab"], [data-baseweb="tab"] *,
.fcard, .fcard *,
.mini-stat, .mini-stat *,
.kpi-card, .kpi-card *,
.kpi-card-ent, .kpi-card-ent *,
.pulse-pill, .pulse-pill *,
.camp-health-card, .profile-chip, .bell-wrap, .top-search, .sb-tsoc i {{
    cursor: var(--cursor-pointer) !important;
}}
button:disabled, button:disabled * {{
    cursor: not-allowed !important;
}}
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# TIỆN ÍCH GIAO DIỆN
# ==============================================================================
def html(markup: str) -> None:
    """Render HTML an toàn (notranslate): bỏ thụt lề & dòng trống để Markdown không biến thành code block."""
    clean = "\n".join(line.strip() for line in markup.splitlines() if line.strip())
    st.markdown(f'<div translate="no" class="notranslate">{clean}</div>', unsafe_allow_html=True)


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
        font=dict(family="Inter, Plus Jakarta Sans, sans-serif", color="#292326", size=12),
        margin=dict(l=10, r=10, t=12, b=10),
        height=height,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=None),
        hoverlabel=dict(bgcolor="#FFFFFF", font_size=12, font_color="#292326", bordercolor="#C21F20"),
    )
    fig.update_xaxes(showgrid=False, title=None, tickfont=dict(color="#766A68"))
    fig.update_yaxes(gridcolor="#EADDD5", title=None, tickfont=dict(color="#766A68"))
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
    "QUOTA_WARNING": "CẢNH BÁO QUOTA",
    "NEEDS_APPROVAL": "CHỜ PHÊ DUYỆT",
    "FAILED": "LỖI CHẶN",
}


def vi_status(code: str, quality_summary: dict = None) -> str:
    if str(code) == "QUOTA_WARNING" and isinstance(quality_summary, dict) and quality_summary.get("Quota_Status_Text"):
        return str(quality_summary["Quota_Status_Text"])
    return VI_STATUS_MAP.get(str(code), str(code))


# ==============================================================================
# SESSION STATE & LOGIC ĐIỀU PHỐI (giữ nguyên backend)
# ==============================================================================
DEFAULT_CHAT_GREETING = {
    "role": "assistant",
    "content": (
        "Xin chào! Tôi là **Trợ lý AI Data Forge** (bộ não ChatGPT + **Can thiệp Dữ liệu Trực tiếp**). "
        "Bạn có thể nhắn lệnh để tôi thực thi thẳng vào dữ liệu và báo cáo:\n"
        "- **Làm sạch & xử lý tự động:** `\"Làm sạch và chạy 6 bước ngay\"`, `\"Nạp dữ liệu lộn xộn và làm sạch\"`\n"
        "- **Can thiệp dữ liệu chuyên sâu:** `\"Xóa các dòng trùng lặp\"`, `\"Loại bỏ các dòng lỗi\"`, `\"Điền kênh trống bằng Shopee\"`, `\"Chỉ giữ lại kênh Shopee\"`\n"
        "- **Sửa/Xóa từng đơn hàng:** `\"Sửa đơn ORD-2001 giá trị 5 triệu\"`, `\"Đổi kênh đơn ORD-1002 thành TikTok\"`, `\"Xóa đơn ORD-2002\"`\n"
        "- **Phê duyệt HITL, Quota & Kiểm toán:** `\"Duyệt tất cả ngoại lệ và chạy kiểm toán\"`, `\"Duyệt đơn ORD-2003\"`, `\"Cắt ngọn Quota\"`, `\"Đổi Return Window thành 20 ngày\"`\n"
        "- Hoặc hỏi bất kỳ câu hỏi phân tích KPI, kiến thức đa lĩnh vực nào!"
    ),
}

DEFAULTS = {
    "nav_page": PAGES[0],
    "show_ai_hub": False,
    "ui_theme": "light",
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
    "pre_clean_scan": None,
    "return_window": 30,
    "max_row_limit": MAX_ROW_LIMIT,
    "quota_policy": "WARN_AND_QUARANTINE",
    "reconciliation_table": None,
    "cleaned_excel": None,
    "uploaded_file_id": None,
    "pending_toast": None,
    "visitor_id": None,
    "user_name": ADMIN_NAME,
    "user_role": "Admin account",
    "custom_openai_key": "",
    "custom_gemini_key": "",
    "chat_history": [dict(DEFAULT_CHAT_GREETING)],
    "biz_industry": "",
    "biz_extra_info": "",
    "biz_questions": "",
    "biz_ai_feedback": None,
}
for _k, _v in DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = list(_v) if isinstance(_v, list) else _v

if st.session_state.nav_page not in PAGES:
    st.session_state.nav_page = PAGES[0]

if st.session_state.visitor_id is None:
    st.session_state.visitor_id = str(uuid.uuid4())[:8]

# Tự động nhận tên & vai trò nếu truy cập qua URL (?user=...&role=...)
try:
    _qp = st.query_params
    _qp_user = str(_qp.get("user", "")).strip()
    _qp_role = str(_qp.get("role", "")).strip()
    if _qp_user:
        st.session_state.user_name = _qp_user[:50]
    if _qp_role:
        st.session_state.user_role = _qp_role[:40]
except Exception:
    pass


def _toggle_ui_theme() -> None:
    st.session_state.ui_theme = "dark" if st.session_state.get("ui_theme", "light") == "light" else "light"


def _on_top_nav_change() -> None:
    st.session_state.show_ai_hub = False


def _sb_nav_go(target_page: str, open_ai_hub: bool = False) -> None:
    st.session_state.show_ai_hub = open_ai_hub
    st.session_state.nav_page = target_page


if st.session_state.get("ui_theme") == "dark":
    st.markdown("""
    <style>
    :root {
        --df-bg: #1F191C;
        --df-surface: #2B2226;
        --df-surface-sub: #362B30;
        --df-ai-bg: #352726;
        --df-border: #4A3940;
        --df-text: #F7ECE8;
        --df-text-muted: #CBB7B2;
        --sb-cream: #1F191C;
        --sb-cream2: #2B2226;
        --sb-light: #362B30;
        --sb-dark: #F7ECE8;
    }
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background:
            radial-gradient(ellipse 56% 48% at 8% 12%, rgba(142, 30, 62, 0.44) 0%, rgba(107, 23, 46, 0.20) 45%, transparent 74%),
            radial-gradient(ellipse 50% 46% at 92% 16%, rgba(194, 31, 58, 0.24) 0%, transparent 70%),
            radial-gradient(ellipse 54% 48% at 24% 88%, rgba(107, 23, 46, 0.38) 0%, transparent 72%),
            radial-gradient(ellipse 46% 44% at 88% 86%, rgba(154, 36, 68, 0.28) 0%, transparent 72%),
            linear-gradient(135deg, #1E0D14 0%, #2C121D 52%, #190A11 100%) !important;
        background-attachment: fixed !important;
        color: #F7ECE8 !important;
    }
    .kpi-card-ent, .df-insight-item, .df-ai-bubble, .df-ai-reply-chip, [class*="st-key-card"] {
        background: rgba(46, 23, 33, 0.84) !important;
        backdrop-filter: blur(14px);
        border-color: rgba(233, 160, 150, 0.20) !important;
        color: #F7ECE8 !important;
    }
    [class*="st-key-card_hero_banner"] {
        background: linear-gradient(115deg, #3D1A22 0%, #5A1E28 48%, #7C1F27 100%) !important;
    }
    .df-banner-title, .df-banner-eyebrow, .df-banner-sub { color: #FFF8F0 !important; }
    </style>
    """, unsafe_allow_html=True)


def get_initials(name: str) -> str:
    parts = [p for p in str(name or "").strip().split() if p]
    if not parts:
        return ADMIN_INITIALS
    if len(parts) == 1:
        return parts[0][:2].upper()
    return f"{parts[0][0]}{parts[-1][0]}".upper()


@st.cache_resource
def get_visitor_registry() -> dict:
    """Lưu danh sách người đang truy cập theo thời gian thực dùng chung giữa mọi phiên."""
    return {}


def sync_current_visitor() -> list:
    """Cập nhật thông tin người đang truy cập hiện tại và loại bỏ phiên cũ > 30 phút."""
    reg = get_visitor_registry()
    now = time.time()
    vid = st.session_state.visitor_id
    u_name = str(st.session_state.user_name or ADMIN_NAME).strip() or ADMIN_NAME
    u_role = str(st.session_state.user_role or "Admin account").strip() or "Admin account"
    reg[vid] = {
        "visitor_id": vid,
        "name": u_name,
        "role": u_role,
        "initials": get_initials(u_name),
        "page": st.session_state.nav_page,
        "last_seen_ts": now,
        "last_seen_str": datetime.datetime.now().strftime("%H:%M:%S"),
    }
    stale = [k for k, v in reg.items() if (now - float(v.get("last_seen_ts", 0))) > 1800]
    for k in stale:
        reg.pop(k, None)
    return sorted(reg.values(), key=lambda x: float(x.get("last_seen_ts", 0)), reverse=True)


def reset_pipeline() -> None:
    """Xóa toàn bộ kết quả cũ khi nạp nguồn dữ liệu mới, tránh hiển thị số liệu lỗi thời."""
    for key in [
        "normalized_data", "quality_summary", "engine", "process_result",
        "verification_result", "reconciliation_table", "cleaned_excel", "cleaning_error_detail",
        "pre_clean_scan",
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
    st.session_state.quota_policy = "WARN_AND_QUARANTINE"


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


# ==============================================================================
# KIỂM TRA SƠ BỘ DỮ LIỆU GỐC TRƯỚC KHI LÀM SẠCH (READ-ONLY, KHÔNG SỬA DỮ LIỆU)
# ==============================================================================
_PRECHECK_ERROR_LABELS = {
    "DUPLICATE_ORDER_ID": "Trùng mã đơn hàng",
    "DUPLICATE_ROW": "Dòng dữ liệu trùng lặp",
    "MISSING_ORDER_ID": "Thiếu mã đơn hàng",
    "EXCEPTION_INVALID": "Giá trị tiền tệ không hợp lệ",
    "EXCEPTION_MISSING": "Thiếu giá trị bắt buộc",
    "EXCEPTION_NEGATIVE": "Giá trị tiền bị âm",
    "EXCEPTION_COUNT_MISMATCH": "Campaign_Count không khớp Campaign_List",
    "EXCEPTION_INVALID_DATE": "Ngày tháng không hợp lệ",
    "QUOTA_EXCEEDED_QUARANTINE": "Vượt hạn mức số dòng (Quota)",
}
_PRECHECK_FORMAT_LABELS = {
    "CURRENCY_NORMALIZED": "Tiền tệ sai định dạng (VNĐ, triệu, dấu chấm...)",
    "DATE_NORMALIZED": "Ngày tháng chưa chuẩn",
    "COLUMN_NORMALIZED": "Tên cột có khoảng trắng thừa",
    "TRIM_WHITESPACE": "Giá trị chứa khoảng trắng thừa",
}
_PRECHECK_SEV_LABELS = {"HIGH": "Cao", "MEDIUM": "Trung bình", "LOW": "Thấp"}


def _precheck_err_label(code: str) -> str:
    code = str(code or "")
    return _PRECHECK_ERROR_LABELS.get(code, code.replace("_", " ").title() or "Lỗi dữ liệu")


def scan_raw_data_issues(raw_tabs: dict, class_info=None, max_row_limit: int = MAX_ROW_LIMIT) -> dict:
    """Quét lỗi trên BẢN SAO dữ liệu gốc; không ghi bất cứ kết quả nào vào session_state."""
    result = {
        "critical_rows": [], "format_rows": [], "schema_rows": [], "info_rows": [],
        "grouped": [], "estimated_score": None, "total_rows": 0, "total_tabs": 0,
        "has_problems": False, "has_blocking_error": False, "total_problem_count": 0,
        "scan_error": None, "_toasted": False,
    }
    if not raw_tabs:
        return result
    copied = {k: (v.copy(deep=True) if isinstance(v, pd.DataFrame) else v) for k, v in raw_tabs.items()}
    result["total_tabs"] = len(copied)
    result["total_rows"] = int(sum(len(v) for v in copied.values() if isinstance(v, pd.DataFrame)))

    # Cảnh báo cấu trúc: tab rỗng, thiếu tab tùy chọn
    tab_names_low = [str(t).lower() for t in copied.keys()]
    for t_name, df_tab in copied.items():
        if not isinstance(df_tab, pd.DataFrame) or df_tab.empty or len(df_tab.columns) == 0:
            result["schema_rows"].append({
                "Mức độ": "Trung bình", "Tab": t_name, "Loại vấn đề": "Tab không có dữ liệu",
                "Mô tả chi tiết": f"Tab '{t_name}' rỗng hoặc không có cột nào.",
                "Hướng xử lý khi Làm sạch": "Bỏ qua tab này, không ảnh hưởng các tab khác",
            })
    if not any(("return" in n) or ("hoan" in n) or ("hoàn" in n) for n in tab_names_low):
        result["info_rows"].append({
            "Mức độ": "Thông tin", "Tab": "—", "Loại vấn đề": "Chưa có tab Hoàn trả (Returns)",
            "Mô tả chi tiết": "Đối soát hoàn trả sẽ được đánh dấu N/A, không tự bịa dữ liệu.",
            "Hướng xử lý khi Làm sạch": "Có thể bổ sung tab Returns để đối soát đầy đủ",
        })
    if not any(("cost" in n) or ("chi phi" in n) or ("chi phí" in n) for n in tab_names_low):
        result["info_rows"].append({
            "Mức độ": "Thông tin", "Tab": "—", "Loại vấn đề": "Chưa có tab Chi phí (Campaign_Costs)",
            "Mô tả chi tiết": "Chi phí ABC & Net Contribution sẽ không được tính, không tự gán chi phí = 0.",
            "Hướng xử lý khi Làm sạch": "Có thể bổ sung tab Campaign_Costs",
        })

    try:
        cleaner = DataCleaner(
            copied,
            tab_classification=class_info,
            max_row_limit=max_row_limit,
            quota_policy="WARN_AND_QUARANTINE",
        )
        can_proc, _norm, q_sum, errs, excs = cleaner.clean_and_normalize()
    except Exception as exc:
        result["scan_error"] = f"{type(exc).__name__}: {exc}"
        result["critical_rows"].append({
            "Mức độ": "Cao", "Tab": "—", "Dòng": "—", "Mã đơn": "—", "Cột / Trường": "—",
            "Loại vấn đề": "Không đọc được cấu trúc dữ liệu", "Giá trị gốc": "—",
            "Mô tả chi tiết": result["scan_error"],
            "Hướng xử lý khi Làm sạch": "Kiểm tra lại file/bảng tính nguồn trước khi làm sạch",
        })
        result["has_blocking_error"] = True
        result["has_problems"] = True
        result["total_problem_count"] = 1
        result["grouped"].append(("high", "Không đọc được cấu trúc dữ liệu", 1, result["scan_error"][:160]))
        return result

    q_sum = q_sum or {}
    result["estimated_score"] = q_sum.get("Data_Quality_Score")

    seen = set()
    for e in errs or []:
        code = e.get("Error_Type", "")
        seen.add((str(e.get("Order_ID", "")), str(code)))
        result["critical_rows"].append({
            "Mức độ": _PRECHECK_SEV_LABELS.get(str(e.get("Severity", "")).upper(), str(e.get("Severity", "—"))),
            "Tab": e.get("Tab", "—"), "Dòng": e.get("Row_Index", "—"), "Mã đơn": e.get("Order_ID", "—"),
            "Cột / Trường": e.get("Field", "—"), "Loại vấn đề": _precheck_err_label(code),
            "Giá trị gốc": str(e.get("Raw_Value", "")), "Mô tả chi tiết": e.get("Description", ""),
            "Hướng xử lý khi Làm sạch": e.get("Action_Taken", "Đưa vào danh sách ngoại lệ"),
            "_code": code,
        })
    for x in excs or []:
        code = x.get("Error_Type", "")
        key = (str(x.get("Order_ID", "")), str(code))
        if key in seen:
            continue
        seen.add(key)
        result["critical_rows"].append({
            "Mức độ": _PRECHECK_SEV_LABELS.get(str(x.get("Severity", "")).upper(), str(x.get("Severity", "—"))),
            "Tab": "—", "Dòng": "—", "Mã đơn": x.get("Order_ID", "—"), "Cột / Trường": "—",
            "Loại vấn đề": _precheck_err_label(code), "Giá trị gốc": str(x.get("Raw_Value", "")),
            "Mô tả chi tiết": x.get("Error_Description", ""),
            "Hướng xử lý khi Làm sạch": x.get("Proposed_Action", "Chờ phê duyệt HITL"),
            "_code": code,
        })
    if q_sum.get("Quota_Exceeded"):
        result["critical_rows"].append({
            "Mức độ": "Cao", "Tab": "—", "Dòng": "—", "Mã đơn": "—", "Cột / Trường": "—",
            "Loại vấn đề": "Vượt hạn mức số dòng (Quota)", "Giá trị gốc": f"{q_sum.get('Raw_Transactions_Count', 0):,} dòng",
            "Mô tả chi tiết": str(q_sum.get("Quota_Status_Text", "Dữ liệu vượt ngưỡng MAX_ROW_LIMIT")),
            "Hướng xử lý khi Làm sạch": "Dòng dư sẽ được cách ly (Quarantine) chờ quyết định",
            "_code": "QUOTA_EXCEEDED_QUARANTINE",
        })
    if not can_proc:
        result["has_blocking_error"] = True

    for a in getattr(cleaner, "audit_log", []) or []:
        method = str(a.get("Method", ""))
        raw_v, clean_v = str(a.get("Raw_Value", "")), str(a.get("Cleaned_Value", ""))
        if method in _PRECHECK_FORMAT_LABELS or (raw_v != clean_v and method != "TEXT_NORMALIZED"):
            result["format_rows"].append({
                "Mức độ": "Trung bình", "Tab": a.get("Tab", "—"), "Dòng": a.get("Row_Index", "—"),
                "Mã đơn": a.get("Record_ID", "—"), "Cột / Trường": a.get("Column", "—"),
                "Loại vấn đề": _PRECHECK_FORMAT_LABELS.get(method, a.get("Reason", method)),
                "Giá trị gốc": raw_v, "Mô tả chi tiết": a.get("Reason", ""),
                "Hướng xử lý khi Làm sạch": f"Tự chuẩn hóa thành: {clean_v}" if clean_v else "Tự chuẩn hóa an toàn",
                "_code": method,
            })

    for t_name, t_info in (getattr(cleaner, "tab_statuses", {}) or {}).items():
        t_stat = str((t_info or {}).get("Status", ""))
        if t_stat in ("FAILED", "WARNING", "QUOTA_WARNING", "NEEDS_APPROVAL"):
            result["schema_rows"].append({
                "Mức độ": "Cao" if t_stat == "FAILED" else "Trung bình", "Tab": t_name,
                "Loại vấn đề": f"Trạng thái tab: {vi_status(t_stat, q_sum)}",
                "Mô tả chi tiết": str((t_info or {}).get("Message", "")),
                "Hướng xử lý khi Làm sạch": "Xem chi tiết lỗi của tab ở danh sách bên trên",
            })

    # Gom nhóm để liệt kê ngắn gọn
    def _group(rows, sev_tag):
        buckets = {}
        for r in rows:
            k = r.get("Loại vấn đề", "Khác")
            buckets.setdefault(k, []).append(r)
        out = []
        for k, items in buckets.items():
            samples = []
            for it in items[:3]:
                rid = it.get("Mã đơn", "—")
                rv = str(it.get("Giá trị gốc", "")).strip()
                samples.append(f"{rid}" + (f" ('{rv[:40]}')" if rv and rv not in ("—", rid) else ""))
            out.append((sev_tag, k, len(items), ", ".join(samples)))
        return out

    result["grouped"] = (
        _group(result["critical_rows"], "high")
        + _group(result["format_rows"], "med")
        + _group(result["schema_rows"], "med")
    )
    result["total_problem_count"] = len(result["critical_rows"]) + len(result["format_rows"]) + len(result["schema_rows"])
    result["has_problems"] = result["total_problem_count"] > 0 or result["has_blocking_error"]
    return result


def get_or_run_pre_clean_scan() -> dict:
    if not st.session_state.get("raw_tabs"):
        return None
    if st.session_state.get("pre_clean_scan") is None:
        st.session_state.pre_clean_scan = scan_raw_data_issues(
            st.session_state.raw_tabs,
            class_info=st.session_state.get("classification_info"),
            max_row_limit=st.session_state.get("max_row_limit", MAX_ROW_LIMIT),
        )
    return st.session_state.pre_clean_scan


def _precheck_df(rows: list) -> pd.DataFrame:
    df = pd.DataFrame([{k: v for k, v in r.items() if not str(k).startswith("_")} for r in rows])
    return sanitize_df_for_display(df.astype(str)) if not df.empty else df


def render_pre_clean_diagnostics(context: str = "connect") -> None:
    """Hiển thị thông báo & danh sách lỗi dữ liệu gốc trước khi người dùng bấm Làm sạch."""
    scan = get_or_run_pre_clean_scan()
    if not scan:
        return
    with st.container(key=f"card_conn_precheck_{context}"):
        card_header(
            "🩺 Kiểm tra sơ bộ dữ liệu trước khi làm sạch",
            f"Nguồn: {st.session_state.source_name} • {scan['total_tabs']} tab • {scan['total_rows']:,} dòng • Dữ liệu gốc CHƯA bị chỉnh sửa",
        )
        n_crit, n_fmt, n_sch = len(scan["critical_rows"]), len(scan["format_rows"]), len(scan["schema_rows"])

        if scan["has_problems"]:
            if not scan.get("_toasted"):
                st.toast(f"Phát hiện {scan['total_problem_count']} vấn đề trong dữ liệu gốc — vui lòng xem danh sách trước khi làm sạch", icon="⚠️")
                scan["_toasted"] = True
            html(
                f'<div class="result-banner fail"><div><b>⚠️ Dữ liệu có {scan["total_problem_count"]} vấn đề cần lưu ý trước khi làm sạch</b>'
                f'<small>{n_crit} lỗi / ngoại lệ • {n_fmt} giá trị sai định dạng • {n_sch} cảnh báo cấu trúc. '
                f'Hệ thống chưa thay đổi dữ liệu — các lỗi chỉ được xử lý khi bạn bấm <b>Bắt đầu làm sạch &amp; chuẩn hóa</b>.</small></div></div>'
            )
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Lỗi / Ngoại lệ", f"{n_crit:,}")
            m2.metric("Định dạng cần chuẩn hóa", f"{n_fmt:,}")
            m3.metric("Cảnh báo cấu trúc", f"{n_sch:,}")
            est = scan.get("estimated_score")
            m4.metric("Điểm chất lượng sơ bộ", f"{est}%" if est is not None else "—")

            rows_html = []
            for sev, label, cnt, sample in scan["grouped"]:
                tag_txt = "LỖI" if sev == "high" else "CẢNH BÁO"
                rows_html.append(
                    f'<div class="precheck-row"><span class="precheck-tag {sev}">{tag_txt}</span>'
                    f'<div><b>{_html.escape(str(label))}</b> — {cnt} bản ghi'
                    f'<small>Ví dụ: {_html.escape(str(sample)) if sample else "—"}</small></div></div>'
                )
            for r in scan["info_rows"]:
                rows_html.append(
                    f'<div class="precheck-row"><span class="precheck-tag info">THÔNG TIN</span>'
                    f'<div><b>{_html.escape(str(r["Loại vấn đề"]))}</b><small>{_html.escape(str(r["Mô tả chi tiết"]))}</small></div></div>'
                )
            html(f'<div class="precheck-box"><div class="precheck-box-title">Danh sách lỗi &amp; vấn đề phát hiện được</div>{"".join(rows_html)}</div>')

            t_crit, t_fmt, t_sch = st.tabs([f"🔴 Lỗi & Ngoại lệ ({n_crit})", f"🟡 Định dạng cần chuẩn hóa ({n_fmt})", f"ℹ️ Cấu trúc & Cột ({n_sch + len(scan['info_rows'])})"])
            with t_crit:
                if n_crit:
                    st.dataframe(_precheck_df(scan["critical_rows"]), width="stretch", hide_index=True)
                else:
                    st.caption("Không có lỗi nghiêm trọng hay ngoại lệ.")
            with t_fmt:
                if n_fmt:
                    st.dataframe(_precheck_df(scan["format_rows"]), width="stretch", hide_index=True)
                else:
                    st.caption("Không có giá trị sai định dạng.")
            with t_sch:
                sch_all = scan["schema_rows"] + scan["info_rows"]
                if sch_all:
                    st.dataframe(_precheck_df(sch_all), width="stretch", hide_index=True)
                else:
                    st.caption("Cấu trúc các tab hợp lệ.")

            if context == "connect":
                st.warning("Vui lòng xem kỹ danh sách lỗi ở trên. Khi đã nắm rõ, chuyển sang bước Làm sạch để hệ thống tự chuẩn hóa và đưa các ngoại lệ vào hàng chờ phê duyệt.")
                st.button(
                    "Đã kiểm tra danh sách lỗi — Chuyển sang bước Làm sạch →",
                    type="primary",
                    key="conn_precheck_go_clean_issues",
                    on_click=go_to,
                    args=(PAGES[2],),
                )
        else:
            html(
                '<div class="result-banner pass"><div><b>✅ Kiểm tra sơ bộ đạt chuẩn — Không phát hiện lỗi dữ liệu gốc</b>'
                f'<small>Điểm chất lượng sơ bộ: {scan.get("estimated_score", "—")}%. Bạn có thể chuyển sang bước Làm sạch để chuẩn hóa.</small></div></div>'
            )
            if scan["info_rows"]:
                rows_html = "".join(
                    f'<div class="precheck-row"><span class="precheck-tag info">THÔNG TIN</span>'
                    f'<div><b>{_html.escape(str(r["Loại vấn đề"]))}</b><small>{_html.escape(str(r["Mô tả chi tiết"]))}</small></div></div>'
                    for r in scan["info_rows"]
                )
                html(f'<div class="precheck-box" style="border-left-color: var(--df-blue);">{rows_html}</div>')
            if context == "connect":
                st.button(
                    "Chuyển sang bước Làm sạch →",
                    type="primary",
                    key="conn_precheck_go_clean_ok",
                    on_click=go_to,
                    args=(PAGES[2],),
                )


def run_cleaning(quota_policy: str = None) -> None:
    import traceback
    st.session_state.cleaning_status = "PROCESSING"
    st.session_state.cleaning_error_detail = None
    active_policy = quota_policy or st.session_state.get("quota_policy", "WARN_AND_QUARANTINE")
    st.session_state.quota_policy = active_policy
    try:
        cleaner = DataCleaner(
            st.session_state.raw_tabs,
            tab_classification=st.session_state.classification_info,
            max_row_limit=st.session_state.get("max_row_limit", MAX_ROW_LIMIT),
            quota_policy=active_policy,
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
            norm_data,
            initial_exceptions=excs,
            return_window_days=st.session_state.return_window,
            quality_summary=q_sum,
        )
        try:
            st.session_state.cleaned_excel = cleaner.export_cleaned_data_excel()
        except Exception:
            st.session_state.cleaned_excel = None
    except Exception as exc:
        st.session_state.can_proceed_process = False
        st.session_state.cleaning_status = "FAILED"
        st.session_state.cleaning_error_detail = f"{type(exc).__name__}: {exc}\n\n{traceback.format_exc()}"


def apply_quota_action(policy: str, rerun_process: bool = True) -> None:
    """Áp dụng nhanh chính sách xử lý vượt ngưỡng Quota & cập nhật Workflow."""
    run_cleaning(quota_policy=policy)
    if rerun_process and st.session_state.can_proceed_process:
        run_process()


def render_quota_guardrail_banner(key_prefix: str) -> None:
    """Hiển thị cảnh báo Quota & nút hành động nhanh khi file vượt MAX_ROW_LIMIT."""
    q = st.session_state.quality_summary or {}
    if not q.get("Quota_Exceeded"):
        return
    raw_rows = int(q.get("Raw_Transactions_Count", 0))
    max_lim = int(q.get("Max_Row_Limit", MAX_ROW_LIMIT))
    excess = int(q.get("Excess_Rows_Count", max(0, raw_rows - max_lim)))
    quar_cnt = int(q.get("Quarantined_Rows_Count", 0))
    policy = q.get("Quota_Policy", st.session_state.quota_policy)
    quota_text = q.get("Quota_Status_Text", f"CẢNH BÁO QUOTA ({raw_rows:,} / {max_lim:,} dòng)")

    if policy == "ALLOW_ALL_ROWS":
        detail = f"Đang bật ngoại lệ xử lý toàn bộ <b>{raw_rows:,}</b> dòng vượt định mức {max_lim:,}."
    else:
        detail = f"Phát hiện <b>{excess:,}</b> dòng vượt định mức kiểm toán; hiện đang cách ly <b>{quar_cnt:,}</b> dòng dư sang Khu Cách Ly (Quarantine) &amp; Exceptions."

    html(f"""
    <div class="result-banner fail" style="background:linear-gradient(135deg,#FFFBEB,#FEF3C7);border-color:#F59E0B;color:#92400E;">
        <div>
            <b>⚠️ {quota_text}</b>
            <small>{detail}</small>
        </div>
        <span class="pill-count">Chính sách: {policy}</span>
    </div>
    """)
    qc1, qc2 = st.columns(2)
    with qc1:
        if st.button(
            f"✂️ Tự động cắt ngọn về {max_lim:,} dòng hợp lệ & Đẩy dòng dư sang Exceptions",
            width="stretch",
            key=f"{key_prefix}_btn_quota_truncate",
        ):
            with st.spinner("Đang áp dụng cắt ngọn Quota & cách ly dòng dư..."):
                apply_quota_action("TRUNCATE_TO_QUOTA", rerun_process=has_report() or st.session_state.process_status == "COMPLETED")
            queue_toast(f"Đã cắt giữ {max_lim:,} dòng hợp lệ & đẩy {excess:,} dòng dư sang Exceptions/Quarantine", "⚠️")
            st.rerun()
    with qc2:
        if st.button(
            f"🔓 Cho phép xử lý ngoại lệ toàn bộ {raw_rows:,} dòng",
            width="stretch",
            key=f"{key_prefix}_btn_quota_allow",
        ):
            with st.spinner(f"Đang xử lý toàn bộ {raw_rows:,} dòng..."):
                apply_quota_action("ALLOW_ALL_ROWS", rerun_process=has_report() or st.session_state.process_status == "COMPLETED")
            queue_toast(f"Đã cho phép xử lý ngoại lệ toàn bộ {raw_rows:,} dòng", "✅")
            st.rerun()


def build_financial_waterfall_fig(rep: pd.DataFrame) -> tuple:
    """Xây dựng biểu đồ Thác nước Tài chính (Financial Waterfall Chart) tự thích ứng đơn bảng/đa bảng."""
    if rep is None or rep.empty:
        return None, True, "Chưa có dữ liệu báo cáo."

    attr_rev = float(rep["Attributed_Revenue"].apply(safe_float).sum()) if "Attributed_Revenue" in rep.columns else 0.0
    attr_ret = float(rep["Attributed_Return"].apply(safe_float).sum()) if "Attributed_Return" in rep.columns else 0.0
    net_sales = float(rep["Net_Sales"].apply(safe_float).sum()) if "Net_Sales" in rep.columns else (attr_rev - attr_ret)
    cogs_val = float(rep["Attributed_COGS"].apply(safe_float).sum()) if "Attributed_COGS" in rep.columns else 0.0
    has_costs = ("Total_Cost" in rep.columns) and rep["Total_Cost"].notna().any()
    has_returns = attr_ret > 0

    direct_cost = float(rep["Direct_Cost"].apply(safe_float).sum()) if (has_costs and "Direct_Cost" in rep.columns) else 0.0
    overhead_cost = float(rep["Allocated_Overhead"].apply(safe_float).sum()) if (has_costs and "Allocated_Overhead" in rep.columns) else 0.0
    net_contrib = float(rep["Net_Contribution"].apply(safe_float).sum()) if (has_costs and "Net_Contribution" in rep.columns) else (net_sales - cogs_val)

    x_labels = ["Tổng Doanh thu Phân bổ<br>(Attributed Revenue)"]
    measures = ["absolute"]
    y_vals = [attr_rev]

    if has_returns:
        x_labels.append("(-) Giảm trừ Hoàn trả<br>(Attributed Return)")
        measures.append("relative")
        y_vals.append(-attr_ret)

    x_labels.append("(=) Doanh thu Thuần<br>(Net Sales)")
    measures.append("total")
    y_vals.append(net_sales)

    if cogs_val > 0:
        x_labels.append("(-) Giá vốn hàng bán<br>(COGS)")
        measures.append("relative")
        y_vals.append(-cogs_val)

    single_table_mode = not has_costs
    if has_costs:
        x_labels.append("(-) Chi phí Trực tiếp<br>(Direct Cost)")
        measures.append("relative")
        y_vals.append(-direct_cost)

        x_labels.append("(-) Chi phí Quản lý Phân bổ<br>(Allocated Overhead ABC)")
        measures.append("relative")
        y_vals.append(-overhead_cost)

        x_labels.append("(=) Lợi nhuận Đóng góp Ròng<br>(Net Contribution)")
        measures.append("total")
        y_vals.append(net_contrib)
        mode_note = "Hiển thị dòng chảy tài chính đầy đủ từ Doanh thu phân bổ -> Giảm trừ hoàn trả -> Doanh thu thuần -> Chi phí ABC -> Lợi nhuận đóng góp ròng."
    else:
        if cogs_val > 0:
            x_labels.append("(=) Lợi nhuận Gộp<br>(Gross Profit)")
            measures.append("total")
            y_vals.append(net_sales - cogs_val)
        mode_note = "Đang chạy ở chế độ Đơn bảng (Single-Table Audit Mode) — Các cột Chi phí Trực tiếp / Chi phí Quản lý ABC (và Hoàn trả nếu thiếu) đã được ẩn tự động."

    text_vals = [f"{v:,.0f} đ" for v in y_vals]
    fig = go.Figure(
        go.Waterfall(
            orientation="v",
            measure=measures,
            x=x_labels,
            textposition="outside",
            text=text_vals,
            y=y_vals,
            connector={"line": {"color": "#EADDD5", "width": 1.5, "dash": "dot"}},
            increasing={"marker": {"color": "#27845E"}},
            decreasing={"marker": {"color": "#C21F20"}},
            totals={"marker": {"color": "#5277A6"}},
        )
    )
    style_chart(fig, height=360)
    fig.update_layout(showlegend=False)
    return fig, single_table_mode, mode_note


def compute_what_if_projection(
    rep: pd.DataFrame,
    direct_cost_delta_pct: float = 0.0,
    return_reduction_pct: float = 0.0,
    overhead_reduction_pct: float = 0.0,
) -> dict:
    """Tính toán tức thời tác động What-If lên Net Sales, Total Cost, Net Contribution và ROI."""
    if rep is None or rep.empty:
        return {}
    attr_rev = float(rep["Attributed_Revenue"].apply(safe_float).sum()) if "Attributed_Revenue" in rep.columns else 0.0
    curr_ret = float(rep["Attributed_Return"].apply(safe_float).sum()) if "Attributed_Return" in rep.columns else 0.0
    curr_ns = float(rep["Net_Sales"].apply(safe_float).sum()) if "Net_Sales" in rep.columns else (attr_rev - curr_ret)
    curr_cogs = float(rep["Attributed_COGS"].apply(safe_float).sum()) if "Attributed_COGS" in rep.columns else 0.0
    has_costs = ("Total_Cost" in rep.columns) and rep["Total_Cost"].notna().any()
    curr_dc = float(rep["Direct_Cost"].apply(safe_float).sum()) if (has_costs and "Direct_Cost" in rep.columns) else 0.0
    curr_ovh = float(rep["Allocated_Overhead"].apply(safe_float).sum()) if (has_costs and "Allocated_Overhead" in rep.columns) else 0.0
    curr_tc = curr_dc + curr_ovh
    curr_nc = float(rep["Net_Contribution"].apply(safe_float).sum()) if (has_costs and "Net_Contribution" in rep.columns) else (curr_ns - curr_cogs)
    curr_roi = (curr_nc / curr_tc * 100.0) if curr_tc > 0 else ((curr_nc / curr_cogs * 100.0) if curr_cogs > 0 else 0.0)

    ret_factor = max(0.0, 1.0 - abs(float(return_reduction_pct)) / 100.0)
    ovh_factor = max(0.0, 1.0 - abs(float(overhead_reduction_pct)) / 100.0)
    dc_factor = max(0.0, 1.0 + float(direct_cost_delta_pct) / 100.0)

    proj_ret = curr_ret * ret_factor
    proj_ns = attr_rev - proj_ret
    proj_dc = curr_dc * dc_factor
    proj_ovh = curr_ovh * ovh_factor
    proj_tc = proj_dc + proj_ovh
    proj_nc = proj_ns - curr_cogs - proj_tc
    proj_roi = (proj_nc / proj_tc * 100.0) if proj_tc > 0 else ((proj_nc / curr_cogs * 100.0) if curr_cogs > 0 else 0.0)

    return {
        "has_costs": has_costs,
        "curr_net_sales": curr_ns,
        "proj_net_sales": proj_ns,
        "delta_net_sales": proj_ns - curr_ns,
        "curr_total_cost": curr_tc,
        "proj_total_cost": proj_tc,
        "delta_total_cost": proj_tc - curr_tc,
        "curr_net_contribution": curr_nc,
        "proj_net_contribution": proj_nc,
        "delta_net_contribution": proj_nc - curr_nc,
        "curr_roi": curr_roi,
        "proj_roi": proj_roi,
        "delta_roi": proj_roi - curr_roi,
    }


def render_what_if_simulator(rep: pd.DataFrame, key_prefix: str = "ov") -> None:
    """Render Expander Mô phỏng Kịch bản Tài chính (What-If Simulator) với 3 thanh trượt."""
    if rep is None or rep.empty:
        return
    with st.expander("🎛️ Mô phỏng Kịch bản Tài chính (What-If Simulator)", expanded=False):
        st.caption("Điều chỉnh 3 tham số chiến lược để mô phỏng tác động tức thời tới Net Sales, Chi phí ABC, Net Contribution và ROI.")
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            dc_delta = st.slider(
                "Ngân sách Trực tiếp (Direct Cost: -50% đến +100%)",
                min_value=-50, max_value=100, value=0, step=5,
                key=f"{key_prefix}_whatif_dc",
            )
        with sc2:
            ret_red = st.slider(
                "Tối ưu giảm Tỷ lệ Hoàn hàng (0% đến -50%)",
                min_value=-50, max_value=0, value=0, step=5,
                key=f"{key_prefix}_whatif_ret",
            )
        with sc3:
            ovh_red = st.slider(
                "Cắt giảm Chi phí Quản lý chung (0% đến -30%)",
                min_value=-30, max_value=0, value=0, step=5,
                key=f"{key_prefix}_whatif_ovh",
            )

        sim = compute_what_if_projection(rep, dc_delta, ret_red, ovh_red)
        if not sim.get("has_costs"):
            st.info("ℹ️ Chế độ Đơn bảng (chưa có tab Campaign_Costs): Direct Cost và Overhead hiện bằng 0 đ; ROI giả lập đang tham chiếu trên Giá vốn (COGS) nếu có.")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric(
            "Projected Net Sales",
            fmt_vnd(sim["proj_net_sales"]),
            delta=f"{sim['delta_net_sales']:+,.0f} đ",
        )
        m2.metric(
            "Projected Total Cost (ABC)",
            fmt_vnd(sim["proj_total_cost"]) if sim["has_costs"] else "Chưa có ABC Cost",
            delta=f"{sim['delta_total_cost']:+,.0f} đ" if sim["has_costs"] else None,
            delta_color="inverse",
        )
        m3.metric(
            "Projected Net Contribution",
            fmt_vnd(sim["proj_net_contribution"]),
            delta=f"{sim['delta_net_contribution']:+,.0f} đ",
        )
        m4.metric(
            "Projected ROI",
            f"{sim['proj_roi']:+.1f}%",
            delta=f"{sim['delta_roi']:+.1f} điểm %",
        )


def quick_approve_all_and_verify() -> int:
    """Phê duyệt nhanh toàn bộ ngoại lệ PENDING_REVIEW & chạy lại Process + Verification Gate."""
    eng = st.session_state.engine
    if eng is None:
        return 0
    approved_count = 0
    reviewer_name = str(st.session_state.user_name or ADMIN_NAME).strip() or ADMIN_NAME
    for exc in list(eng.exceptions_view):
        if exc.get("Approval_Status") == "PENDING_REVIEW":
            ok, _ = eng.resolve_exception(
                exc["Order_ID"],
                "APPROVED",
                "Trưởng phòng Marketing",
                reviewer_name,
                "Phê duyệt nhanh toàn bộ ngoại lệ từ Trung tâm Tác vụ Nhanh (Quick Action)",
                error_type=exc.get("Error_Type"),
            )
            if ok:
                approved_count += 1
    st.session_state.exceptions_list = eng.exceptions_view
    st.session_state.process_status = "COMPLETED" if eng.report_result is not None else st.session_state.process_status
    vr = eng.run_verification()
    st.session_state.verification_result = vr
    st.session_state.verification_status = vr.get("overall_status", "NOT_RUN")
    return approved_count


def render_executive_pulse_bar(
    rep: pd.DataFrame,
    norm_tx: pd.DataFrame,
    q: dict,
    total_gross_rev: float,
    total_net: float,
) -> None:
    """Dải 4 thẻ nhịp đập điều hành bo tròn loang hồng đỏ với hiệu ứng hover nổi khối."""
    retention_pct = (total_net / total_gross_rev * 100.0) if total_gross_rev > 0 else 100.0
    n_orders = len(norm_tx) if (norm_tx is not None and not norm_tx.empty) else int(rep["Orders_Count"].apply(safe_float).sum())
    aov = (total_gross_rev / n_orders) if n_orders > 0 else 0.0

    top_row = rep.sort_values("Net_Sales", ascending=False).iloc[0] if not rep.empty else None
    top_name = str(top_row["Campaign_Name"]) if top_row is not None else "—"
    top_ns = safe_float(top_row["Net_Sales"], 0.0) if top_row is not None else 0.0

    ver = st.session_state.verification_result or {}
    if ver.get("tests"):
        ver_label = f"{ver.get('pass_count', 0)}/{len(ver['tests'])} ({ver.get('overall_status', '—')})"
    else:
        ver_label = f"{len(pending_exceptions())} Hồ sơ chờ HITL"

    html(f"""
    <div class="pulse-grid">
        <div class="pulse-pill">
            <div class="pulse-top"><span>💖 Bảo toàn Doanh thu</span><span class="badge ok">Net/Gross</span></div>
            <div class="pulse-val">{retention_pct:.1f}%</div>
            <div class="pulse-sub">Tỷ lệ giữ lại sau giảm giá &amp; hoàn trả</div>
        </div>
        <div class="pulse-pill">
            <div class="pulse-top"><span>🔥 Chiến dịch Ngôi sao</span><span class="badge warn">Top Revenue</span></div>
            <div class="pulse-val" style="font-size:15.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{top_name}</div>
            <div class="pulse-sub">Đóng góp Net Sales: {fmt_vnd(top_ns)}</div>
        </div>
        <div class="pulse-pill">
            <div class="pulse-top"><span>🚀 Giá trị Đơn TB (AOV)</span><span class="badge idle">{n_orders:,} đơn</span></div>
            <div class="pulse-val">{fmt_vnd(aov)}</div>
            <div class="pulse-sub">Bình quân Doanh thu gộp mỗi đơn hàng</div>
        </div>
        <div class="pulse-pill">
            <div class="pulse-top"><span>🛡️ Kiểm toán &amp; HITL</span><span class="badge {'ok' if ver.get('overall_status') == 'PASS' else 'warn'}">Audit Gate</span></div>
            <div class="pulse-val" style="font-size:16.5px;">{ver_label}</div>
            <div class="pulse-sub">Điểm dữ liệu: {q.get('Data_Quality_Score', '—')}%</div>
        </div>
    </div>
    """)


def render_campaign_health_cards(rep: pd.DataFrame) -> None:
    """Render lưới thẻ sức khỏe & xếp hạng chiến dịch bo tròn với hiệu ứng hover nổi mượt."""
    if rep is None or rep.empty:
        return
    import html as _html_mod
    total_ns = max(1.0, float(rep["Net_Sales"].apply(safe_float).sum()))
    has_costs = ("Total_Cost" in rep.columns) and rep["Total_Cost"].notna().any()
    sorted_rep = rep.sort_values("Net_Sales", ascending=False).head(6)
    cards = []
    for _, r in sorted_rep.iterrows():
        cname = _html_mod.escape(str(r.get("Campaign_Name", r.get("Campaign_ID", "N/A"))))
        chan = _html_mod.escape(str(r.get("Channel", "General")))
        ns = safe_float(r.get("Net_Sales"), 0.0)
        share_pct = min(100.0, max(0.0, ns / total_ns * 100.0))
        dec = str(r.get("Strategic_Decision", "N/A"))
        badge_cls = "ok" if ("SCALE" in dec or "MỞ RỘNG" in dec) else ("fail" if ("TERMINATE" in dec or "DỪNG" in dec) else "warn")
        dec_short = _html_mod.escape(dec.split("(")[0].strip()[:22] or "ACTIVE")
        if has_costs:
            nc = safe_float(r.get("Net_Contribution"), 0.0)
            roi = safe_float(r.get("ROI"), 0.0)
            roas = safe_float(r.get("ROAS"), 0.0)
            nc_color = "#27845E" if nc >= 0 else "#C21F20"
            foot_html = f"<span>Net Contrib: <b style='color:{nc_color}'>{fmt_vnd(nc)}</b></span><span>ROAS {roas:.2f}x • ROI {roi:+.1f}%</span>"
        else:
            ret_val = safe_float(r.get("Attributed_Return"), 0.0)
            foot_html = f"<span>Net Sales: <b style='color:#C21F20'>{fmt_vnd(ns)}</b></span><span>Hoàn trả: {fmt_vnd(ret_val)}</span>"
        cards.append(f"""
        <div class="camp-health-card">
            <div class="camp-h-head">
                <div>
                    <div class="camp-h-name">{cname}</div>
                    <div class="camp-h-chan">{chan} • Tỷ trọng {share_pct:.1f}%</div>
                </div>
                <span class="badge {badge_cls}">{dec_short}</span>
            </div>
            <div class="camp-h-metrics">{foot_html}</div>
            <div class="camp-bar-track"><div class="camp-bar-fill" style="width:{share_pct:.1f}%;"></div></div>
        </div>
        """)
    html(f'<div class="camp-health-grid">{"".join(cards)}</div>')


def run_process() -> dict:
    if st.session_state.engine is None:
        st.session_state.engine = MarketingAnalyticsEngine(
            st.session_state.normalized_data,
            initial_exceptions=st.session_state.exceptions_list,
            return_window_days=st.session_state.return_window,
            quality_summary=st.session_state.quality_summary,
        )
    else:
        st.session_state.engine.quality_summary = st.session_state.quality_summary
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
    elif s.cleaning_status == "QUOTA_WARNING":
        clean = "warn"
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
    pend = pending_exceptions()
    lines = [
        f"- Người dùng hiện tại: {s.user_name} ({s.user_role})",
        f"- Nguồn dữ liệu: {s.source_name if s.data_status == 'CONNECTED' else 'Chưa kết nối'}",
        f"- Trạng thái làm sạch: {vi_status(s.cleaning_status)}",
        f"- Quy trình 6 bước: {s.process_status}",
        f"- Kiểm toán Verification: {s.verification_status}",
        f"- Ngoại lệ chờ duyệt: {len(pend)}/{len(s.exceptions_list)}",
    ]
    if s.get("biz_industry"):
        lines.append(f"- Bối cảnh doanh nghiệp: {s.biz_industry}" + (f" ({s.biz_extra_info})" if s.get("biz_extra_info") else ""))
    if s.get("biz_questions"):
        lines.append(f"- Vấn đề cần phân tích: {s.biz_questions.replace(chr(10), '; ')}")
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
        active_df = eng.get_active_transactions_df()
        _g_rev = rep["Gross_Revenue"].sum() if ("Gross_Revenue" in rep.columns and rep["Gross_Revenue"].notna().any()) else rep["Attributed_Revenue"].sum()
        lines.append(
            f"- Tổng doanh thu gộp: {fmt_vnd(_g_rev)} | "
            f"Doanh thu phân bổ: {fmt_vnd(rep['Attributed_Revenue'].sum())} | "
            f"Net Sales: {fmt_vnd(rep['Net_Sales'].sum())}"
        )
        if active_df is not None and not active_df.empty:
            if "COGS" in active_df.columns:
                lines.append(f"- Tổng giá vốn (COGS): {fmt_vnd(pd.to_numeric(active_df['COGS'], errors='coerce').dropna().sum())}")
            if "Source_Profit" in active_df.columns:
                lines.append(f"- Tổng lợi nhuận gộp: {fmt_vnd(pd.to_numeric(active_df['Source_Profit'], errors='coerce').dropna().sum())}")
            if "Channel" in active_df.columns and "Order_Value" in active_df.columns:
                ch_df = active_df[["Channel", "Order_Value"]].copy()
                ch_df["Order_Value"] = pd.to_numeric(ch_df["Order_Value"], errors="coerce").fillna(0)
                by_ch = ch_df.groupby("Channel")["Order_Value"].sum()
                by_ch = by_ch[by_ch > 0].sort_values(ascending=False)
                if not by_ch.empty:
                    lines.append(f"- Kênh dẫn đầu: {by_ch.index[0]} ({fmt_vnd(by_ch.iloc[0])})")
            if "Product_Name" in active_df.columns and active_df["Product_Name"].notna().any():
                pr_df = active_df[["Product_Name", "Order_Value"]].dropna(subset=["Product_Name"]).copy()
                pr_df["Order_Value"] = pd.to_numeric(pr_df["Order_Value"], errors="coerce").fillna(0)
                by_pr = pr_df.groupby("Product_Name")["Order_Value"].sum().sort_values(ascending=False)
                if not by_pr.empty:
                    lines.append(f"- Sản phẩm dẫn đầu: {by_pr.index[0]} ({fmt_vnd(by_pr.iloc[0])})")
    return "\n".join(lines)


def _offline_smart_fallback(question: str, ctx: str) -> str:
    """Bộ giải toán & kiến thức nội bộ khi môi trường ngoại tuyến."""
    import ast
    import operator as _op
    import re as _re

    q = (question or "").strip()
    m = _re.fullmatch(r'[\s\d\+\-\*\/\(\)\.\^\%]+', q)
    if m and any(c.isdigit() for c in q):
        expr = q.replace("^", "**")
        ops = {ast.Add: _op.add, ast.Sub: _op.sub, ast.Mult: _op.mul, ast.Div: _op.truediv, ast.Mod: _op.mod, ast.Pow: _op.pow}
        def _eval(node):
            if isinstance(node, ast.Expression):
                return _eval(node.body)
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return node.value
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
                return -_eval(node.operand)
            if isinstance(node, ast.BinOp) and type(node.op) in ops:
                return ops[type(node.op)](_eval(node.left), _eval(node.right))
            raise ValueError("Unsupported")
        try:
            val = _eval(ast.parse(expr, mode="eval"))
            return f"Kết quả phép tính `{q}` = **{val:,.4g}**"
        except Exception:
            pass

    q_l = q.lower()
    if any(k in q_l for k in ["roas", "roi", "cogs", "abc", "net sales", "net contribution"]):
        return (
            "**Giải thích chỉ số Marketing & Tài chính trong hệ thống:**\n"
            "- **Net Sales:** Doanh thu thuần sau giảm giá và hoàn trả.\n"
            "- **COGS:** Giá vốn hàng bán.\n"
            "- **Chi phí ABC (Activity Based Costing):** Tổng chi phí trực tiếp + chi phí vận hành phân bổ cho từng chiến dịch.\n"
            "- **Net Contribution:** `Net Sales - COGS - Tổng chi phí ABC`.\n"
            "- **ROAS:** `Net Sales / Tổng chi phí` | **ROI:** `(Net Sales - COGS - Tổng chi phí) / Tổng chi phí × 100%`."
        )

    return (
        f"Hiện kết nối AI Cloud tạm gián đoạn, dưới đây là **trạng thái phiên thực tế** của bạn:\n{ctx}\n\n"
        "Bạn có thể hỏi về quy trình, số liệu KPI, ngoại lệ, tính toán nhanh, hoặc giải thích chỉ số `ROAS` / `ROI` / `COGS`."
    )


def _call_llm_brain(question: str, ctx: str) -> str:
    """Gọi bộ não LLM đa tầng (OpenAI -> Pollinations ChatGPT -> Gemini -> Offline Fallback)."""
    import os
    import requests as _req

    s = st.session_state
    system_prompt = (
        "Bạn là Trợ lý AI thông minh đa năng (tương tự ChatGPT) tích hợp trong nền tảng Data Forge Enterprise Analytics & BI SaaS. "
        "Bạn có thể trả lời mọi câu hỏi ở mọi lĩnh vực (kiến thức chung, khoa học, kinh doanh, Marketing, tài chính, lập trình, toán học, viết nội dung, dịch thuật...) "
        "một cách chính xác, tự nhiên bằng ngôn ngữ người dùng hỏi (ưu tiên tiếng Việt). "
        "Khi câu hỏi liên quan đến dữ liệu hoặc phiên làm việc hiện tại, chỉ sử dụng đúng số liệu thực tế sau và tuyệt đối không bịa số:\n"
        f"{ctx}"
    )

    messages = [{"role": "system", "content": system_prompt}]
    for item in (s.chat_history or [])[-8:]:
        r = item.get("role", "user")
        c = str(item.get("content", "")).strip()
        if r in ("user", "assistant") and c:
            messages.append({"role": r, "content": c})
    if not messages or messages[-1].get("content") != question:
        messages.append({"role": "user", "content": question})

    # Tầng 1: OpenAI API (nếu có key riêng)
    openai_key = (s.get("custom_openai_key") or os.environ.get("OPENAI_API_KEY", "")).strip()
    if openai_key:
        try:
            resp = _req.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                json={"model": "gpt-4o-mini", "messages": messages, "temperature": 0.7},
                timeout=18,
            )
            if resp.status_code == 200:
                txt = resp.json()["choices"][0]["message"]["content"].strip()
                if txt:
                    return txt
        except Exception:
            pass

    # Tầng 2: Pollinations OpenAI-compatible ChatGPT endpoint (miễn phí, không cần API key)
    try:
        resp = _req.post(
            "https://text.pollinations.ai/openai",
            headers={"Content-Type": "application/json"},
            json={"model": "openai", "messages": messages},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            txt = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if txt:
                return txt
    except Exception:
        pass

    # Tầng 3: Google Gemini API (nếu có GEMINI_API_KEY)
    gemini_key = (s.get("custom_gemini_key") or os.environ.get("GEMINI_API_KEY", "")).strip()
    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            prompt = f"{system_prompt}\n\nCâu hỏi người dùng: {question}"
            resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            if resp and getattr(resp, "text", None):
                return resp.text.strip()
        except Exception:
            pass

    return _offline_smart_fallback(question, ctx)


KNOWN_CHAT_CHANNELS = [
    ("tiktok shop", "TikTok Shop"),
    ("tiktok", "TikTok Shop"),
    ("shopee", "Shopee"),
    ("lazada", "Lazada"),
    ("tiki", "Tiki"),
    ("website direct", "Website Direct"),
    ("website", "Website Direct"),
    ("facebook messenger", "Facebook Messenger"),
    ("facebook ads", "Facebook Ads"),
    ("facebook", "Facebook"),
    ("google ads", "Google Ads"),
    ("google", "Google"),
    ("youtube", "YouTube"),
    ("hotline", "Hotline"),
    ("zalo", "Zalo"),
    ("email", "Email"),
]

INVALID_ERROR_TYPES = {
    "MISSING_ORDER_ID",
    "EXCEPTION_INVALID",
    "EXCEPTION_NEGATIVE",
    "EXCEPTION_MISSING",
    "INVALID_CURRENCY_FORMAT",
    "NEGATIVE_CURRENCY",
    "INVALID_CAMPAIGN_FORMAT",
    "COGS_EXCEPTION_INVALID",
    "COGS_EXCEPTION_NEGATIVE",
}


def _extract_order_ids_from_text(text: str) -> list:
    import re as _re
    raw = _re.findall(r'\b(?:ORD-[A-Z0-9\-]+|TEMP-UNKNOWN-\d+|[A-Z]{2,6}-\d{2,6})\b', str(text or ""), flags=_re.IGNORECASE)
    seen = []
    for oid in raw:
        up = oid.upper()
        if up.startswith("CHK-"):
            continue
        if up not in seen:
            seen.append(up)
    return seen


def _parse_chat_vnd_amount(text: str):
    import re as _re
    cleaned = str(text or "")
    cleaned = _re.sub(r'\b(?:ORD-[A-Z0-9\-]+|TEMP-UNKNOWN-\d+|CHK-\d+|[A-Z]{2,6}-\d{2,6})\b', ' ', cleaned, flags=_re.IGNORECASE)
    cleaned = _re.sub(r'\b(?:PG|CMP)\d+\b', ' ', cleaned, flags=_re.IGNORECASE)
    cleaned = _re.sub(r'\b\d+\s*(?:bước|ngày|dòng|cột|tab|tabs|%)\b', ' ', cleaned, flags=_re.IGNORECASE)
    m_unit = _re.search(
        r'(-?\d+(?:[.,]\d+)*)\s*(tỷ|ty|triệu|trieu|tr|nghìn|nghin|ngàn|ngan|k|vnđ|vnd|đồng|dong|đ)\b',
        cleaned,
        flags=_re.IGNORECASE,
    )
    if m_unit:
        val, stat, _ = parse_currency_value(m_unit.group(0))
        if val is not None and "EXCEPTION" not in stat:
            return float(val)
    m_num = _re.search(r'\b(\d{1,3}(?:[.,]\d{3})+|\d{4,})\b', cleaned)
    if m_num:
        val, stat, _ = parse_currency_value(m_num.group(1))
        if val is not None and "EXCEPTION" not in stat:
            return float(val)
    return None


def _extract_target_channel(text: str):
    import re as _re
    low = str(text or "").lower()
    for pat, label in KNOWN_CHAT_CHANNELS:
        if _re.search(rf'\b{_re.escape(pat)}\b', low):
            return label
    m = _re.search(
        r'(?:kênh(?:\s+trống)?|channel)\s*(?:thành|bằng|là|:|=)\s*([A-Za-zÀ-ỹ0-9\s\-]{2,30})',
        str(text or ""),
        flags=_re.IGNORECASE,
    )
    if m:
        cand = _re.split(r'(?:,|\.|;|\bvà\b|\bcho\b|\brồi\b|\bvới\b)', m.group(1), maxsplit=1, flags=_re.IGNORECASE)[0].strip()
        if cand:
            return cand
    return None


def _record_chat_audit(column: str, record_id: str, raw_val, clean_val, reason: str, method: str) -> None:
    st.session_state.audit_log.append({
        "Tab": "AI_Chatbot",
        "Column": column,
        "Row_Index": 0,
        "Record_ID": str(record_id),
        "Raw_Value": "" if raw_val is None else str(raw_val),
        "Cleaned_Value": "" if clean_val is None else str(clean_val),
        "Reason": reason,
        "Method": method,
        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })


def _sync_tx_intervention_state(df_tx: pd.DataFrame, mark_clean_if_resolved: bool = False) -> None:
    """Đồng bộ bảng Normalized_Transactions, exceptions_list, quality_summary và engine sau khi AI can thiệp."""
    s = st.session_state
    if s.normalized_data is None:
        s.normalized_data = {}
    s.normalized_data["Normalized_Transactions"] = df_tx
    if s.engine is not None:
        s.engine.data["Normalized_Transactions"] = df_tx
        s.exceptions_list = s.engine.exceptions_view

    q = dict(s.quality_summary or {})
    q["Normalized_Transactions_Count"] = int(len(df_tx))
    q["Normalized_Rows_Count"] = int(len(df_tx))
    dup_cnt = int(df_tx.duplicated(subset=["Order_ID"], keep="first").sum()) if (df_tx is not None and not df_tx.empty and "Order_ID" in df_tx.columns) else 0
    q["Duplicate_Rows_Count"] = dup_cnt
    q["Audit_Log_Count"] = len(s.audit_log)
    q["Exceptions_Count"] = len(s.exceptions_list)

    n_pend = len(pending_exceptions())
    if mark_clean_if_resolved and n_pend == 0 and dup_cnt == 0 and not q.get("Quota_Exceeded"):
        q["Status"] = "SUCCESS"
        q["Data_Quality_Score"] = 100.0
        s.cleaning_status = "SUCCESS"
    elif n_pend == 0 and dup_cnt == 0 and s.cleaning_status == "NEEDS_APPROVAL" and not q.get("Quota_Exceeded"):
        q["Status"] = "SUCCESS"
        s.cleaning_status = "SUCCESS"
    s.quality_summary = q


def _format_intervention_report(actions_done: list) -> str:
    """Tạo biên bản phản hồi sau khi Chatbot trực tiếp can thiệp làm sạch / xử lý dữ liệu."""
    s = st.session_state
    lines = ["**🤖 Biên bản Can thiệp Dữ liệu Trực tiếp (AI Agent Action):**"]
    for idx, act in enumerate(actions_done, 1):
        lines.append(f"{idx}. {act}")

    if s.data_status != "CONNECTED":
        lines.append("\n- **Trạng thái phiên:** Đã làm mới về trạng thái chờ nạp dữ liệu mới.")
        return "\n".join(lines)

    q = s.quality_summary or {}
    eng = s.engine
    rep = eng.report_result if (eng is not None and s.process_status == "COMPLETED") else None
    n_norm = q.get("Normalized_Transactions_Count", 0)
    n_pend = len(pending_exceptions())

    lines.append("\n**Trạng thái hệ thống sau can thiệp:**")
    lines.append(
        f"- **Nguồn:** `{s.source_name}` | **Làm sạch:** {vi_status(s.cleaning_status, q)} "
        f"(Điểm chất lượng: **{q.get('Data_Quality_Score', '—')}%**, **{n_norm:,}** giao dịch)"
    )
    lines.append(
        f"- **Xử lý 6 bước:** `{s.process_status}` | **Ngoại lệ chờ HITL:** `{n_pend}` | "
        f"**Verification:** `{s.verification_status}`"
    )
    if rep is not None and not rep.empty:
        g_rev = rep["Gross_Revenue"].sum() if ("Gross_Revenue" in rep.columns and rep["Gross_Revenue"].notna().any()) else rep["Attributed_Revenue"].sum()
        ns = rep["Net_Sales"].sum()
        kpi_str = f"- **KPI cập nhật:** Doanh thu gộp **{fmt_vnd(g_rev)}** | Net Sales **{fmt_vnd(ns)}**"
        if "Net_Contribution" in rep.columns and rep["Net_Contribution"].notna().any():
            kpi_str += f" | Net Contribution **{fmt_vnd(rep['Net_Contribution'].sum())}**"
        lines.append(kpi_str)
    lines.append("\n*Toàn bộ biểu đồ, bảng đối soát và số liệu trên màn hình đã được đồng bộ tự động.*")
    return "\n".join(lines)


def execute_chatbot_data_intervention(question: str):
    """
    Phân tích lệnh chat của người dùng và trực tiếp can thiệp vào dữ liệu/quy trình:
    nạp dữ liệu, làm sạch, xóa trùng, loại bỏ/điền dữ liệu lỗi, sửa/xóa đơn,
    lọc giao dịch, phê duyệt/từ chối HITL, xử lý Quota, chạy 6 bước & kiểm toán.
    Trả về None nếu câu hỏi chỉ là tra cứu thông tin hoặc kiến thức chung.
    """
    import re as _re
    s = st.session_state
    raw_q = (question or "").strip()
    if not raw_q:
        return None
    q = raw_q.lower()
    order_ids = _extract_order_ids_from_text(raw_q)

    # Bảo vệ câu hỏi tra cứu / giải thích thụ động không phải mệnh lệnh thao tác
    passive_markers = [
        "là gì", "tại sao", "vì sao", "làm thế nào", "như thế nào", "cách nào",
        "giải thích", "ý nghĩa", "bao nhiêu", "tóm tắt", "bước tiếp theo", "làm gì tiếp",
    ]
    strong_action_present = any(k in q for k in [
        "làm sạch", "chuẩn hóa", "clean", "quét lỗi",
        "xóa", "xoá", "loại bỏ", "loại trừ", "sửa", "cập nhật", "điền", "gán",
        "chỉ giữ", "nạp ", "tải mẫu", "tải dữ liệu",
        "duyệt tất cả", "duyệt toàn bộ", "duyệt hết", "duyệt nhanh",
        "phê duyệt tất cả", "phê duyệt toàn bộ", "phê duyệt hết",
        "chấp thuận tất cả", "chấp thuận toàn bộ", "từ chối tất cả", "từ chối toàn bộ",
        "chạy 6 bước", "chạy lại 6 bước", "chạy quy trình", "chạy phân tích", "xử lý dữ liệu",
        "cắt ngọn", "mở khóa quota", "cho phép toàn bộ", "allow all",
        "chạy kiểm toán", "chạy verification", "kiểm toán 7", "kiểm chứng dữ liệu",
        "return window", "max_row_limit", "max row limit", "giới hạn dòng",
        "reset dữ liệu", "làm mới phiên dữ liệu",
    ]) or (bool(order_ids) and any(k in q for k in ["duyệt", "phê duyệt", "chấp thuận", "từ chối", "sửa", "đổi", "xóa", "xoá", "bỏ", "cập nhật"]))

    if not strong_action_present:
        return None
    if any(pm in q for pm in passive_markers) and not any(k in q for k in ["ngay", "tất cả", "toàn bộ", "hết"]) and not order_ids and not any(
        k in q for k in ["xóa", "xoá", "sửa", "nạp", "điền", "cập nhật", "chỉ giữ", "cắt ngọn", "mở khóa", "reset"]
    ):
        return None

    actions_done = []

    # 1. Reset toàn bộ phiên dữ liệu
    if any(k in q for k in ["reset dữ liệu", "làm mới phiên dữ liệu", "xóa toàn bộ dữ liệu", "xóa hết dữ liệu"]):
        reset_pipeline()
        s.raw_tabs = None
        s.data_status = "NOT_CONNECTED"
        s.source_name = "Chưa có nguồn dữ liệu"
        s.uploaded_file_id = None
        queue_toast("Chatbot AI đã làm mới phiên dữ liệu", "🔄")
        return _format_intervention_report(["Đã xóa kết quả phiên hiện tại và đặt lại trạng thái **Chưa kết nối dữ liệu**."])

    # 2. Nạp dữ liệu mẫu theo yêu cầu (hoặc tự nạp nếu chưa có dữ liệu)
    wants_load = any(k in q for k in ["nạp", "tải mẫu", "tải dữ liệu", "load ", "chuyển sang bộ", "dùng bộ", "mở bộ"])
    sample_kind = None
    if any(k in q for k in ["lộn xộn", "messy", "gia hòa", "giahoa", "testcase"]):
        sample_kind = "messy"
    elif any(k in q for k in ["ecommerce", "e-commerce", "12 cột"]):
        sample_kind = "ecommerce"
    elif any(k in q for k in ["3 tab", "3 tabs", "chuẩn", "mẫu"]):
        sample_kind = "standard"

    if wants_load and sample_kind:
        load_sample(sample_kind)
        actions_done.append(f"Đã nạp nguồn dữ liệu **{s.source_name}**.")
    elif s.data_status != "CONNECTED":
        auto_kind = sample_kind or (
            "messy" if (any(k in q for k in ["trùng", "lỗi", "ngoại lệ", "duyệt"]) or any(oid.startswith("ORD-20") for oid in order_ids))
            else "standard"
        )
        load_sample(auto_kind)
        actions_done.append(f"Chưa có dữ liệu đang mở — AI tự động nạp **{s.source_name}** để thực thi yêu cầu.")

    # 3. Điều chỉnh cấu hình Return Window / MAX_ROW_LIMIT
    need_reclean = False
    need_process = False
    did_clean_now = False

    m_rw = _re.search(r'(?:return window|hoàn trả|đối soát)\D{0,20}(\d{1,3})\s*ngày', q)
    if not m_rw and "return window" in q:
        m_rw = _re.search(r'(\d{1,3})', q.split("return window", 1)[1])
    if m_rw and ("return window" in q or ("ngày" in q and any(k in q for k in ["đổi", "đặt", "cập nhật", "sửa", "chỉnh"]))):
        new_rw = max(1, min(365, int(m_rw.group(1))))
        s.return_window = new_rw
        if s.engine is not None:
            s.engine.return_window_days = new_rw
        actions_done.append(f"Đã cập nhật **Return Window = {new_rw} ngày**.")
        _record_chat_audit("Return_Window", "CONFIG", "old", new_rw, f"Cập nhật Return Window = {new_rw} ngày qua Chatbot", "AI_CHAT_CONFIG")
        need_process = True

    m_lim = _re.search(r'(?:max_row_limit|max row limit|giới hạn dòng|định mức dòng|quota)\D{0,20}(\d[\d\.,]*)', q)
    if m_lim and any(k in q for k in ["đặt", "đổi", "cập nhật", "sửa", "chỉnh", "nâng", "giảm"]):
        raw_lim = int(_re.sub(r'[^\d]', '', m_lim.group(1)) or MAX_ROW_LIMIT)
        new_lim = max(100, min(500000, raw_lim))
        s.max_row_limit = new_lim
        actions_done.append(f"Đã cập nhật ngưỡng kiểm toán **MAX_ROW_LIMIT = {new_lim:,} dòng**.")
        _record_chat_audit("MAX_ROW_LIMIT", "CONFIG", "old", new_lim, f"Cập nhật MAX_ROW_LIMIT = {new_lim:,} qua Chatbot", "AI_CHAT_CONFIG")
        need_reclean = True

    # 4. Can thiệp chính sách Quota
    if any(k in q for k in ["cắt ngọn", "cắt về", "truncate", "cách ly dòng dư"]):
        run_cleaning(quota_policy="TRUNCATE_TO_QUOTA")
        did_clean_now = True
        need_process = True
        actions_done.append(f"Đã thực thi **Cắt ngọn Quota** về **{int(s.max_row_limit):,}** dòng hợp lệ và đẩy dòng dư sang Exceptions/Quarantine.")
    elif any(k in q for k in ["mở khóa quota", "cho phép toàn bộ", "cho phép xử lý toàn bộ", "xử lý hết dòng", "allow all", "bỏ qua quota"]):
        run_cleaning(quota_policy="ALLOW_ALL_ROWS")
        did_clean_now = True
        need_process = True
        actions_done.append("Đã kích hoạt ngoại lệ **Cho phép xử lý toàn bộ dòng (ALLOW_ALL_ROWS)**.")

    # 5. Đảm bảo đã chạy Data Cleaning trước khi xử lý/can thiệp bảng
    wants_clean = any(k in q for k in ["làm sạch", "chuẩn hóa", "clean", "quét lỗi"])
    wants_process = any(k in q for k in ["xử lý dữ liệu", "xử lý ngay", "chạy 6 bước", "chạy lại 6 bước", "chạy quy trình", "chạy phân tích", "phân tích ngay", "tính lại", "chạy lại", "cập nhật báo cáo"])

    if not did_clean_now and (wants_clean or need_reclean or s.normalized_data is None):
        run_cleaning()
        did_clean_now = True
        q_cur = s.quality_summary or {}
        actions_done.append(
            f"Đã chạy **Làm sạch & Kiểm toán dữ liệu**: Điểm chất lượng **{q_cur.get('Data_Quality_Score', '—')}%**, "
            f"chuẩn hóa **{q_cur.get('Normalized_Transactions_Count', 0):,}** giao dịch, phát hiện **{len(s.exceptions_list)}** ngoại lệ."
        )
        if wants_process or s.process_status == "COMPLETED" or (wants_clean and s.can_proceed_process):
            need_process = True

    df_tx = (s.normalized_data or {}).get("Normalized_Transactions")
    eng = s.engine
    reviewer_name = str(s.user_name or ADMIN_NAME).strip() or ADMIN_NAME
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tx_mutated = False
    cleared_dup_or_invalid = False

    # 6. Can thiệp Làm sạch sâu: Xóa các dòng trùng lặp
    if df_tx is not None and any(k in q for k in ["xóa trùng", "xoá trùng", "xóa các dòng trùng", "xoá các dòng trùng", "loại bỏ trùng", "loại bỏ các dòng trùng", "bỏ trùng", "xóa đơn trùng", "dedup"]):
        before_n = len(df_tx)
        dup_mask = df_tx.duplicated(subset=["Order_ID"], keep="first") if "Order_ID" in df_tx.columns else pd.Series(False, index=df_tx.index)
        if "Is_Duplicate_Copy" in df_tx.columns:
            dup_mask = dup_mask | (df_tx["Is_Duplicate_Copy"] == True)
        removed_dups = int(dup_mask.sum())
        if removed_dups > 0:
            df_tx = df_tx[~dup_mask].reset_index(drop=True)
            tx_mutated = True
        resolved_dup_exc = 0
        if eng is not None:
            for e in eng.exceptions_view:
                if e.get("Error_Type") == "DUPLICATE_ORDER_ID" and e.get("Approval_Status") == "PENDING_REVIEW":
                    e["Approval_Status"] = "REJECTED"
                    e["Reviewer"] = f"{reviewer_name} (AI Chatbot)"
                    e["Review_Time"] = now_str
                    e["Note"] = "Loại bỏ bản sao trùng lặp trực tiếp qua Chatbot AI"
                    resolved_dup_exc += 1
        _record_chat_audit("Order_ID", "DEDUPLICATE", before_n, len(df_tx), f"Xóa {removed_dups} bản ghi trùng lặp (giữ bản ghi đầu)", "AI_CHAT_DEDUPLICATE")
        actions_done.append(f"Đã **loại bỏ {removed_dups} dòng trùng lặp** (`Order_ID` duy nhất còn **{len(df_tx)}** dòng) và đóng **{resolved_dup_exc}** ngoại lệ trùng.")
        cleared_dup_or_invalid = True
        need_process = True

    # 7. Can thiệp Làm sạch sâu: Loại bỏ các dòng lỗi / ngoại lệ bất hợp lệ
    if df_tx is not None and any(k in q for k in ["xóa dòng lỗi", "xoá dòng lỗi", "xóa các dòng lỗi", "xoá các dòng lỗi", "loại bỏ dòng lỗi", "loại bỏ các dòng lỗi", "bỏ dòng lỗi", "xóa bản ghi lỗi", "lọc bỏ lỗi", "xóa dữ liệu lỗi"]):
        before_n = len(df_tx)
        err_oids = set()
        resolved_err_exc = 0
        if eng is not None:
            for e in eng.exceptions_view:
                if e.get("Error_Type") in INVALID_ERROR_TYPES:
                    err_oids.add(str(e.get("Order_ID", "")))
                    if e.get("Approval_Status") == "PENDING_REVIEW":
                        e["Approval_Status"] = "REJECTED"
                        e["Reviewer"] = f"{reviewer_name} (AI Chatbot)"
                        e["Review_Time"] = now_str
                        e["Note"] = "Loại bỏ bản ghi lỗi trực tiếp qua Chatbot AI"
                        resolved_err_exc += 1
        val_series = pd.to_numeric(df_tx["Order_Value"], errors="coerce") if "Order_Value" in df_tx.columns else pd.Series(1.0, index=df_tx.index)
        inv_mask = val_series.isna() | (val_series <= 0)
        if "Order_ID" in df_tx.columns and err_oids:
            inv_mask = inv_mask | df_tx["Order_ID"].astype(str).isin(err_oids)
        removed_err = int(inv_mask.sum())
        if removed_err > 0:
            df_tx = df_tx[~inv_mask].reset_index(drop=True)
            tx_mutated = True
        _record_chat_audit("ALL", "REMOVE_INVALID", before_n, len(df_tx), f"Loại bỏ {removed_err} bản ghi lỗi dữ liệu", "AI_CHAT_REMOVE_INVALID")
        actions_done.append(f"Đã **loại bỏ {removed_err} bản ghi lỗi** (giá trị không hợp lệ/âm/thiếu mã) và đóng **{resolved_err_exc}** ngoại lệ liên quan.")
        cleared_dup_or_invalid = True
        need_process = True

    # 8. Can thiệp từng Đơn hàng theo Order_ID (Xóa đơn / Sửa đơn)
    if df_tx is not None and order_ids:
        is_del_order = any(k in q for k in ["xóa đơn", "xoá đơn", "loại bỏ đơn", "bỏ đơn", "hủy đơn"]) or (
            any(k in q for k in ["xóa ", "xoá ", "loại bỏ"]) and not any(k in q for k in ["sửa", "đổi", "cập nhật", "giá trị", "kênh", "chiến dịch", "duyệt", "từ chối"])
        )
        is_edit_order = any(k in q for k in ["sửa", "chỉnh", "cập nhật", "đổi", "thay"]) and not is_del_order and not any(
            k in q for k in ["duyệt", "phê duyệt", "chấp thuận", "từ chối"]
        )

        if is_del_order:
            before_n = len(df_tx)
            upper_ids = df_tx["Order_ID"].astype(str).str.upper()
            del_mask = upper_ids.isin(order_ids)
            del_cnt = int(del_mask.sum())
            if del_cnt > 0:
                df_tx = df_tx[~del_mask].reset_index(drop=True)
                tx_mutated = True
            if eng is not None:
                for e in eng.exceptions_view:
                    if str(e.get("Order_ID", "")).upper() in order_ids and e.get("Approval_Status") == "PENDING_REVIEW":
                        e["Approval_Status"] = "REJECTED"
                        e["Reviewer"] = f"{reviewer_name} (AI Chatbot)"
                        e["Review_Time"] = now_str
                        e["Note"] = "Xóa đơn hàng trực tiếp qua Chatbot AI"
            _record_chat_audit("Order_ID", ", ".join(order_ids), before_n, len(df_tx), f"Xóa đơn {', '.join(order_ids)}", "AI_CHAT_DELETE_ORDER")
            actions_done.append(f"Đã **xóa {del_cnt} dòng** thuộc đơn hàng `{', '.join(order_ids)}` (bảng chuẩn hóa còn **{len(df_tx)}** đơn).")
            need_process = True

        elif is_edit_order:
            new_val = _parse_chat_vnd_amount(raw_q)
            new_ch = _extract_target_channel(raw_q) if ("kênh" in q or _extract_target_channel(raw_q) is not None) else None
            new_cmps = [c.upper() for c in _re.findall(r'\b(?:PG|CMP)\d+\b', raw_q, flags=_re.IGNORECASE)]
            upper_ids = df_tx["Order_ID"].astype(str).str.upper()
            hit_idxs = df_tx.index[upper_ids.isin(order_ids)].tolist()
            edited_fields = []
            if hit_idxs:
                for ridx in hit_idxs:
                    oid_real = str(df_tx.at[ridx, "Order_ID"])
                    if new_val is not None:
                        old_v = df_tx.at[ridx, "Order_Value"] if "Order_Value" in df_tx.columns else None
                        df_tx.at[ridx, "Order_Value"] = float(new_val)
                        disc = max(0.0, safe_float(df_tx.at[ridx, "Discount_Amount"] if "Discount_Amount" in df_tx.columns else 0.0, 0.0))
                        if "Gross_Sales" in df_tx.columns:
                            df_tx.at[ridx, "Gross_Sales"] = float(new_val) + disc
                        if "COGS" in df_tx.columns and pd.notna(df_tx.at[ridx, "COGS"]):
                            df_tx.at[ridx, "Source_Profit"] = float(new_val) - safe_float(df_tx.at[ridx, "COGS"], 0.0)
                        _record_chat_audit("Order_Value", oid_real, old_v, float(new_val), f"Sửa giá trị đơn {oid_real} qua Chatbot", "AI_CHAT_EDIT_ORDER")
                    if new_ch:
                        old_ch = df_tx.at[ridx, "Channel"] if "Channel" in df_tx.columns else None
                        df_tx.at[ridx, "Channel"] = new_ch
                        _record_chat_audit("Channel", oid_real, old_ch, new_ch, f"Đổi kênh đơn {oid_real} thành {new_ch} qua Chatbot", "AI_CHAT_EDIT_ORDER")
                    if new_cmps:
                        old_cmp = df_tx.at[ridx, "Campaign_List_Str"] if "Campaign_List_Str" in df_tx.columns else ""
                        df_tx.at[ridx, "Campaign_List"] = list(new_cmps)
                        df_tx.at[ridx, "Campaign_List_Str"] = "; ".join(new_cmps)
                        df_tx.at[ridx, "Campaign_Count"] = len(new_cmps)
                        df_tx.at[ridx, "Campaign_Data_Status"] = "AVAILABLE"
                        _record_chat_audit("Campaign_List", oid_real, old_cmp, "; ".join(new_cmps), f"Sửa chiến dịch đơn {oid_real} qua Chatbot", "AI_CHAT_EDIT_ORDER")
                if eng is not None:
                    for e in eng.exceptions_view:
                        if str(e.get("Order_ID", "")).upper() in order_ids and e.get("Error_Type") != "DUPLICATE_ORDER_ID" and e.get("Approval_Status") == "PENDING_REVIEW":
                            e["Approval_Status"] = "APPROVED"
                            e["Reviewer"] = f"{reviewer_name} (AI Chatbot)"
                            e["Review_Time"] = now_str
                            e["Note"] = "Đã cập nhật dữ liệu trực tiếp qua Chatbot AI"
                if "Has_Exception" in df_tx.columns:
                    pending_oids_after = {str(e.get("Order_ID", "")).upper() for e in (eng.exceptions_view if eng is not None else []) if e.get("Approval_Status") == "PENDING_REVIEW"}
                    for ridx in hit_idxs:
                        if str(df_tx.at[ridx, "Order_ID"]).upper() not in pending_oids_after:
                            df_tx.at[ridx, "Has_Exception"] = False
                if new_val is not None:
                    edited_fields.append(f"Giá trị = **{fmt_vnd(new_val)}**")
                if new_ch:
                    edited_fields.append(f"Kênh = **{new_ch}**")
                if new_cmps:
                    edited_fields.append(f"Chiến dịch = **{'; '.join(new_cmps)}**")
                tx_mutated = True
                actions_done.append(f"Đã chỉnh sửa trực tiếp đơn `{', '.join(order_ids)}` ({', '.join(edited_fields) or 'đồng bộ trạng thái'}).")
            else:
                actions_done.append(f"Không tìm thấy mã đơn `{', '.join(order_ids)}` trong bảng dữ liệu hiện tại.")
            need_process = True

    # 9. Điền giá trị thiếu (Kênh / Chiến dịch trống)
    if df_tx is not None and any(k in q for k in ["điền kênh", "thay kênh", "gán kênh", "điền chiến dịch", "gán chiến dịch"]):
        fill_ch = _extract_target_channel(raw_q)
        fill_cmps = [c.upper() for c in _re.findall(r'\b(?:PG|CMP)\d+\b', raw_q, flags=_re.IGNORECASE)]
        if ("kênh" in q or "channel" in q) and fill_ch and "Channel" in df_tx.columns:
            ch_str = df_tx["Channel"].fillna("").astype(str).str.strip()
            miss_mask = ch_str.isin(["", "nan", "None", "null", "Chưa xác định", "Unknown"])
            cnt_fill = int(miss_mask.sum())
            if cnt_fill > 0:
                df_tx.loc[miss_mask, "Channel"] = fill_ch
                tx_mutated = True
            _record_chat_audit("Channel", "FILL_MISSING", "Empty", fill_ch, f"Điền {cnt_fill} ô kênh trống thành {fill_ch}", "AI_CHAT_FILL_MISSING")
            actions_done.append(f"Đã điền **{cnt_fill}** bản ghi thiếu kênh bán thành **{fill_ch}**.")
            need_process = True
        elif ("chiến dịch" in q or "campaign" in q) and fill_cmps and "Campaign_List_Str" in df_tx.columns:
            cmp_str = df_tx["Campaign_List_Str"].fillna("").astype(str).str.strip()
            miss_mask = cmp_str.isin(["", "KHONG_CO", "MISSING_SOURCE_DATA", "nan", "None"])
            cnt_fill = int(miss_mask.sum())
            for ridx in df_tx.index[miss_mask]:
                df_tx.at[ridx, "Campaign_List"] = list(fill_cmps)
                df_tx.at[ridx, "Campaign_List_Str"] = "; ".join(fill_cmps)
                df_tx.at[ridx, "Campaign_Count"] = len(fill_cmps)
                df_tx.at[ridx, "Campaign_Data_Status"] = "AVAILABLE"
                tx_mutated = True
            _record_chat_audit("Campaign_List", "FILL_MISSING", "Empty/KHONG_CO", "; ".join(fill_cmps), f"Gán {cnt_fill} đơn chưa có chiến dịch thành {'; '.join(fill_cmps)}", "AI_CHAT_FILL_MISSING")
            actions_done.append(f"Đã gán chiến dịch **{'; '.join(fill_cmps)}** cho **{cnt_fill}** đơn trống chiến dịch.")
            need_process = True

    # 10. Lọc dữ liệu theo Kênh hoặc Ngưỡng tiền
    if df_tx is not None and not order_ids:
        flt_ch = _extract_target_channel(raw_q)
        flt_amt = _parse_chat_vnd_amount(raw_q)
        before_n = len(df_tx)
        if flt_ch and "Channel" in df_tx.columns and any(k in q for k in ["chỉ giữ", "giữ lại kênh", "lọc kênh", "chỉ lấy kênh"]):
            keep_mask = df_tx["Channel"].astype(str).str.lower().str.contains(flt_ch.lower(), regex=False, na=False)
            cand_df = df_tx[keep_mask].reset_index(drop=True)
            if cand_df.empty:
                actions_done.append(f"Không tìm thấy giao dịch nào thuộc kênh **{flt_ch}** — giữ nguyên **{before_n}** giao dịch hiện tại để tránh rỗng bảng.")
            else:
                df_tx = cand_df
                tx_mutated = True
                _record_chat_audit("Channel", "FILTER_KEEP", before_n, len(df_tx), f"Chỉ giữ lại kênh {flt_ch}", "AI_CHAT_FILTER")
                actions_done.append(f"Đã lọc **chỉ giữ lại kênh {flt_ch}**: còn **{len(df_tx)} / {before_n}** giao dịch.")
                need_process = True
        elif flt_ch and "Channel" in df_tx.columns and any(k in q for k in ["xóa kênh", "xoá kênh", "loại bỏ kênh", "bỏ kênh"]):
            drop_mask = df_tx["Channel"].astype(str).str.lower().str.contains(flt_ch.lower(), regex=False, na=False)
            cand_df = df_tx[~drop_mask].reset_index(drop=True)
            if cand_df.empty:
                actions_done.append(f"Nếu xóa kênh **{flt_ch}** sẽ không còn giao dịch nào — giữ nguyên **{before_n}** giao dịch hiện tại.")
            else:
                df_tx = cand_df
                tx_mutated = True
                _record_chat_audit("Channel", "FILTER_DROP", before_n, len(df_tx), f"Loại bỏ kênh {flt_ch}", "AI_CHAT_FILTER")
                actions_done.append(f"Đã **loại bỏ kênh {flt_ch}**: còn **{len(df_tx)} / {before_n}** giao dịch.")
                need_process = True
        elif flt_amt is not None and any(k in q for k in ["lọc đơn", "lọc các đơn", "giữ đơn", "chỉ giữ", "xóa các đơn", "xoá các đơn", "loại bỏ các đơn"]):
            vals = pd.to_numeric(df_tx["Order_Value"], errors="coerce").fillna(0.0)
            if any(k in q for k in ["dưới", "nhỏ hơn", "<"]):
                keep_mask = vals >= flt_amt if any(k in q for k in ["xóa", "xoá", "loại bỏ"]) else vals < flt_amt
            else:
                keep_mask = vals < flt_amt if any(k in q for k in ["xóa", "xoá", "loại bỏ"]) else vals >= flt_amt
            cand_df = df_tx[keep_mask].reset_index(drop=True)
            if cand_df.empty:
                actions_done.append(f"Không còn giao dịch nào đạt điều kiện lọc theo ngưỡng **{fmt_vnd(flt_amt)}** — giữ nguyên **{before_n}** giao dịch hiện tại.")
            else:
                df_tx = cand_df
                tx_mutated = True
                _record_chat_audit("Order_Value", "FILTER_AMOUNT", before_n, len(df_tx), f"Lọc giao dịch theo ngưỡng {fmt_vnd(flt_amt)}", "AI_CHAT_FILTER")
                actions_done.append(f"Đã lọc dữ liệu theo ngưỡng **{fmt_vnd(flt_amt)}**: còn **{len(df_tx)} / {before_n}** giao dịch.")
                need_process = True

    if tx_mutated and df_tx is not None:
        # Khóa mọi ngoại lệ còn PENDING của những Order_ID không còn trong bảng
        if eng is not None and "Order_ID" in df_tx.columns:
            rem_ids = set(df_tx["Order_ID"].astype(str))
            for e in eng.exceptions_view:
                if e.get("Approval_Status") == "PENDING_REVIEW" and str(e.get("Order_ID", "")) not in rem_ids:
                    e["Approval_Status"] = "REJECTED"
                    e["Reviewer"] = f"{reviewer_name} (AI Chatbot)"
                    e["Review_Time"] = now_str
                    e["Note"] = "Bản ghi đã được loại bỏ khỏi bảng chuẩn hóa qua Chatbot AI"
        _sync_tx_intervention_state(df_tx, mark_clean_if_resolved=cleared_dup_or_invalid)

    # 11. Chạy Quy trình 6 bước khi có yêu cầu hoặc sau khi biến đổi dữ liệu
    if (wants_process or need_process) and s.normalized_data is not None:
        if s.can_proceed_process:
            res = run_process()
            if res.get("status") == "COMPLETED":
                actions_done.append("Đã chạy lại **Quy trình Xử lý 6 Bước** & cập nhật toàn bộ biểu đồ, KPI, Waterfall.")
            else:
                actions_done.append(f"Quy trình 6 bước dừng tại `{res.get('failed_step')}`: {res.get('message')}")
        else:
            actions_done.append("Không thể chạy 6 bước vì dữ liệu đang có lỗi chặn từ bước Làm sạch.")

    # 12. Phê duyệt / Từ chối ngoại lệ HITL
    did_verify = False
    if s.engine is not None:
        wants_approve_all = any(k in q for k in [
            "duyệt tất cả", "duyệt toàn bộ", "duyệt hết", "duyệt nhanh",
            "phê duyệt tất cả", "phê duyệt toàn bộ", "phê duyệt hết", "phê duyệt hitl", "duyệt hitl",
            "chấp thuận tất cả", "chấp thuận toàn bộ", "chấp thuận hết", "duyệt mọi ngoại lệ",
        ])
        wants_reject_all = any(k in q for k in [
            "từ chối tất cả", "từ chối toàn bộ", "từ chối hết", "loại trừ tất cả", "loại bỏ tất cả ngoại lệ",
        ])

        if wants_approve_all:
            if s.process_status != "COMPLETED" and s.can_proceed_process:
                run_process()
            cnt_app = quick_approve_all_and_verify()
            did_verify = True
            actions_done.append(f"Đã **phê duyệt nhanh {cnt_app} hồ sơ HITL** và chạy **Verification Gate ({s.verification_status})**.")
        elif wants_reject_all:
            if s.process_status != "COMPLETED" and s.can_proceed_process:
                run_process()
            cnt_rej = 0
            for exc in list(s.engine.exceptions_view):
                if exc.get("Approval_Status") == "PENDING_REVIEW":
                    ok, _ = s.engine.resolve_exception(
                        exc["Order_ID"], "REJECT", "Trưởng phòng Marketing", reviewer_name,
                        "Từ chối / loại trừ toàn bộ ngoại lệ trực tiếp qua Chatbot AI",
                        error_type=exc.get("Error_Type"),
                    )
                    if ok:
                        cnt_rej += 1
            s.exceptions_list = s.engine.exceptions_view
            vr = s.engine.run_verification()
            s.verification_result = vr
            s.verification_status = vr.get("overall_status", "NOT_RUN")
            did_verify = True
            actions_done.append(f"Đã **từ chối/loại trừ {cnt_rej} hồ sơ ngoại lệ** và cập nhật **Verification ({s.verification_status})**.")
        elif order_ids and any(k in q for k in ["duyệt", "phê duyệt", "chấp thuận", "từ chối"]):
            act_code = "REJECT" if "từ chối" in q else "APPROVE"
            act_lbl = "Từ chối" if act_code == "REJECT" else "Chấp thuận"
            done_oids = []
            for oid in order_ids:
                ok, _ = s.engine.resolve_exception(
                    oid, act_code, "Trưởng phòng Marketing", reviewer_name,
                    f"{act_lbl} ngoại lệ trực tiếp qua Chatbot AI",
                )
                if ok:
                    done_oids.append(oid)
            if done_oids:
                s.exceptions_list = s.engine.exceptions_view
                s.process_status = "COMPLETED" if s.engine.report_result is not None else s.process_status
                s.verification_result = None
                s.verification_status = "NOT_RUN"
                actions_done.append(f"Đã **{act_lbl}** ngoại lệ cho đơn `{', '.join(done_oids)}`.")
            else:
                actions_done.append(f"Không có ngoại lệ nào cho mã `{', '.join(order_ids)}` để {act_lbl.lower()}.")

    # 13. Chạy Kiểm toán Verification Suite
    if s.engine is not None and not did_verify and any(k in q for k in ["chạy kiểm toán", "kiểm toán ngay", "chạy verification", "kiểm toán 7", "kiểm chứng dữ liệu", "kiểm chứng ngay"]):
        if s.process_status != "COMPLETED" and s.can_proceed_process:
            run_process()
        if s.process_status == "COMPLETED":
            vr = s.engine.run_verification()
            s.verification_result = vr
            s.verification_status = vr.get("overall_status", "NOT_RUN")
            actions_done.append(
                f"Đã chạy **Verification Suite (7 phép kiểm toán)**: **{s.verification_status}** "
                f"({vr.get('pass_count', 0)} đạt, {vr.get('na_count', 0)} N/A, {vr.get('fail_count', 0)} lỗi)."
            )

    if not actions_done:
        return None
    queue_toast("Trợ lý AI đã trực tiếp cập nhật dữ liệu & hệ thống!", "🤖")
    return _format_intervention_report(actions_done)


def generate_ai_reply(question: str) -> str:
    """Trả lời câu hỏi hoặc thực thi trực tiếp thao tác làm sạch / xử lý dữ liệu khi có lệnh yêu cầu."""
    intervention_reply = execute_chatbot_data_intervention(question)
    if intervention_reply is not None:
        return intervention_reply

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
        total_gross_rev = rep["Gross_Revenue"].sum() if ("Gross_Revenue" in rep.columns and rep["Gross_Revenue"].notna().any()) else total_rev
        total_net = rep["Net_Sales"].sum()
        ans = [
            f"**Tóm tắt số liệu thực tế ({s.source_name}):**",
            f"- **Tổng Doanh thu gộp (Gross Revenue):** {fmt_vnd(total_gross_rev)}",
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

    # 4. Mọi câu hỏi tự do & kiến thức đa lĩnh vực: dùng bộ não ChatGPT đa tầng kèm ngữ cảnh phiên
    ctx = _build_live_context_summary()
    return _call_llm_brain(question, ctx)


def _render_visitor_popover(visitors: list) -> None:
    u_name = st.session_state.user_name
    with st.popover(f"👤 {u_name} ({len(visitors)} online)", width="stretch"):
        st.markdown("**Định danh người đang truy cập**")
        with st.form("visitor_profile_form", border=False):
            new_name = st.text_input("Tên hiển thị của bạn", value=u_name, placeholder="Nhập tên của bạn...")
            role_opts = ["Admin account", "Trưởng phòng Marketing", "Quản trị viên", "Chuyên viên Phân tích", "Khách truy cập"]
            cur_role = st.session_state.user_role if st.session_state.user_role in role_opts else role_opts[0]
            new_role = st.selectbox("Vai trò", role_opts, index=role_opts.index(cur_role))
            saved = st.form_submit_button("Cập nhật tên hiển thị", type="primary", width="stretch")
        if saved and new_name.strip():
            st.session_state.user_name = new_name.strip()[:50]
            st.session_state.user_role = new_role
            sync_current_visitor()
            queue_toast(f"Đã cập nhật hiển thị: {st.session_state.user_name}")
            st.rerun()

        st.divider()
        st.markdown(f"**Đang truy cập trên trang ({len(visitors)})**")
        for v in visitors[:10]:
            is_me = " *(Bạn)*" if v["visitor_id"] == st.session_state.visitor_id else ""
            st.caption(f"🟢 **{v['name']}**{is_me} • {v['role']} — *{v['page']}* ({v['last_seen_str']})")


def render_header(title: str, subtitle: str, show_chatbot: bool = True) -> None:
    visitors = sync_current_visitor()
    u_name = st.session_state.user_name
    u_role = st.session_state.user_role
    u_init = get_initials(u_name)
    source = st.session_state.source_name if st.session_state.data_status == "CONNECTED" else "Chưa kết nối nguồn dữ liệu"
    n_pend = len(pending_exceptions())
    bell_badge = f'<span class="bell-dot">{n_pend}</span>' if n_pend else ""

    html("""
    <div class="sb-topbar">
        <div style="display:flex;align-items:center;gap:18px;flex-wrap:wrap;">
            <span><b>Hotline:</b> 0978632574</span>
            <span><b>Hỗ trợ:</b> audit@dataforge.ai</span>
            <span><b>Hệ thống:</b> Enterprise BI &amp; Audit Suite v2.5</span>
        </div>
        <div style="display:flex;align-items:center;gap:12px;">
            <span class="sb-ttag">HITL READY</span>
            <div class="sb-tsoc">
                <i>DF</i><i>BI</i><i>AI</i><i>SA</i>
            </div>
        </div>
    </div>
    """)

    bar_html = f"""
    <div class="top-glass-bar" style="margin-bottom:0;">
        <div class="top-search"><span>🔍 Tìm kiếm báo cáo, dashboard hoặc đặt câu hỏi...</span><span class="top-search-kbd">Ctrl + K</span></div>
        <div class="top-right">
            <span class="badge ok">🟢 {len(visitors)} đang online</span>
            <span class="source-chip" title="{source}">Nguồn: {source}</span>
            <div class="bell-wrap" title="Ngoại lệ chờ duyệt">🔔{bell_badge}</div>
            <div class="profile-chip">
                <div class="avatar">{u_init}</div>
                <div><div class="p-name">{u_name}</div><div class="p-role">{u_role}</div></div>
            </div>
        </div>
    </div>
    """
    theme_icon = "☀️ Sáng" if st.session_state.get("ui_theme", "light") == "dark" else "🌙 Tối"
    if show_chatbot:
        c_bar, c_thm, c_vis, c_bot = st.columns([3.0, 0.78, 1.52, 0.96], vertical_alignment="center")
        with c_bar:
            html(bar_html)
        with c_thm:
            st.button(theme_icon, key="btn_toggle_theme", help="Chuyển chế độ Sáng / Tối", width="stretch", on_click=_toggle_ui_theme)
        with c_vis:
            _render_visitor_popover(visitors)
        with c_bot:
            with st.popover("🤖 Trợ lý AI", width="stretch"):
                st.markdown("**Trợ lý AI Data Forge**")
                st.caption(f"Nguồn: {source} • {vi_status(st.session_state.cleaning_status, st.session_state.quality_summary)}")
                q1, q2 = st.columns(2)
                q3, q4 = st.columns(2)
                q5, q6 = st.columns(2)
                quick_prompts = [
                    (q1, "⚡ Làm sạch & Xử lý", "Làm sạch dữ liệu và chạy quy trình 6 bước ngay", "ai_q1"),
                    (q2, "✅ Duyệt HITL & Audit", "Phê duyệt tất cả ngoại lệ và chạy kiểm toán Verification", "ai_q2"),
                    (q3, "🧹 Xóa trùng & Lỗi", "Xóa các dòng trùng lặp, loại bỏ dòng lỗi và chạy lại phân tích", "ai_q3"),
                    (q4, "📊 Tóm tắt KPI", "Tóm tắt doanh thu & lợi nhuận", "ai_q4"),
                    (q5, "🔍 Xem ngoại lệ", "Giải thích ngoại lệ cần duyệt", "ai_q5"),
                    (q6, "🧭 Bước tiếp theo?", "Tôi cần làm gì tiếp theo?", "ai_q6"),
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
                    user_q = st.text_input(
                        "Hỏi hoặc ra lệnh cho Trợ lý AI...",
                        placeholder="VD: Xóa trùng, sửa đơn ORD-2001 5tr, hoặc hỏi KPI...",
                        label_visibility="collapsed",
                    )
                    send_clicked = st.form_submit_button("Gửi yêu cầu", type="primary", width="stretch")
                if send_clicked and user_q.strip():
                    st.session_state.chat_history.append({"role": "user", "content": user_q.strip()})
                    st.session_state.chat_history.append({"role": "assistant", "content": generate_ai_reply(user_q.strip())})
                    st.rerun()
                if st.button("Làm mới hội thoại", key="ai_clear", width="stretch"):
                    st.session_state.chat_history = [dict(DEFAULT_CHAT_GREETING)]
                    st.rerun()
                with st.expander("⚙️ Cấu hình AI (Tùy chọn API Key)", expanded=False):
                    st.caption("Mặc định đã kết nối ChatGPT Cloud miễn phí. Có thể nhập key riêng nếu muốn:")
                    st.text_input("OpenAI API Key", type="password", key="custom_openai_key", placeholder="sk-...")
                    st.text_input("Gemini API Key", type="password", key="custom_gemini_key", placeholder="AIza...")
    else:
        c_bar, c_thm, c_vis = st.columns([3.70, 0.78, 1.52], vertical_alignment="center")
        with c_bar:
            html(bar_html)
        with c_thm:
            st.button(theme_icon, key="btn_toggle_theme", help="Chuyển chế độ Sáng / Tối", width="stretch", on_click=_toggle_ui_theme)
        with c_vis:
            _render_visitor_popover(visitors)

    with st.container(key="top_pill_nav"):
        st.radio(
            "Điều hướng",
            PAGES,
            key="nav_page",
            horizontal=True,
            label_visibility="collapsed",
            format_func=lambda p: NAV_SHORT_LABELS.get(p, p),
            on_change=_on_top_nav_change,
        )


def badge(state: str, text: str) -> str:
    return f'<span class="badge {state}">{text}</span>'


def empty_state(message: str, button_label: str, page: str, key: str) -> None:
    with st.container(key=f"card_empty_{key}"):
        st.info(message)
        next_step(button_label, page, key=f"btn_empty_{key}")


# ==============================================================================
# SIDEBAR — KHU VỰC NHẬN DIỆN THƯƠNG HIỆU ĐỎ RƯỢU VANG (#6D1B29 → #4B111D)
# ==============================================================================
with st.sidebar:
    html("""
    <div class="brand-red-banner">
        <div class="brand-svg-mark">
            <svg width="40" height="40" viewBox="0 0 42 42" fill="none">
                <defs>
                    <linearGradient id="dfLogoGrad" x1="4" y1="4" x2="38" y2="38" gradientUnits="userSpaceOnUse">
                        <stop offset="0%" stop-color="#FF7B73"/>
                        <stop offset="55%" stop-color="#C21F20"/>
                        <stop offset="100%" stop-color="#7C1F27"/>
                    </linearGradient>
                </defs>
                <rect x="2" y="2" width="38" height="38" rx="12" fill="rgba(255,255,255,0.12)" stroke="rgba(255,248,240,0.22)" stroke-width="1"/>
                <path d="M12 10H22C28.5 10 32.5 14 32.5 21C32.5 28 28.5 32 22 32H12V10Z" fill="url(#dfLogoGrad)"/>
                <path d="M16.5 15.5V26.5H21.2C24.8 26.5 26.8 24.4 26.8 21C26.8 17.6 24.8 15.5 21.2 15.5H16.5Z" fill="#5B1522"/>
            </svg>
        </div>
        <div>
            <div class="brand-red-title">DATA FORGE</div>
            <div class="brand-red-sub">Enterprise BI SaaS</div>
        </div>
    </div>
    """)

    s = st.session_state

    _q_cur = s.quality_summary
    ds = badge("ok", "ĐÃ KẾT NỐI") if s.data_status == "CONNECTED" else (badge("fail", "LỖI") if s.data_status == "FAILED" else badge("idle", "CHƯA KẾT NỐI"))
    if s.cleaning_status == "SUCCESS":
        cl = badge("ok", vi_status("SUCCESS"))
    elif s.cleaning_status == "QUOTA_WARNING":
        cl = badge("warn", vi_status("QUOTA_WARNING", _q_cur))
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
    _acc_init = get_initials(s.user_name)
    html(f"""
    <div class="side-progress">
        <div class="side-progress-title">Tiến độ Workflow</div>
        <div class="side-row"><span>Nguồn dữ liệu</span>{ds}</div>
        <div class="side-row"><span>Làm sạch</span>{cl}</div>
        <div class="side-row"><span>Process 6 bước</span>{pr}</div>
        <div class="side-row"><span>Phê duyệt HITL</span>{ap}</div>
        <div class="side-row"><span>Verification</span>{vr}</div>
    </div>
    <div class="side-promo-red">
        <div class="side-promo-head">
            <div class="side-promo-title">Khai thác dữ liệu –<br>Kiến tạo giá trị số</div>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#E9A096" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;opacity:0.9;">
                <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"></polyline>
                <polyline points="16 7 22 7 22 13"></polyline>
            </svg>
        </div>
        <div class="side-promo-sub">Cùng Data Forge AI vươn xa hơn</div>
    </div>
    <div class="side-account-card">
        <div class="side-acc-ava">{_acc_init}</div>
        <div>
            <div class="side-acc-name">{s.user_name}</div>
            <div class="side-acc-role">{s.user_role}</div>
        </div>
    </div>
    """)

# Thông báo toast sau khi thao tác (hiển thị một lần)
if st.session_state.pending_toast:
    _msg, _icon = st.session_state.pending_toast
    st.toast(_msg, icon=_icon)
    st.session_state.pending_toast = None

page = st.session_state.nav_page


def generate_business_context_ai_consultation(industry: str, extra_info: str, questions_text: str) -> str:
    """Tạo tư vấn định hướng từ Data Forge AI dựa trên bối cảnh doanh nghiệp và câu hỏi người dùng."""
    lines = [q.strip() for q in (questions_text or "").splitlines() if q.strip()][:8]
    if not lines:
        lines = ["Đánh giá hiệu quả doanh thu và chi phí đa kênh tổng thể"]

    q_analysis = []
    for idx, q in enumerate(lines, 1):
        q_lower = q.lower()
        if any(w in q_lower for w in ["kênh", "channel", "sàn", "shopee", "lazada", "tiktok"]):
            matched_kpi = "Doanh thu phân bổ đa điểm chạm (Attributed Net Sales) theo Channel"
            dim = "Mô hình First-touch / Last-touch / Linear & Tỷ lệ hoàn đơn thực tế theo từng sàn"
        elif any(w in q_lower for w in ["chiến dịch", "campaign", "chi phí", "ngân sách", "quảng cáo"]):
            matched_kpi = "Chi phí hoạt động phân bổ ABC (Direct Cost + Allocated Overhead) & Net Contribution"
            dim = "Chi phí trực tiếp chiến dịch kết hợp phân bổ chi phí gián tiếp ABC 3 tầng"
        elif any(w in q_lower for w in ["hoàn", "return", "hủy"]):
            matched_kpi = "Tỷ lệ hoàn hàng (Return Rate %) & Doanh thu hoàn trả (Attributed Return)"
            dim = "Chu kỳ đối soát 14–30 ngày (Return Window) bảo vệ lợi nhuận gộp thực tế"
        elif any(w in q_lower for w in ["sản phẩm", "product", "sku", "mặt hàng"]):
            matched_kpi = "Biên đóng góp theo nhóm sản phẩm (Product Contribution Margin)"
            dim = "Đánh giá SKU chủ lực, tỷ suất sinh lời ròng và chi phí đóng gói"
        elif any(w in q_lower for w in ["lợi nhuận", "profit", "roi", "roas"]):
            matched_kpi = "Lợi nhuận đóng góp ròng (Net Contribution) & Tỷ suất ROI/ROAS"
            dim = "Đối soát 7 bất biến tài chính, loại bỏ doanh thu ảo trước ghi nhận"
        else:
            matched_kpi = "Chỉ số hiệu quả tổng hợp (Composite Executive Scorecard)"
            dim = "Phân tích xu hướng biến động và kiểm soát thất thoát dòng tiền"

        q_analysis.append(f"**Câu hỏi {idx}:** *\"{q}\"*\n  - 🎯 **Chỉ số đo lường đề xuất:** {matched_kpi}\n  - 💡 **Phương pháp đối soát:** {dim}")

    analysis_bullets = "\n\n".join(q_analysis)
    extra_note = f"\n- **Đặc thù bổ sung:** *{extra_info.strip()}*" if extra_info.strip() else ""

    advice = f"""### 🎯 Định hướng Chiến lược Phân tích & Kiểm toán Dữ liệu

Chào bạn! Dựa trên bối cảnh doanh nghiệp:
- **Loại hình kinh doanh:** **{industry.strip()}**{extra_note}
- **Số câu hỏi trọng tâm:** **{len(lines)} vấn đề** cần giải quyết.

---

#### 🧭 Ánh xạ Câu hỏi vào Chỉ số Quản trị & Mô hình Dữ liệu:
{analysis_bullets}

---

#### 🛡️ Khuyến nghị từ Chuyên gia Kiểm toán Data Forge:
1. **Kiểm toán Hoàn hàng (Returns Reconciliation):** Đối với ngành **{industry.strip()}**, tỷ lệ hoàn và hủy đơn có thể làm sai lệch 15–30% doanh thu ghi nhận. Quy trình 6 bước sẽ tự động đối soát trường `Return_Date` và chỉ ghi nhận `Net Sales` thực nhận.
2. **Phân bổ Chi phí ABC (Activity-Based Costing):** Để trả lời chính xác chi phí chiến dịch nào cao nhất và hiệu quả nhất, hệ thống sẽ tự động phân bổ chi phí quảng cáo trực tiếp cùng định phí vận hành theo tỷ trọng đơn hàng.
3. **Chốt chặn Quota 20,000 dòng:** Đảm bảo toàn bộ dữ liệu tải lên được kiểm toán 7 bất biến tài chính không bị xáo trộn.

> [!TIP]
> 💡 Toàn bộ bối cảnh này đã được đồng bộ vào **Trợ lý AI Data Forge**. Khi bạn tiến hành nạp bảng tính và chạy phân tích, các báo cáo sẽ tự động làm nổi bật câu trả lời cho các vấn đề trên!
"""
    return advice


def render_business_context_section() -> None:
    """Hiển thị khối Bối cảnh doanh nghiệp & Trao đổi yêu cầu với AI trên trang Kết Nối chuẩn theo thiết kế."""
    with st.container(key="card_biz_context"):
        html("""
        <div class="biz-head">
            <div class="biz-icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2D6A4F" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                    <line x1="16" y1="13" x2="8" y2="13"></line>
                    <line x1="16" y1="17" x2="8" y2="17"></line>
                    <polyline points="10 9 9 9 8 9"></polyline>
                </svg>
            </div>
            <div>
                <div class="biz-title">Bối cảnh doanh nghiệp</div>
                <div class="biz-sub">Câu hỏi của bạn định hướng việc chọn chỉ số và đọc kết quả.</div>
            </div>
        </div>
        """)

        industry_val = st.text_input(
            "Loại hình doanh nghiệp *",
            value=st.session_state.get("biz_industry", ""),
            placeholder="Ví dụ: Bán lẻ thời trang, SaaS B2B, dịch vụ logistics",
            key="input_biz_industry"
        )
        st.session_state.biz_industry = industry_val

        extra_val = st.text_area(
            "Thông tin bổ sung  ·  không bắt buộc",
            value=st.session_state.get("biz_extra_info", ""),
            placeholder="Ví dụ: Hai chi nhánh, đang đánh giá hiệu quả quý I",
            height=70,
            key="input_biz_extra_info"
        )
        st.session_state.biz_extra_info = extra_val

        questions_val = st.text_area(
            "Vấn đề cần phân tích *",
            value=st.session_state.get("biz_questions", ""),
            placeholder="Doanh thu theo kênh nào cao nhất?\nChi phí theo chiến dịch nào cao nhất?",
            height=90,
            key="input_biz_questions"
        )
        st.session_state.biz_questions = questions_val
        st.caption("Nhập tối đa 8 câu hỏi, mỗi câu một dòng.")

    # Khối 2: Trao đổi yêu cầu với AI
    with st.container(key="card_biz_ai_bar"):
        c_desc, c_btn = st.columns([3.2, 1.3], vertical_alignment="center")
        with c_desc:
            html("""
            <div>
                <div style="font-weight:700;font-size:16px;color:#1A1A1A;">Trao đổi yêu cầu với AI</div>
                <div style="font-size:13px;color:#666;margin-top:3px;">Xem cách AI hiểu yêu cầu và bổ sung thông tin trước khi phân tích.</div>
            </div>
            """)
        with c_btn:
            consult_clicked = st.button("✦ Trao đổi yêu cầu", key="btn_biz_ai_consult", width="stretch")

    if consult_clicked:
        if not industry_val.strip() or not questions_val.strip():
            st.warning("Vui lòng nhập Loại hình doanh nghiệp và ít nhất một Vấn đề cần phân tích (các mục có dấu *).")
        else:
            with st.spinner("Data Forge AI đang phân tích bối cảnh và định hướng chỉ số..."):
                consultation = generate_business_context_ai_consultation(industry_val, extra_val, questions_val)
                st.session_state.biz_ai_feedback = consultation
                # Đồng bộ vào lịch sử Chatbot
                user_msg = f"**Bối cảnh doanh nghiệp:** {industry_val}" + (f" ({extra_val})" if extra_val.strip() else "") + f"\n**Vấn đề cần phân tích:**\n{questions_val}"
                st.session_state.chat_history.append({"role": "user", "content": user_msg})
                st.session_state.chat_history.append({"role": "assistant", "content": consultation})
                queue_toast("AI đã tiếp nhận và phân tích bối cảnh thành công!", "✨")
                st.rerun()

    # Hiển thị phản hồi tư vấn của AI nếu có
    if st.session_state.get("biz_ai_feedback"):
        with st.container(key="card_biz_ai_feedback"):
            html("""
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                <div style="display:flex;align-items:center;gap:10px;">
                    <span style="font-size:20px;">✨</span>
                    <b style="font-family:'Baloo 2',sans-serif;font-size:17px;color:#1A1A1A;">Định hướng Phân tích & Kiểm toán từ AI</b>
                </div>
                <span class="badge ok">Đã đồng bộ vào Chatbot</span>
            </div>
            """)
            st.markdown(st.session_state.biz_ai_feedback)
            c_f1, c_f2 = st.columns(2)
            c_f1.caption("💡 Bạn có thể hỏi thêm chi tiết bất cứ lúc nào qua biểu tượng **🤖 Trợ lý AI** ở góc trên.")
            if c_f2.button("Thu gọn phản hồi AI", key="btn_close_ai_fb"):
                st.session_state.biz_ai_feedback = None
                st.rerun()


def _svg_sparkline(values, stroke_hex: str = "#C21F20", fill_hex: str = "rgba(194,31,32,0.16)") -> str:
    """Render a compact inline SVG area+line sparkline from real series data."""
    nums = [safe_float(v, 0.0) for v in (values or [])]
    if len(nums) == 0:
        nums = [0.0, 0.0, 0.0, 0.0]
    elif len(nums) == 1:
        nums = [nums[0] * 0.92, nums[0] * 0.97, nums[0], nums[0]]
    w, h, pad_x, pad_y = 92, 32, 3, 4
    mn, mx = min(nums), max(nums)
    span = (mx - mn) if (mx - mn) > 1e-9 else 1.0
    n = len(nums)
    pts = []
    for idx, val in enumerate(nums):
        x = pad_x + (idx / max(1, n - 1)) * (w - 2 * pad_x)
        norm = (val - mn) / span if (mx - mn) > 1e-9 else 0.5
        y = (h - pad_y) - norm * (h - 2 * pad_y)
        pts.append((round(x, 1), round(y, 1)))
    poly_pts = " ".join(f"{x},{y}" for x, y in pts)
    area_pts = f"{pts[0][0]},{h} " + poly_pts + f" {pts[-1][0]},{h}"
    lx, ly = pts[-1]
    return (
        f'<svg class="kpi-spark" viewBox="0 0 {w} {h}" preserveAspectRatio="none" aria-hidden="true">'
        f'<polygon points="{area_pts}" fill="{fill_hex}" />'
        f'<polyline points="{poly_pts}" fill="none" stroke="{stroke_hex}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />'
        f'<circle cx="{lx}" cy="{ly}" r="2.8" fill="{stroke_hex}" stroke="#FFFFFF" stroke-width="1.2" />'
        f'</svg>'
    )


def _strip_md_for_chip(text: str) -> str:
    plain = re.sub(r"\*\*(.*?)\*\*", r"\1", str(text or ""))
    plain = re.sub(r"`([^`]*)`", r"\1", plain)
    return _html.escape(" ".join(plain.split())[:220])


def render_hero_banner_and_ai_assistant():
    """Render Enterprise Data Forge Banner + Standalone Warm-Cream AI Assistant Card."""
    b_col, a_col = st.columns([1.82, 1.0], gap="medium")

    with b_col:
        with st.container(key="card_hero_banner"):
            bl, br = st.columns([1.12, 0.98], gap="small")
            with bl:
                html("""
                <div class="df-banner-eyebrow">BUSINESS INTELLIGENCE PLATFORM</div>
                <div class="df-banner-title">Data Forge</div>
                <div class="df-banner-sub">Phân tích dữ liệu thông minh, Kiến tạo quyết định vượt trội</div>
                """)
                if st.button("Bắt đầu khám phá →", key="hero_banner_explore", type="primary"):
                    if st.session_state.data_status != "CONNECTED":
                        go_to(PAGES[1])
                    elif not has_report():
                        go_to(PAGES[3])
                    else:
                        go_to(PAGES[6])
                    st.rerun()
            with br:
                html("""
                <div class="df-banner-art">
                    <svg viewBox="0 0 280 185" width="100%" height="185" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                        <defs>
                            <linearGradient id="dfCylTop" x1="0" y1="0" x2="1" y2="1">
                                <stop offset="0%" stop-color="#FFE6DF"/><stop offset="100%" stop-color="#E9A096"/>
                            </linearGradient>
                            <linearGradient id="dfCylBody" x1="0" y1="0" x2="1" y2="0">
                                <stop offset="0%" stop-color="#C21F20"/><stop offset="55%" stop-color="#8C2E2E"/><stop offset="100%" stop-color="#4B111D"/>
                            </linearGradient>
                            <linearGradient id="dfGlass" x1="0" y1="0" x2="1" y2="1">
                                <stop offset="0%" stop-color="rgba(255,255,255,0.42)"/><stop offset="100%" stop-color="rgba(255,255,255,0.12)"/>
                            </linearGradient>
                        </defs>
                        <!-- Isometric platform -->
                        <ellipse cx="145" cy="156" rx="108" ry="20" fill="rgba(255,248,240,0.16)" stroke="rgba(255,248,240,0.34)" stroke-width="1.2"/>
                        <ellipse cx="145" cy="150" rx="84" ry="14" fill="rgba(255,255,255,0.20)"/>
                        <!-- Floating back bar chart panel -->
                        <rect x="20" y="34" width="102" height="72" rx="12" fill="url(#dfGlass)" stroke="rgba(255,255,255,0.45)" stroke-width="1.2"/>
                        <rect x="34" y="66" width="10" height="26" rx="3" fill="#FFFFFF" fill-opacity="0.9"/>
                        <rect x="50" y="54" width="10" height="38" rx="3" fill="#FFE6DF" fill-opacity="0.95"/>
                        <rect x="66" y="60" width="10" height="32" rx="3" fill="#FFFFFF" fill-opacity="0.88"/>
                        <rect x="82" y="46" width="10" height="46" rx="3" fill="#E9A096"/>
                        <rect x="98" y="52" width="10" height="40" rx="3" fill="#FFFFFF"/>
                        <!-- Floating top-right line trend panel -->
                        <rect x="148" y="16" width="114" height="68" rx="12" fill="url(#dfGlass)" stroke="rgba(255,255,255,0.45)" stroke-width="1.2"/>
                        <polyline points="162,64 182,50 202,55 224,36 248,28" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                        <circle cx="182" cy="50" r="3" fill="#FFE6DF"/><circle cx="224" cy="36" r="3" fill="#FFE6DF"/><circle cx="248" cy="28" r="3.6" fill="#FFFFFF"/>
                        <!-- 3D stacked database cylinders -->
                        <path d="M106 118 v22 c0 8 18 14 40 14 s40 -6 40 -14 v-22 z" fill="url(#dfCylBody)" stroke="rgba(255,230,223,0.45)"/>
                        <ellipse cx="146" cy="118" rx="40" ry="13" fill="url(#dfCylTop)"/>
                        <path d="M106 94 v20 c0 8 18 14 40 14 s40 -6 40 -14 v-20 z" fill="url(#dfCylBody)" stroke="rgba(255,230,223,0.45)"/>
                        <ellipse cx="146" cy="94" rx="40" ry="13" fill="url(#dfCylTop)"/>
                        <path d="M106 70 v20 c0 8 18 14 40 14 s40 -6 40 -14 v-20 z" fill="url(#dfCylBody)" stroke="rgba(255,230,223,0.55)"/>
                        <ellipse cx="146" cy="70" rx="40" ry="13" fill="#FFF8F0" stroke="#E9A096" stroke-width="1.2"/>
                        <!-- Sparkle particles -->
                        <circle cx="248" cy="114" r="3.5" fill="#FFE6DF" fill-opacity="0.85"/>
                        <circle cx="32" cy="128" r="2.5" fill="#FFE6DF" fill-opacity="0.7"/>
                        <circle cx="224" cy="138" r="2" fill="#FFFFFF" fill-opacity="0.8"/>
                    </svg>
                </div>
                """)

    with a_col:
        with st.container(key="card_hero_ai"):
            html("""
            <div class="df-ai-head">
                <div class="df-ai-title"><span style="color:#C21F20;">✦</span> Trợ lý Data Forge AI</div>
                <span class="df-ai-online">● Trực tuyến</span>
            </div>
            <div class="df-ai-body">
                <svg width="64" height="68" viewBox="0 0 64 68" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;" aria-hidden="true">
                    <circle cx="32" cy="36" r="26" fill="#FFFFFF" stroke="#EADDD5" stroke-width="1.5"/>
                    <rect x="6" y="25" width="7" height="17" rx="3.5" fill="#C21F20"/>
                    <rect x="51" y="25" width="7" height="17" rx="3.5" fill="#C21F20"/>
                    <path d="M11 26 C11 12, 53 12, 53 26" stroke="#8C2924" stroke-width="3" stroke-linecap="round"/>
                    <rect x="15" y="20" width="34" height="25" rx="11" fill="#FFF8F0" stroke="#EADDD5" stroke-width="1.4"/>
                    <rect x="19" y="24" width="26" height="15" rx="7" fill="#4B111D"/>
                    <circle cx="26.5" cy="31.5" r="2.6" fill="#E9A096"/>
                    <circle cx="37.5" cy="31.5" r="2.6" fill="#E9A096"/>
                    <path d="M27.5 35.5 Q32 38.2 36.5 35.5" stroke="#FFF8F0" stroke-width="1.6" stroke-linecap="round"/>
                    <rect x="21" y="48" width="22" height="11" rx="5.5" fill="#FFFFFF" stroke="#EADDD5" stroke-width="1.2"/>
                    <circle cx="32" cy="53.5" r="2.5" fill="#C21F20"/>
                </svg>
                <div class="df-ai-bubble">
                    <b>Xin chào! Tôi có thể giúp bạn:</b>
                    <ul>
                        <li><span>✓</span>Phân tích doanh thu theo chiến dịch &amp; khu vực</li>
                        <li><span>✓</span>Tạo dashboard trực quan</li>
                        <li><span>✓</span>Trả lời các câu hỏi về dữ liệu...</li>
                    </ul>
                </div>
            </div>
            """)
            _chat_hist = st.session_state.setdefault("chat_history", [dict(DEFAULT_CHAT_GREETING)])
            last_ai = next(
                (m["content"] for m in reversed(_chat_hist) if m.get("role") == "assistant"),
                None,
            )
            if last_ai and len(_chat_hist) > 1:
                html(f'<div class="df-ai-reply-chip"><b>AI:</b> {_strip_md_for_chip(last_ai)}</div>')

            with st.form("hero_ai_inline_form", clear_on_submit=True):
                qi_col, qb_col = st.columns([2.85, 1.55], gap="small")
                with qi_col:
                    hero_ai_q = st.text_input(
                        "Đặt câu hỏi cho tôi...",
                        placeholder="Đặt câu hỏi cho tôi...",
                        label_visibility="collapsed",
                    )
                with qb_col:
                    hero_ai_go = st.form_submit_button("Gửi →", type="primary", use_container_width=True)
            if hero_ai_go and hero_ai_q.strip():
                _chat_hist.append({"role": "user", "content": hero_ai_q.strip()})
                _chat_hist.append({"role": "assistant", "content": generate_ai_reply(hero_ai_q.strip())})
                st.rerun()

    if st.session_state.get("show_ai_hub"):
        _chat_hist = st.session_state.setdefault("chat_history", [dict(DEFAULT_CHAT_GREETING)])
        with st.container(key="card_ai_hub"):
            hc1, hc2 = st.columns([5, 1])
            with hc1:
                card_header("Trung tâm Trợ lý Data Forge AI", "Hỏi đáp trực tiếp, chạy chuẩn hóa hoặc điều hướng nhanh bằng ngôn ngữ tự nhiên")
            with hc2:
                if st.button("Đóng AI ✕", key="btn_close_ai_hub", use_container_width=True):
                    st.session_state.show_ai_hub = False
                    st.rerun()
            hq1, hq2, hq3, hq4 = st.columns(4)
            _hub_qs = [
                (hq1, "aihub_q1", "📊 Tình hình hiện tại", "Tóm tắt tình hình dữ liệu và các bước tiếp theo"),
                (hq2, "aihub_q2", "🔥 Top 3 chiến dịch", "Top 3 chiến dịch nào mang lại doanh thu cao nhất?"),
                (hq3, "aihub_q3", "🧹 Lọc dữ liệu rác", "Chạy làm sạch lọc dữ liệu rác ngay bây giờ"),
                (hq4, "aihub_q4", "🛡 Mở trang HITL", "Chuyển sang trang Phê duyệt Exceptions"),
            ]
            for col_w, k_btn, lbl_btn, prompt_btn in _hub_qs:
                with col_w:
                    if st.button(lbl_btn, key=k_btn, use_container_width=True):
                        _chat_hist.append({"role": "user", "content": prompt_btn})
                        _chat_hist.append({"role": "assistant", "content": generate_ai_reply(prompt_btn)})
                        st.rerun()
            for msg in _chat_hist[-4:]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
            with st.form("ai_hub_form", clear_on_submit=True):
                c_inp, c_go = st.columns([4.5, 1.2])
                with c_inp:
                    hub_q = st.text_input("Nhập câu hỏi hoặc câu lệnh vận hành...", placeholder="Ví dụ: Top chiến dịch, doanh thu khu vực hoặc lọc dữ liệu rác...", label_visibility="collapsed")
                with c_go:
                    hub_go = st.form_submit_button("Thực thi câu lệnh AI", type="primary", use_container_width=True)
                if hub_go and hub_q.strip():
                    _chat_hist.append({"role": "user", "content": hub_q.strip()})
                    _chat_hist.append({"role": "assistant", "content": generate_ai_reply(hub_q.strip())})
                    st.rerun()


def _build_overview_insights(rep, norm_tx, q, total_gross_rev, total_net, total_cost, total_nc):
    """Build real-data insight bullets from active engine outputs (zero fabricated numbers)."""
    items = []
    if rep is not None and not rep.empty and "Attributed_Revenue" in rep.columns:
        top_row = rep.sort_values("Attributed_Revenue", ascending=False).iloc[0]
        top_name = _html.escape(str(top_row.get("Campaign_Name", "N/A")))
        top_rev = safe_float(top_row.get("Attributed_Revenue", 0.0), 0.0)
        tot_attr = max(1e-9, float(rep["Attributed_Revenue"].sum()))
        share_pct = (top_rev / tot_attr) * 100.0
        items.append({
            "cls": "red",
            "ico": "📈",
            "title": f"Chiến dịch dẫn đầu: {top_name}",
            "desc": f"Đóng góp {share_pct:.1f}% tổng doanh thu phân bổ toàn hệ thống.",
            "badge": fmt_vnd(top_rev),
        })

    dq_score = q.get("Data_Quality_Score", "—") if isinstance(q, dict) else "—"
    n_orders = len(norm_tx) if norm_tx is not None else 0
    disc_pct = ((total_gross_rev - total_net) / max(1e-9, total_gross_rev)) * 100.0 if total_gross_rev > 0 else 0.0
    items.append({
        "cls": "amber",
        "ico": "🧹",
        "title": f"Chất lượng dữ liệu đạt {dq_score}%",
        "desc": f"Đã đối soát {n_orders:,} giao dịch hợp lệ; tỷ lệ giảm trừ & hoàn trả ở mức {disc_pct:.1f}%.",
        "badge": vi_status(q.get("Status", st.session_state.cleaning_status), q) if isinstance(q, dict) else "Đã kiểm soát",
    })

    n_pend = len(pending_exceptions())
    if total_nc is not None and total_net > 0:
        margin_pct = (total_nc / total_net) * 100.0
        items.append({
            "cls": "purple" if n_pend > 0 else "teal",
            "ico": "🛡" if n_pend > 0 else "💎",
            "title": f"Biên đóng góp ròng {margin_pct:.1f}% • {n_pend} ngoại lệ HITL",
            "desc": "Chi phí ABC đã đối soát đầy đủ." if n_pend == 0 else f"Còn {n_pend} ngoại lệ cần Trưởng bộ phận phê duyệt tại HITL.",
            "badge": fmt_vnd(total_nc),
        })
    else:
        items.append({
            "cls": "purple",
            "ico": "🛡",
            "title": f"{n_pend} hồ sơ ngoại lệ chờ HITL",
            "desc": "Hệ thống bảo vệ dữ liệu chuẩn hóa với 7 Audit Tests bất biến.",
            "badge": f"{len(rep) if rep is not None else 0} chiến dịch",
        })
    return items


# ==============================================================================
# TRANG 1: TỔNG QUAN
# ==============================================================================
if page == PAGES[0]:
    render_header(f"Chào mừng {st.session_state.user_name} trở lại!", "Quản lý và khai thác dữ liệu Marketing thông minh cùng Data Forge AI.", show_chatbot=True)

    if st.session_state.data_status != "CONNECTED":
        with st.container(key="card_hero_glass"):
            h_left, h_right = st.columns([1.15, 1.0], gap="large")
            with h_left:
                html("""
                <div class="hero-tag">✨ Enterprise Data Analytics &amp; BI SaaS • Quy trình chuẩn 6 bước</div>
                <div class="hero-h1">DATA FORGE<br><span>Phân tích &amp; Kiểm toán Dữ liệu Doanh nghiệp</span></div>
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
                html("""
                <div class="hstats" id="df-hero-stats">
                    <div class="hstat"><span class="snum"><span class="hstat-val" data-target="6" data-suffix="" data-duration="1100" data-delay="0">6</span><em>Bước</em></span><small>Làm sạch tự động</small></div>
                    <div class="sdiv"></div>
                    <div class="hstat"><span class="snum"><span class="hstat-val" data-target="7" data-suffix="" data-duration="1250" data-delay="120">7</span><em>Tests</em></span><small>Kiểm toán bất biến</small></div>
                    <div class="sdiv"></div>
                    <div class="hstat"><span class="snum"><span class="hstat-val" data-target="20" data-suffix="K" data-duration="1500" data-delay="240">20K</span><em>Max</em></span><small>Quota Guardrail</small></div>
                    <div class="sdiv"></div>
                    <div class="hstat"><span class="snum"><span class="hstat-val" data-target="100" data-suffix="" data-duration="1700" data-delay="360">100</span><em>%</em></span><small>Audit Logged</small></div>
                </div>
                """)
                st.components.v1.html("""
                <script>
                (function() {
                    function initHeroStatsCounter() {
                        var pWin, pDoc;
                        try {
                            pWin = window.parent;
                            pDoc = pWin.document;
                        } catch (e) {
                            return;
                        }
                        var root = pDoc.getElementById('df-hero-stats');
                        if (!root) return false;
                        if (root.dataset.counterBound === '1') return true;
                        root.dataset.counterBound = '1';

                        var vals = Array.prototype.slice.call(root.querySelectorAll('.hstat-val'));
                        if (!vals.length) return true;

                        var stMain = pDoc.querySelector('[data-testid="stMain"]');
                        var appView = pDoc.querySelector('[data-testid="stAppViewContainer"]');
                        var secMain = pDoc.querySelector('section.main');

                        function getScrollY() {
                            return Math.max(
                                pWin.scrollY || pWin.pageYOffset || 0,
                                pDoc.documentElement ? (pDoc.documentElement.scrollTop || 0) : 0,
                                pDoc.body ? (pDoc.body.scrollTop || 0) : 0,
                                stMain ? (stMain.scrollTop || 0) : 0,
                                appView ? (appView.scrollTop || 0) : 0,
                                secMain ? (secMain.scrollTop || 0) : 0
                            );
                        }

                        function maxScroll() {
                            var m = 0;
                            [pDoc.documentElement, pDoc.body, stMain, appView, secMain].forEach(function(el) {
                                if (el && el.scrollHeight > el.clientHeight) {
                                    var diff = el.scrollHeight - el.clientHeight;
                                    if (diff > m) m = diff;
                                }
                            });
                            return m;
                        }

                        function isInView() {
                            var r = root.getBoundingClientRect();
                            var vh = pWin.innerHeight || (pDoc.documentElement ? pDoc.documentElement.clientHeight : 900);
                            return r.height > 0 && r.top < vh * 0.96 && r.bottom > 10;
                        }

                        var io = null;
                        var scrollTargets = [];
                        var startY = getScrollY();
                        var startedVisible = isInView();

                        function cleanup() {
                            if (io) { io.disconnect(); io = null; }
                            scrollTargets.forEach(function(t) { t.removeEventListener('scroll', onScroll); });
                        }

                        function runCountUp() {
                            if (root.dataset.counted === '1') return;
                            root.dataset.counted = '1';
                            cleanup();
                            vals.forEach(function(el) {
                                var target = parseInt(el.dataset.target || '0', 10);
                                var suffix = el.dataset.suffix || '';
                                var dur = parseInt(el.dataset.duration || '1300', 10);
                                var delay = parseInt(el.dataset.delay || '0', 10);
                                var card = el.closest('.hstat');
                                el.textContent = '0' + suffix;
                                setTimeout(function() {
                                    if (card) card.classList.add('is-counting');
                                    var t0 = null;
                                    function frame(now) {
                                        if (t0 === null) t0 = now;
                                        var p = Math.min(1, (now - t0) / dur);
                                        var eased = target <= 10 ? (1 - Math.pow(1 - p, 3)) : (1 - Math.pow(1 - p, 4));
                                        el.textContent = Math.round(eased * target) + suffix;
                                        if (p < 1) {
                                            pWin.requestAnimationFrame(frame);
                                        } else {
                                            el.textContent = target + suffix;
                                            if (card) {
                                                card.classList.remove('is-counting');
                                                card.classList.add('is-settled');
                                            }
                                        }
                                    }
                                    pWin.requestAnimationFrame(frame);
                                }, delay);
                            });
                        }

                        function onScroll() {
                            if (root.dataset.counted === '1') return;
                            var curY = getScrollY();
                            if (isInView() && (!startedVisible || curY > startY + 12)) {
                                runCountUp();
                            }
                        }

                        function bindListeners() {
                            [pWin, pDoc, pDoc.documentElement, pDoc.body, stMain, appView, secMain].forEach(function(t) {
                                if (t && scrollTargets.indexOf(t) === -1) {
                                    scrollTargets.push(t);
                                    t.addEventListener('scroll', onScroll, { passive: true });
                                }
                            });
                        }

                        if (!startedVisible) {
                            vals.forEach(function(el) {
                                el.textContent = '0' + (el.dataset.suffix || '');
                            });
                            bindListeners();
                            if ('IntersectionObserver' in pWin) {
                                io = new pWin.IntersectionObserver(function(entries) {
                                    entries.forEach(function(en) {
                                        if (en.isIntersecting) runCountUp();
                                    });
                                }, { threshold: 0.2 });
                                io.observe(root);
                            }
                        } else if (maxScroll() > 15) {
                            bindListeners();
                        } else {
                            setTimeout(runCountUp, 350);
                        }
                        return true;
                    }

                    var tries = 0;
                    if (!initHeroStatsCounter()) {
                        var timer = setInterval(function() {
                            tries += 1;
                            if (initHeroStatsCounter() || tries >= 25) clearInterval(timer);
                        }, 120);
                    }
                })();
                </script>
                """, height=0, width=0)
            with h_right:
                html("""
                <div class="orbit-stage">
                    <div class="orbit-ring"></div>
                    <div class="orbit-mote-track">
                        <div class="orbit-dot d1"></div>
                        <div class="orbit-dot d2"></div>
                    </div>
                    <div class="hero-circle">
                        <div class="hc-num">DF</div>
                        <div class="hc-lbl">Data Forge</div>
                        <div class="hc-sub">ENTERPRISE ANALYTICS</div>
                    </div>
                    
                    <!-- LỚP 2: ORBIT ROTATOR (Quay 360 độ liên tục trong 30s) -->
                    <div class="orbit-rotator">
                        <!-- LỚP 3 & 4: Vệ tinh 1: Auto-Clean (góc -150 độ) -->
                        <div class="orbit-item item-1">
                            <div class="orbit-counter">
                                <div class="fcard fc1" title="Auto-Clean 6 Bước">
                                    <div class="fcoi r">⚡</div>
                                    <div><span class="fcnum">Auto-Clean</span><span class="fcsm">6 Bước chuẩn hoá</span></div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- LỚP 3 & 4: Vệ tinh 2: 7 Audit Tests (góc -30 độ) -->
                        <div class="orbit-item item-2">
                            <div class="orbit-counter">
                                <div class="fcard fc2" title="7 Tests Kiểm toán">
                                    <div class="fcoi g">✓</div>
                                    <div><span class="fcnum">7 Audit Tests</span><span class="fcsm">Bảo toàn dòng tiền</span></div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- LỚP 3 & 4: Vệ tinh 3: HITL Guardrail (góc +90 độ) -->
                        <div class="orbit-item item-3">
                            <div class="orbit-counter">
                                <div class="fcard fc3" title="HITL Guardrail Ngoại lệ">
                                    <div class="fcoi y">★</div>
                                    <div><span class="fcnum">HITL Guardrail</span><span class="fcsm">Kiểm soát ngoại lệ</span></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="mini-grid">
                    <div class="mini-float mf-1">
                        <div class="mini-stat green">
                            <div class="mini-top"><span>✓</span><span class="mini-pill">Auto</span></div>
                            <div class="mini-lbl">Làm Sạch Tự Động</div>
                            <div class="mini-num">6 Bước</div>
                            <div class="mini-foot">Bảo toàn Raw Data</div>
                        </div>
                    </div>
                    <div class="mini-float mf-2">
                        <div class="mini-stat orange">
                            <div class="mini-top"><span>!</span><span class="mini-pill">HITL</span></div>
                            <div class="mini-lbl">Hồ sơ chờ phê duyệt (HITL)</div>
                            <div class="mini-num">0</div>
                            <div class="mini-foot">0 Hồ sơ chờ phê duyệt (HITL)</div>
                        </div>
                    </div>
                    <div class="mini-float mf-3">
                        <div class="mini-stat amber">
                            <div class="mini-top"><span>⚑</span><span class="mini-pill">Audit</span></div>
                            <div class="mini-lbl">Kiểm Toán Suite</div>
                            <div class="mini-num">7 Tests</div>
                            <div class="mini-foot">Đối soát bất biến</div>
                        </div>
                    </div>
                </div>
                """)

        html("""
        <div class="sb-marquee">
            <div class="sb-mqtrack">
                <div class="sb-mqitem"><i>●</i> Phân Tích Đa Điểm Chạm Multi-Touch</div>
                <div class="sb-mqitem"><i>●</i> Đối Soát Hoàn Hàng Tự Động (Returns)</div>
                <div class="sb-mqitem"><i>●</i> Phân Bổ Chi Phí ABC 3 Tầng</div>
                <div class="sb-mqitem"><i>●</i> Kiểm Toán 7 Bất Biến Tài Chính</div>
                <div class="sb-mqitem"><i>●</i> Quota Guardrail Chốt Chặn 20,000 Dòng</div>
                <div class="sb-mqitem"><i>●</i> Human-In-The-Loop (HITL) Phê Duyệt</div>
                <div class="sb-mqitem"><i>●</i> Xuất Excel Đa Sheet &amp; HTML Pack Độc Lập</div>
                <div class="sb-mqitem"><i>●</i> Phân Tích Đa Điểm Chạm Multi-Touch</div>
                <div class="sb-mqitem"><i>●</i> Đối Soát Hoàn Hàng Tự Động (Returns)</div>
                <div class="sb-mqitem"><i>●</i> Phân Bổ Chi Phí ABC 3 Tầng</div>
                <div class="sb-mqitem"><i>●</i> Kiểm Toán 7 Bất Biến Tài Chính</div>
                <div class="sb-mqitem"><i>●</i> Quota Guardrail Chốt Chặn 20,000 Dòng</div>
                <div class="sb-mqitem"><i>●</i> Human-In-The-Loop (HITL) Phê Duyệt</div>
                <div class="sb-mqitem"><i>●</i> Xuất Excel Đa Sheet &amp; HTML Pack Độc Lập</div>
            </div>
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

        # Nếu đã chạy Data Cleaning nhưng chưa chạy Process 6 bước -> hiển thị cảnh báo Quota & biểu đồ chất lượng dữ liệu
        q = st.session_state.quality_summary
        if q:
            st.write("")
            render_quota_guardrail_banner("ov_pre")
            qc1, qc2 = st.columns(2)
            with qc1:
                with st.container(key="card_ov_clean_summary"):
                    card_header("Tổng quan Làm sạch Dữ liệu", f"Trạng thái: {vi_status(q.get('Status', '—'), q)} • Điểm chất lượng: {q.get('Data_Quality_Score', 0)}%")
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
                                    color_discrete_sequence=["#27845E", "#D69A3B", "#5277A6", "#8B6A9C", "#C21F20"])
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
                                            "SUCCESS": "#27845E", "WARNING": "#D69A3B",
                                            "QUOTA_WARNING": "#8C2924",
                                            "NEEDS_APPROVAL": "#8B6A9C", "FAILED": "#C21F20",
                                        })
                        fig_ts.update_traces(textinfo="label+value")
                        st.plotly_chart(style_chart(fig_ts, height=260), width="stretch", config={"displayModeBar": False})

    else:
        rep = st.session_state.engine.report_result
        norm_tx = st.session_state.engine.get_active_transactions_df()
        total_rev = float(rep["Attributed_Revenue"].sum())
        if "Gross_Revenue" in rep.columns and rep["Gross_Revenue"].notna().any():
            total_gross_rev = float(rep["Gross_Revenue"].sum())
        elif norm_tx is not None and "Gross_Sales" in norm_tx.columns and norm_tx["Gross_Sales"].notna().any():
            total_gross_rev = float(pd.to_numeric(norm_tx["Gross_Sales"], errors="coerce").fillna(0).sum())
        else:
            total_gross_rev = total_rev
        if total_gross_rev < total_rev:
            total_gross_rev = total_rev
        total_discount = max(0.0, total_gross_rev - total_rev)
        total_net = float(rep["Net_Sales"].sum())
        has_costs = "Total_Cost" in rep.columns and rep["Total_Cost"].notna().any()
        total_cost = rep["Total_Cost"].sum() if has_costs else None
        total_nc = rep["Net_Contribution"].sum() if has_costs and "Net_Contribution" in rep.columns else None
        n_campaigns = len(rep)
        q = st.session_state.quality_summary or {}

        cost_html = f'<div class="kpi-val">{fmt_vnd(total_cost)}</div>' if total_cost is not None else '<div class="kpi-val muted">Chưa có dữ liệu chi phí</div>'
        nc_html = f'<div class="kpi-val">{fmt_vnd(total_nc)}</div>' if total_nc is not None else '<div class="kpi-val muted">Cần tab Campaign_Costs</div>'
        gross_hint = f"↑ Giảm giá: {fmt_vnd(total_discount)} • {n_campaigns} chiến dịch" if total_discount > 0 else f"↑ Trước hoàn trả • {n_campaigns} nhóm chiến dịch"

        html("""
        <div class="sb-marquee" style="margin-bottom:16px;">
            <div class="sb-mqtrack">
                <div class="sb-mqitem"><i>●</i> Phân Tích Đa Điểm Chạm Multi-Touch</div>
                <div class="sb-mqitem"><i>●</i> Đối Soát Hoàn Hàng Tự Động (Returns)</div>
                <div class="sb-mqitem"><i>●</i> Phân Bổ Chi Phí ABC 3 Tầng</div>
                <div class="sb-mqitem"><i>●</i> Kiểm Toán 7 Bất Biến Tài Chính</div>
                <div class="sb-mqitem"><i>●</i> Quota Guardrail Chốt Chặn 20,000 Dòng</div>
                <div class="sb-mqitem"><i>●</i> Human-In-The-Loop (HITL) Phê Duyệt</div>
                <div class="sb-mqitem"><i>●</i> Xuất Excel Đa Sheet &amp; HTML Pack Độc Lập</div>
                <div class="sb-mqitem"><i>●</i> Phân Tích Đa Điểm Chạm Multi-Touch</div>
                <div class="sb-mqitem"><i>●</i> Đối Soát Hoàn Hàng Tự Động (Returns)</div>
                <div class="sb-mqitem"><i>●</i> Phân Bổ Chi Phí ABC 3 Tầng</div>
                <div class="sb-mqitem"><i>●</i> Kiểm Toán 7 Bất Biến Tài Chính</div>
                <div class="sb-mqitem"><i>●</i> Quota Guardrail Chốt Chặn 20,000 Dòng</div>
                <div class="sb-mqitem"><i>●</i> Human-In-The-Loop (HITL) Phê Duyệt</div>
                <div class="sb-mqitem"><i>●</i> Xuất Excel Đa Sheet &amp; HTML Pack Độc Lập</div>
            </div>
        </div>
        """)

        _rev_pts = [safe_float(v, 0.0) for v in rep["Attributed_Revenue"].tolist()] if "Attributed_Revenue" in rep.columns else []
        _net_pts = [safe_float(v, 0.0) for v in rep["Net_Sales"].tolist()] if "Net_Sales" in rep.columns else []
        _nc_pts = (
            [safe_float(v, 0.0) for v in rep["Net_Contribution"].tolist()]
            if (has_costs and "Net_Contribution" in rep.columns)
            else _net_pts
        )
        _ord_cnt = len(norm_tx) if norm_tx is not None else 0
        if norm_tx is not None and not norm_tx.empty and "Order_Date" in norm_tx.columns:
            _sp_df = norm_tx[["Order_Date", "Order_Value"]].copy()
            _sp_df["_dt"] = pd.to_datetime(_sp_df["Order_Date"], errors="coerce")
            _sp_df = _sp_df.dropna(subset=["_dt"]).sort_values("_dt")
            if len(_sp_df) >= 2:
                _sp_df["Order_Value"] = pd.to_numeric(_sp_df["Order_Value"], errors="coerce").fillna(0)
                _grp_sp = _sp_df.groupby(_sp_df["_dt"].dt.date)["Order_Value"].agg(["sum", "count"]).tail(12)
                if len(_grp_sp) >= 2:
                    if len(set(_grp_sp["sum"].tolist())) >= 2:
                        _rev_pts = _grp_sp["sum"].tolist()
                    if len(set(_grp_sp["count"].tolist())) >= 2:
                        _net_pts = _grp_sp["count"].tolist()

        _dq_raw = q.get("Data_Quality_Score", "—")
        _dq_num = safe_float(_dq_raw, 0.0)
        _dq_pts = [max(0.0, _dq_num - 4.5), max(0.0, _dq_num - 2.1), max(0.0, _dq_num - 0.8), _dq_num]
        _dq_cls = "pos" if _dq_num >= 85 else ("neu" if _dq_num >= 65 else "neg")
        _n_pend_hitl = len(pending_exceptions())
        nc_display = fmt_vnd(total_nc) if total_nc is not None else (fmt_vnd(total_cost) if total_cost is not None else f"{_n_pend_hitl} Hồ sơ chờ phê duyệt (HITL)")
        nc_label = "Lợi nhuận ròng (NC)" if total_nc is not None else ("Chi phí ABC" if total_cost is not None else "Hồ sơ chờ phê duyệt (HITL)")
        _nc_hint = (
            f"Chi phí ABC: {fmt_vnd(total_cost)}"
            if total_cost is not None
            else f"{_n_pend_hitl} hồ sơ chờ phê duyệt (HITL)"
        )
        _nc_cls = "pos" if (total_nc is not None and total_nc >= 0) else ("neg" if (total_nc is not None and total_nc < 0) else "neu")
        _margin_txt = f" • Biên NC {(float(total_nc) / float(total_net) * 100):.1f}%" if (total_nc is not None and total_net > 0) else ""

        html(f"""
        <div class="kpi-grid-4">
            <div class="kpi-card-ent">
                <div class="kpi-ent-top">
                    <div class="kpi-ent-ico red">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><rect x="7" y="11" width="3" height="6" rx="1"/><rect x="12" y="7" width="3" height="10" rx="1"/><rect x="17" y="4" width="3" height="13" rx="1"/></svg>
                    </div>
                    <div>
                        <div class="kpi-ent-lbl">Tổng Doanh Thu Gộp</div>
                        <div class="kpi-ent-val">{fmt_vnd(total_gross_rev)}</div>
                    </div>
                </div>
                <div class="kpi-ent-bottom">
                    <div class="kpi-ent-delta pos">{gross_hint}<small>{n_campaigns} chiến dịch phân bổ</small></div>
                    {_svg_sparkline(_rev_pts, "#C21F20", "rgba(194,31,32,0.16)")}
                </div>
            </div>
            <div class="kpi-card-ent">
                <div class="kpi-ent-top">
                    <div class="kpi-ent-ico amber">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="20" r="1.5"/><circle cx="17" cy="20" r="1.5"/><path d="M3 4h2l2.4 11.2a2 2 0 0 0 2 1.6h7.8a2 2 0 0 0 2-1.5L21 8H7"/></svg>
                    </div>
                    <div>
                        <div class="kpi-ent-lbl">Net Sales &amp; Đơn hàng</div>
                        <div class="kpi-ent-val">{fmt_vnd(total_net)}</div>
                    </div>
                </div>
                <div class="kpi-ent-bottom">
                    <div class="kpi-ent-delta pos">↑ {_ord_cnt:,} đơn hợp lệ<small>Đối soát hoàn trả {st.session_state.return_window} ngày</small></div>
                    {_svg_sparkline(_net_pts, "#D69A3B", "rgba(214,154,59,0.18)")}
                </div>
            </div>
            <div class="kpi-card-ent">
                <div class="kpi-ent-top">
                    <div class="kpi-ent-ico purple">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
                    </div>
                    <div>
                        <div class="kpi-ent-lbl">{nc_label}</div>
                        <div class="kpi-ent-val">{nc_display}</div>
                    </div>
                </div>
                <div class="kpi-ent-bottom">
                    <div class="kpi-ent-delta {_nc_cls}">{_nc_hint}<small>Đối soát chi phí ABC 3 tầng</small></div>
                    {_svg_sparkline(_nc_pts, "#8B6A9C", "rgba(139,106,156,0.18)")}
                </div>
            </div>
            <div class="kpi-card-ent">
                <div class="kpi-ent-top">
                    <div class="kpi-ent-ico teal">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                    </div>
                    <div>
                        <div class="kpi-ent-lbl">Chất lượng Dữ liệu</div>
                        <div class="kpi-ent-val">{_dq_raw}%</div>
                    </div>
                </div>
                <div class="kpi-ent-bottom">
                    <div class="kpi-ent-delta {_dq_cls}">{vi_status(q.get("Status", st.session_state.cleaning_status), q)}<small>Kiểm toán 7 Audit Tests{_margin_txt}</small></div>
                    {_svg_sparkline(_dq_pts, "#258B86", "rgba(37,139,134,0.18)")}
                </div>
            </div>
        </div>
        """)

        ov_main_l, ov_main_r = st.columns([1.68, 1.0], gap="medium")
        with ov_main_l:
            with st.container(key="card_ov_main_rev_chart"):
                mc_h, mc_f = st.columns([1.0, 1.55], vertical_alignment="center")
                with mc_h:
                    html('<div class="card-title">Biểu đồ doanh thu</div><div class="card-sub">Theo dõi doanh thu &amp; tăng trưởng từ dữ liệu thực tế</div>')
                with mc_f:
                    with st.container(key="ov_period_filter"):
                        ov_period = st.radio(
                            "Kỳ hiển thị",
                            ["Chiến dịch", "Ngày", "Tháng", "Quý", "Năm"],
                            key="ov_period_radio",
                            horizontal=True,
                            label_visibility="collapsed",
                        )

                _period_mode_used = ov_period
                _plot_df = None
                _is_time_series = False
                if ov_period != "Chiến dịch" and norm_tx is not None and not norm_tx.empty and "Order_Date" in norm_tx.columns:
                    _tdf = norm_tx[["Order_Date", "Order_Value"]].copy()
                    _tdf["_dt"] = pd.to_datetime(_tdf["Order_Date"], errors="coerce")
                    _tdf = _tdf.dropna(subset=["_dt"]).copy()
                    if not _tdf.empty:
                        _tdf["Order_Value"] = pd.to_numeric(_tdf["Order_Value"], errors="coerce").fillna(0)
                        if "Gross_Sales" in norm_tx.columns and norm_tx["Gross_Sales"].notna().any():
                            _tdf["Rev"] = pd.to_numeric(norm_tx.loc[_tdf.index, "Gross_Sales"], errors="coerce").fillna(_tdf["Order_Value"])
                        else:
                            _tdf["Rev"] = _tdf["Order_Value"]
                        if ov_period == "Ngày":
                            _tdf["_key"] = _tdf["_dt"].dt.to_period("D")
                            _tdf["Nhãn"] = _tdf["_dt"].dt.strftime("%d/%m/%Y")
                        elif ov_period == "Tháng":
                            _tdf["_key"] = _tdf["_dt"].dt.to_period("M")
                            _tdf["Nhãn"] = _tdf["_dt"].dt.strftime("T%m/%Y")
                        elif ov_period == "Quý":
                            _tdf["_key"] = _tdf["_dt"].dt.to_period("Q")
                            _tdf["Nhãn"] = _tdf["_key"].astype(str)
                        else:
                            _tdf["_key"] = _tdf["_dt"].dt.to_period("Y")
                            _tdf["Nhãn"] = _tdf["_dt"].dt.strftime("%Y")
                        _agg = _tdf.groupby(["_key", "Nhãn"], as_index=False)[["Rev", "Order_Value"]].sum().sort_values("_key").tail(18)
                        if len(_agg) >= 1:
                            _agg["Growth_Pct"] = _agg["Rev"].pct_change().replace([float("inf"), float("-inf")], 0).fillna(0.0) * 100.0
                            _plot_df = _agg
                            _is_time_series = True

                if _plot_df is None:
                    if ov_period != "Chiến dịch":
                        st.caption(f"Nguồn hiện tại chưa đủ cột ngày (`Order_Date`) để tách theo {ov_period.lower()} — đang hiển thị theo Chiến dịch.")
                    _g_col = "Gross_Revenue" if "Gross_Revenue" in rep.columns else "Attributed_Revenue"
                    _plot_df = rep[["Campaign_Name", _g_col, "Net_Sales"]].copy()
                    _plot_df["Nhãn"] = _plot_df["Campaign_Name"].astype(str)
                    _plot_df["Rev"] = pd.to_numeric(_plot_df[_g_col], errors="coerce").fillna(0)
                    _plot_df["Order_Value"] = pd.to_numeric(_plot_df["Net_Sales"], errors="coerce").fillna(0)
                    _plot_df = _plot_df.sort_values("Rev", ascending=False).head(10)

                fig_main = go.Figure()
                fig_main.add_trace(
                    go.Bar(
                        x=_plot_df["Nhãn"],
                        y=_plot_df["Rev"],
                        name="Doanh thu",
                        marker=dict(color="#C21F20", line=dict(width=0)),
                        hovertemplate="%{x}<br>Doanh thu: %{y:,.0f} đ<extra></extra>",
                    )
                )
                if _is_time_series and len(_plot_df) >= 2:
                    fig_main.add_trace(
                        go.Scatter(
                            x=_plot_df["Nhãn"],
                            y=_plot_df["Growth_Pct"],
                            name="Tăng trưởng (%)",
                            yaxis="y2",
                            mode="lines+markers",
                            line=dict(color="#E9A096", width=2.6, shape="spline"),
                            marker=dict(size=7, color="#FFFFFF", line=dict(color="#C21F20", width=2)),
                            hovertemplate="%{x}<br>Tăng trưởng: %{y:+.1f}%<extra></extra>",
                        )
                    )
                    fig_main.update_layout(
                        yaxis2=dict(
                            overlaying="y",
                            side="right",
                            ticksuffix="%",
                            showgrid=False,
                            zeroline=True,
                            zerolinecolor="#EADDD5",
                            title=None,
                        )
                    )
                else:
                    fig_main.add_trace(
                        go.Scatter(
                            x=_plot_df["Nhãn"],
                            y=_plot_df["Order_Value"],
                            name="Net Sales",
                            mode="lines+markers",
                            line=dict(color="#258B86", width=2.6, shape="spline"),
                            marker=dict(size=7, color="#FFFFFF", line=dict(color="#258B86", width=2)),
                            hovertemplate="%{x}<br>Net Sales: %{y:,.0f} đ<extra></extra>",
                        )
                    )
                fig_main.update_layout(hovermode="x unified", bargap=0.38)
                st.plotly_chart(style_chart(fig_main, height=288), width="stretch", config={"displayModeBar": False})

        with ov_main_r:
            with st.container(key="card_ov_insights"):
                _insights = _build_overview_insights(rep, norm_tx, q, total_gross_rev, total_net, total_cost, total_nc)
                _ins_cards = []
                for _it in _insights:
                    _ins_cards.append(
                        f'<div class="df-insight-item">'
                        f'<div class="df-ins-ico {_it["cls"]}">{_it["ico"]}</div>'
                        f'<div><div class="df-ins-h">{_it["title"]}</div>'
                        f'<div class="df-ins-p">{_it["desc"]}</div>'
                        f'<span class="df-ins-metric">{_it["badge"]}</span></div>'
                        f'</div>'
                    )
                html(
                    f'<div class="df-insight-head">'
                    f'<div class="df-insight-title"><span style="color:#C21F20;">💡</span> Insight quan trọng</div>'
                    f'<span style="font-size:11.5px;font-weight:700;color:var(--df-brand-red);">{len(_insights)} điểm nhấn</span>'
                    f'</div>'
                    f'<div class="df-insight-list">{"".join(_ins_cards)}</div>'
                )
                st.write("")
                ib1, ib2 = st.columns(2, gap="small")
                with ib1:
                    if st.button("Kiểm toán →", key="ins_goto_clean", use_container_width=True):
                        go_to(PAGES[2])
                        st.rerun()
                with ib2:
                    if st.button(f"Duyệt HITL ({_n_pend_hitl}) →", key="ins_goto_exc", use_container_width=True):
                        go_to(PAGES[4])
                        st.rerun()

        st.write("")
        render_quota_guardrail_banner("ov")
        render_executive_pulse_bar(rep, norm_tx, q, total_gross_rev, total_net)

        with st.container(key="card_ov_quick_filter"):
            f1, f2 = st.columns([2.2, 1.4], vertical_alignment="bottom")
            with f1:
                ov_kw = st.text_input(
                    "🔍 Tìm kiếm nhanh Chiến dịch / Kênh / Sản phẩm",
                    placeholder="Nhập tên chiến dịch, kênh hoặc sản phẩm để lọc trực quan...",
                    key="ov_chart_search",
                ).strip().lower()
            with f2:
                ov_chart_mode = st.selectbox(
                    "📊 Kiểu hiển thị Biểu đồ",
                    ["Cột nhóm (Grouped)", "Cột chồng (Stacked)", "Biểu đồ ngang (Horizontal)"],
                    key="ov_chart_mode",
                )

        filtered_rep = rep.copy()
        filtered_tx = norm_tx.copy() if norm_tx is not None else None
        if ov_kw:
            mask_rep = (
                filtered_rep["Campaign_Name"].astype(str).str.lower().str.contains(ov_kw, regex=False, na=False)
                | filtered_rep.get("Channel", pd.Series("", index=filtered_rep.index)).astype(str).str.lower().str.contains(ov_kw, regex=False, na=False)
            )
            if mask_rep.any():
                filtered_rep = filtered_rep[mask_rep].copy()
            else:
                st.caption(f"Không tìm thấy chiến dịch khớp '{ov_kw}' — đang hiển thị toàn bộ dữ liệu chiến dịch.")
            if filtered_tx is not None and not filtered_tx.empty:
                m_tx = pd.Series(False, index=filtered_tx.index)
                for col_s in ["Order_ID", "Channel", "Campaign_List_Str", "Product_Name"]:
                    if col_s in filtered_tx.columns:
                        m_tx |= filtered_tx[col_s].astype(str).str.lower().str.contains(ov_kw, regex=False, na=False)
                if m_tx.any():
                    filtered_tx = filtered_tx[m_tx].copy()

        st.write("")
        ent_narratives = build_enterprise_report_narratives(
            df_campaign_metrics=rep,
            cleaning_report=q,
            exceptions_df=st.session_state.engine.exceptions_view,
            verification_results=st.session_state.verification_result or st.session_state.engine.verification_results,
            config={
                "return_window_days": st.session_state.return_window,
                "total_orders": len(norm_tx) if norm_tx is not None else None,
            },
            raw_or_cleaned_data=st.session_state.normalized_data,
        )
        if ent_narratives.get("block1_executive_mda"):
            html(ent_narratives["block1_executive_mda"])
        if ent_narratives.get("block2_data_governance"):
            html(ent_narratives["block2_data_governance"])

        with st.container(key="card_ov_campaign_health"):
            card_header("🏆 Thẻ Sức khỏe & Xếp hạng Chiến dịch Tương tác", "Di chuột vào từng thẻ để xem nổi khối chi tiết tỷ trọng Net Sales & hiệu quả ROI/ROAS")
            render_campaign_health_cards(filtered_rep)
        st.write("")

        missing_cmp = (
            norm_tx is not None and "Campaign_Data_Status" in norm_tx.columns
            and (norm_tx["Campaign_Data_Status"] == "MISSING_SOURCE_DATA").all()
        )
        has_product = (
            norm_tx is not None and "Product_Name" in norm_tx.columns
            and norm_tx["Product_Name"].dropna().astype(str).str.strip().ne("").any()
        )

        # Hàng biểu đồ 1: Doanh thu theo Sản phẩm (nếu thiếu mã chiến dịch) hoặc Chiến dịch & Tỷ trọng theo kênh
        bmode = "stack" if "Stacked" in ov_chart_mode else "group"
        is_horiz = "Horizontal" in ov_chart_mode
        col_a, col_b = st.columns([3, 2])
        with col_a:
            with st.container(key="card_campaign_chart"):
                if missing_cmp and has_product:
                    card_header("Doanh thu gộp & Lợi nhuận gộp theo Sản phẩm", "Tổng hợp từ các bản ghi hợp lệ sau xử lý")
                    tx_plot = filtered_tx if (filtered_tx is not None and not filtered_tx.empty) else norm_tx
                    p_cols = ["Product_Name", "Order_Value", "Source_Profit"]
                    if "Gross_Sales" in tx_plot.columns:
                        p_cols.append("Gross_Sales")
                    p_df = tx_plot[p_cols].dropna(subset=["Product_Name"]).copy()
                    p_df["Order_Value"] = pd.to_numeric(p_df["Order_Value"], errors="coerce").fillna(0)
                    p_df["Source_Profit"] = pd.to_numeric(p_df["Source_Profit"], errors="coerce").fillna(0)
                    if "Gross_Sales" in p_df.columns:
                        p_df["Gross_Sales"] = pd.to_numeric(p_df["Gross_Sales"], errors="coerce").fillna(p_df["Order_Value"])
                        val_cols = ["Gross_Sales", "Order_Value", "Source_Profit"]
                    else:
                        p_df["Gross_Sales"] = p_df["Order_Value"]
                        val_cols = ["Gross_Sales", "Source_Profit"]
                    by_prod = p_df.groupby("Product_Name", as_index=False)[val_cols].sum()
                    melt_prod = by_prod.melt(id_vars="Product_Name", var_name="Chỉ tiêu", value_name="VNĐ").replace({
                        "Gross_Sales": "Doanh thu gộp",
                        "Order_Value": "Doanh thu thuần",
                        "Source_Profit": "Lợi nhuận gộp",
                    })
                    if is_horiz:
                        fig = px.bar(melt_prod, y="Product_Name", x="VNĐ", color="Chỉ tiêu", orientation="h", barmode=bmode,
                                     color_discrete_sequence=["#C21F20", "#5277A6", "#27845E"])
                        fig.update_traces(marker_line_width=0, hovertemplate="%{y}<br>%{x:,.0f} đ<extra></extra>")
                    else:
                        fig = px.bar(melt_prod, x="Product_Name", y="VNĐ", color="Chỉ tiêu", barmode=bmode,
                                     color_discrete_sequence=["#C21F20", "#5277A6", "#27845E"])
                        fig.update_traces(marker_line_width=0, hovertemplate="%{x}<br>%{y:,.0f} đ<extra></extra>")
                    st.plotly_chart(style_chart(fig), width="stretch", config={"displayModeBar": False})
                else:
                    card_header("Doanh thu gộp theo chiến dịch", "So sánh Doanh thu gộp và Net Sales sau hoàn trả")
                    gross_col = "Gross_Revenue" if "Gross_Revenue" in filtered_rep.columns else "Attributed_Revenue"
                    chart_df = filtered_rep[["Campaign_Name", gross_col, "Net_Sales"]].melt(
                        id_vars="Campaign_Name", var_name="Chỉ số", value_name="VNĐ"
                    ).replace({gross_col: "Doanh thu gộp", "Net_Sales": "Net Sales"})
                    if is_horiz:
                        fig = px.bar(chart_df, y="Campaign_Name", x="VNĐ", color="Chỉ số", orientation="h", barmode=bmode,
                                     color_discrete_sequence=["#C21F20", "#E9A096"])
                        fig.update_traces(marker_line_width=0, hovertemplate="%{y}<br>%{x:,.0f} đ<extra></extra>")
                    else:
                        fig = px.bar(chart_df, x="Campaign_Name", y="VNĐ", color="Chỉ số", barmode=bmode,
                                     color_discrete_sequence=["#C21F20", "#E9A096"])
                        fig.update_traces(marker_line_width=0, hovertemplate="%{x}<br>%{y:,.0f} đ<extra></extra>")
                    st.plotly_chart(style_chart(fig), width="stretch", config={"displayModeBar": False})
                if ent_narratives.get("revenue_chart_html"):
                    html(ent_narratives["revenue_chart_html"])

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
                                     color_discrete_sequence=["#5277A6", "#8B6A9C", "#27845E"])
                    fig_fin.update_traces(marker_line_width=0, hovertemplate="%{x}<br>%{y:,.0f} đ<extra></extra>")
                    st.plotly_chart(style_chart(fig_fin, height=290), width="stretch", config={"displayModeBar": False})
                elif norm_tx is not None and len(norm_tx):
                    card_header("Cơ cấu Doanh thu gộp — Giá vốn — Lợi nhuận", "Tổng hợp từ bảng giao dịch đã chuẩn hóa")
                    net_s = float(pd.to_numeric(norm_tx.get("Order_Value", 0), errors="coerce").fillna(0).sum())
                    disc_s = float(pd.to_numeric(norm_tx.get("Discount_Amount", 0), errors="coerce").fillna(0).sum())
                    if "Gross_Sales" in norm_tx.columns and norm_tx["Gross_Sales"].notna().any():
                        gross_s = float(pd.to_numeric(norm_tx["Gross_Sales"], errors="coerce").fillna(0).sum())
                    else:
                        gross_s = net_s + max(0.0, disc_s)
                    cogs_s = float(pd.to_numeric(norm_tx.get("COGS", 0), errors="coerce").fillna(0).sum())
                    prof_s = float(pd.to_numeric(norm_tx.get("Source_Profit", 0), errors="coerce").fillna(0).sum())
                    struct_df = pd.DataFrame({
                        "Thành phần": ["Doanh thu gộp", "Net Sales", "Giá vốn (COGS)", "Lợi nhuận gộp"],
                        "Giá trị": [gross_s, net_s, cogs_s, prof_s],
                    })
                    fig_st = px.bar(struct_df, x="Thành phần", y="Giá trị", color="Thành phần",
                                    color_discrete_sequence=["#C21F20", "#5277A6", "#D69A3B", "#27845E"])
                    fig_st.update_layout(showlegend=False)
                    fig_st.update_traces(marker_line_width=0, hovertemplate="%{x}: %{y:,.0f} đ<extra></extra>")
                    st.plotly_chart(style_chart(fig_st, height=290), width="stretch", config={"displayModeBar": False})
                if ent_narratives.get("abc_cost_chart_html"):
                    html(ent_narratives["abc_cost_chart_html"])

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
                                         color_discrete_sequence=["#C21F20", "#258B86"])
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
                has_returns = "Attributed_Return" in rep.columns and rep["Attributed_Return"].sum() > 0
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
                                     color_discrete_sequence=["#5277A6", "#27845E"])
                    fig_reg.update_traces(marker_line_width=0, hovertemplate="%{x}<br>%{y:,.0f} đ<extra></extra>")
                    st.plotly_chart(style_chart(fig_reg, height=270), width="stretch", config={"displayModeBar": False})
                elif has_returns:
                    card_header("Tác động Hoàn trả theo Chiến dịch", "Doanh thu gộp, giá trị hoàn trả và Net Sales thực nhận")
                    g_col_ret = "Gross_Revenue" if "Gross_Revenue" in rep.columns else "Attributed_Revenue"
                    ret_df = rep[["Campaign_Name", g_col_ret, "Attributed_Return", "Net_Sales"]].melt(
                        id_vars="Campaign_Name", var_name="Thành phần", value_name="VNĐ"
                    ).replace({
                        g_col_ret: "Doanh thu gộp",
                        "Attributed_Return": "Khấu trừ hoàn trả",
                        "Net_Sales": "Net Sales",
                    })
                    fig_ret = px.bar(ret_df, x="Campaign_Name", y="VNĐ", color="Thành phần", barmode="group",
                                     color_discrete_sequence=["#5277A6", "#C21F20", "#27845E"])
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
                                   color_discrete_map={"PASS": "#27845E", "NOT_APPLICABLE": "#9E908D", "FAIL": "#C21F20"})
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
                                    color_discrete_sequence=["#27845E", "#5277A6", "#8B6A9C", "#D69A3B"])
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
                st.dataframe(sanitize_df_for_display(view), width="stretch", hide_index=True)
            else:
                st.caption("Chưa có đơn hàng.")

        if ent_narratives.get("block4_internal_control"):
            st.write("")
            html(ent_narratives["block4_internal_control"])

        # Khối 3.5: Biểu đồ Thác nước Tài chính (Financial Waterfall Chart)
        with st.container(key="card_ov_waterfall"):
            card_header("Biểu đồ Thác nước Tài chính (Financial Waterfall Chart)", "Dịch chuyển dòng tiền từ Doanh thu phân bổ qua Giảm trừ hoàn trả & Chi phí ABC tới Net Contribution")
            fig_wf, is_single_tbl, wf_note = build_financial_waterfall_fig(rep)
            if fig_wf is not None:
                st.plotly_chart(fig_wf, width="stretch", config={"displayModeBar": False})
                if is_single_tbl:
                    st.info(f"ℹ️ {wf_note}")
                else:
                    st.caption(wf_note)

        # Khối 4.5: Trình mô phỏng Kịch bản Động (What-If Scenario Simulator)
        render_what_if_simulator(rep, key_prefix="ov")

        if ent_narratives.get("block5_decision_matrix"):
            html(ent_narratives["block5_decision_matrix"])

        n_pending = len(pending_exceptions())
        with st.container(key="card_ov_quick_hub"):
            card_header("⚡ Trung tâm Tác vụ Nhanh & Xuất Báo cáo 1-Chạm", "Phê duyệt nhanh ngoại lệ HITL hoặc xuất ngay Báo cáo HTML / Gói Kiểm toán Excel 5 Sheet ngay tại trang Tổng quan")
            if n_pending:
                qa1, qa2 = st.columns(2)
                with qa1:
                    if st.button(f"⚡ Duyệt nhanh tất cả ({n_pending}) Hồ sơ HITL & Kiểm toán", type="primary", width="stretch", key="ov_btn_quick_approve_all"):
                        cnt_app = quick_approve_all_and_verify()
                        queue_toast(f"Đã phê duyệt nhanh {cnt_app} hồ sơ HITL & hoàn tất Kiểm toán Verification Suite", "✅")
                        st.rerun()
                with qa2:
                    next_step("Đi tới Phê duyệt chi tiết từng ngoại lệ →", PAGES[4], "ov_next_approve")
            else:
                if st.session_state.verification_status != "PASS":
                    st.info("Tất cả ngoại lệ đã xử lý — hãy chạy Verification Gate để mở khóa Báo cáo chuẩn kiểm toán.")
                    next_step("Đi tới Verification Suite →", PAGES[5], "ov_next_verify")
                else:
                    ov_rep_html = st.session_state.engine.generate_html_report(quality_summary=st.session_state.quality_summary)
                    ov_audit_xlsx = st.session_state.engine.generate_enterprise_audit_excel_pack(
                        quality_summary=st.session_state.quality_summary,
                        cleaning_errors=st.session_state.cleaning_errors,
                        audit_log=st.session_state.audit_log,
                        reconciliation_table=st.session_state.reconciliation_table,
                    )
                    qh1, qh2, qh3 = st.columns(3)
                    with qh1:
                        st.download_button(
                            "📄 Tải Báo cáo HTML (.html)",
                            data=ov_rep_html,
                            file_name=f"DataForge_Executive_Report_{datetime.datetime.now():%Y%m%d_%H%M%S}.html",
                            mime="text/html",
                            type="primary",
                            width="stretch",
                            key="ov_dl_html",
                        )
                    with qh2:
                        st.download_button(
                            "📥 Tải Hồ sơ Kiểm toán Excel (.xlsx)",
                            data=ov_audit_xlsx,
                            file_name=f"DataForge_Audit_Pack_{datetime.datetime.now():%Y%m%d_%H%M%S}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            width="stretch",
                            key="ov_dl_excel_pack",
                        )
                    with qh3:
                        next_step("Xem Báo cáo Đầy đủ →", PAGES[6], "ov_next_report")


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

    # Bối cảnh doanh nghiệp & Trao đổi yêu cầu với AI
    render_business_context_section()

    if st.session_state.raw_tabs:
        st.write("")
        if st.session_state.cleaning_status == "NOT_STARTED":
            render_pre_clean_diagnostics(context="connect")
        else:
            html(
                f'<div class="result-banner pass"><div><b>Nguồn dữ liệu này đã được làm sạch</b>'
                f'<small>Trạng thái: {vi_status(st.session_state.cleaning_status, st.session_state.quality_summary)} — xem chi tiết tại bước Làm sạch.</small></div></div>'
            )
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
                queue_toast(f"Làm sạch xong ({vi_status(q['Status'], q)}) — chất lượng {q['Data_Quality_Score']}%, {len(st.session_state.exceptions_list)} ngoại lệ")
            st.rerun()

        if st.session_state.cleaning_error_detail:
            st.error("Đã phát sinh lỗi khi làm sạch dữ liệu (hệ thống đã giữ nguyên Dữ liệu gốc). Chi tiết kỹ thuật:")
            st.code(st.session_state.cleaning_error_detail)

        if st.session_state.quality_summary is None and st.session_state.cleaning_status == "NOT_STARTED":
            st.write("")
            render_pre_clean_diagnostics(context="clean")

        q = st.session_state.quality_summary
        if q:
            st.write("")
            render_quota_guardrail_banner("cl")
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Bảng đã xử lý", f"{q.get('Tabs_Processed_Count', 1)}/{q.get('Total_Tabs_Count', 1)}")
            m2.metric("Dòng kiểm tra", f"{q['Total_Raw_Records']:,}")
            m3.metric("Dòng chuẩn hóa", f"{q.get('Normalized_Rows_Count', q['Normalized_Transactions_Count']):,}")
            m4.metric("Tự sửa an toàn", f"{q['Auto_Fixed_Count']:,}")
            m5.metric("Điểm chất lượng", f"{q['Data_Quality_Score']}%")

            n1, n2, n3, n4, n5 = st.columns(5)
            n1.metric("Lỗi phát hiện", f"{q.get('Total_Errors_Count', len(st.session_state.cleaning_errors))}")
            n2.metric("Trùng lặp", f"{q.get('Duplicate_Rows_Count', 0)}")
            n3.metric("Trường bị thiếu", f"{q.get('Missing_Fields_Count', 0)}")
            n4.metric("Hồ sơ chờ HITL", f"{q['Exceptions_Count']}")
            n5.metric("Trạng thái", vi_status(q.get("Status", st.session_state.cleaning_status), q))

            if st.session_state.cleaning_status == "FAILED" or not st.session_state.can_proceed_process:
                st.error("Dữ liệu còn lỗi chặn nên chưa thể chạy quy trình 6 bước. Xem nhật ký lỗi và trạng thái từng bảng bên dưới để biết chi tiết.")
            elif st.session_state.cleaning_status == "NEEDS_APPROVAL":
                st.warning(f"Đã chuẩn hóa dữ liệu ({q['Data_Quality_Score']}%) nhưng còn {q['Exceptions_Count']} Hồ sơ chờ phê duyệt (HITL).")

            st.write("")
            t_tabs, t_rec, t_cmp, t_log, t_audit, t_quar = st.tabs([
                "Trạng thái các bảng", "Đối chiếu bất biến", "Trước & sau", "Nhật ký lỗi", "Nhật ký thay đổi", "Khu Cách Ly (Quarantine)"
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
            with t_quar:
                quar_df = (st.session_state.normalized_data or {}).get("Quarantined_Records")
                if quar_df is not None and not quar_df.empty:
                    st.warning(f"Đang cách ly {len(quar_df):,} bản ghi vượt ngưỡng MAX_ROW_LIMIT ({q.get('Max_Row_Limit', MAX_ROW_LIMIT):,} dòng).")
                    show_df_preview(quar_df, width="stretch", hide_index=True)
                else:
                    st.success("Không có bản ghi nào nằm trong Khu Cách Ly (Data Quarantine).")

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
        colors = ["#C21F20", "#8C2924", "#D69A3B", "#5277A6", "#8B6A9C", "#258B86"]
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
                        reviewer = st.text_input("Tên người duyệt", value=st.session_state.user_name)
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
# TRANG 7: XUẤT BÁO CÁO QUẢN TRỊ (REPORTS & EXPORT)
# ==============================================================================
elif page == PAGES[6]:
    render_header("Xuất Báo cáo Quản trị (Reports & Export)", "Báo cáo HTML độc lập & Hồ sơ Kiểm toán Excel đa Sheet, sẵn sàng gửi Ban Giám đốc.")

    if st.session_state.verification_status != "PASS" or not has_report():
        empty_state("Báo cáo đang khóa: cần Verification đạt PASS.", "Đi tới Verification Suite →", PAGES[5], "rep")
    else:
        report_html = st.session_state.engine.generate_html_report(quality_summary=st.session_state.quality_summary)
        audit_excel = st.session_state.engine.generate_enterprise_audit_excel_pack(
            quality_summary=st.session_state.quality_summary,
            cleaning_errors=st.session_state.cleaning_errors,
            audit_log=st.session_state.audit_log,
            reconciliation_table=st.session_state.reconciliation_table,
        )
        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button(
                "📄 Tải Báo cáo HTML (Standalone HTML Report)",
                data=report_html,
                file_name=f"DataForge_Executive_Report_{datetime.datetime.now():%Y%m%d_%H%M%S}.html",
                mime="text/html",
                type="primary",
                width="stretch",
                key="rep_dl_html",
            )
        with dl2:
            st.download_button(
                "📥 Tải Hồ sơ Kiểm toán Excel (.xlsx)",
                data=audit_excel,
                file_name=f"DataForge_Audit_Pack_{datetime.datetime.now():%Y%m%d_%H%M%S}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
                key="rep_dl_excel_pack",
            )
        st.write("")
        render_what_if_simulator(st.session_state.engine.report_result, key_prefix="rep")
        st.write("")
        with st.container(key="card_report_preview"):
            card_header("Xem trước Báo cáo Quản trị")
            st.components.v1.html(report_html, height=760, scrolling=True)


# ==============================================================================
# TRANG 8: CẤU HÌNH HỆ THỐNG & ĐỊNH MỨC (SETTINGS)
# ==============================================================================
elif page == PAGES[7]:
    render_header("Cấu hình Hệ thống & Định mức (Settings)", "Tham số nghiệp vụ và chốt chặn định mức kiểm toán dùng cho các lần chạy tiếp theo.")

    with st.container(key="card_settings"):
        card_header("Định mức Return Window & Chốt chặn Dòng Dữ liệu (MAX_ROW_LIMIT)", "Điều chỉnh số ngày đối soát hoàn trả và ngưỡng giới hạn dòng trước khi kích hoạt Khu Cách Ly (Data Quarantine)")
        new_window = st.slider("Return Window (Số ngày đối soát hoàn trả)", min_value=15, max_value=30, value=st.session_state.return_window, step=1)
        if new_window != st.session_state.return_window:
            st.session_state.return_window = new_window
            if st.session_state.normalized_data:
                st.info("Đã lưu Return Window. Hãy chạy lại Data Cleaning và quy trình 6 bước để áp dụng giá trị mới.")
            else:
                st.success(f"Đã cập nhật Return Window = {new_window} ngày.")

        new_max_rows = st.number_input(
            "Ngưỡng tối đa số dòng kiểm toán chuẩn (MAX_ROW_LIMIT)",
            min_value=1000,
            max_value=200000,
            value=int(st.session_state.max_row_limit),
            step=1000,
            key="cfg_max_row_limit",
        )
        if int(new_max_rows) != int(st.session_state.max_row_limit):
            st.session_state.max_row_limit = int(new_max_rows)
            st.success(f"Đã cập nhật chốt chặn MAX_ROW_LIMIT = {int(new_max_rows):,} dòng.")

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
