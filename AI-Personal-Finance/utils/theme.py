"""Shared Streamlit styling and lightweight line icons."""

import streamlit as st


ICON_PATHS = {
    "wallet": '<path d="M20 8V5a2 2 0 0 0-2-2H5a3 3 0 0 0 0 6h15v10a2 2 0 0 1-2 2H5a3 3 0 0 1-3-3V6"/><path d="M16 14h.01"/><path d="M20 11h-5a3 3 0 0 0 0 6h5"/>',
    "income": '<path d="M12 19V5"/><path d="m5 12 7-7 7 7"/><path d="M5 19h14"/>',
    "expense": '<path d="M12 5v14"/><path d="m19 12-7 7-7-7"/><path d="M5 5h14"/>',
    "savings": '<circle cx="12" cy="12" r="9"/><path d="M16 8.5c-.7-.8-1.8-1.2-3.2-1.2-1.7 0-2.8.8-2.8 2s1 1.8 2.8 2.2 2.8 1 2.8 2.2-1.1 2-2.9 2c-1.4 0-2.5-.5-3.3-1.4M12.7 5.8v12.4"/>',
    "trend": '<path d="m3 17 6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
    "pie": '<path d="M21.2 15A9 9 0 0 1 9 2.8"/><path d="M21.2 15A9 9 0 0 0 9 2.8V15z"/><path d="M9 2.8A9 9 0 1 0 21.2 15"/>',
    "chart": '<path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/><path d="M15 9h4v4"/>',
    "receipt": '<path d="M4 2v20l4-2 4 2 4-2 4 2V2l-4 2-4-2-4 2z"/><path d="M8 9h8M8 13h6"/>',
    "sparkles": '<path d="m12 3 1.9 5.8L20 11l-6.1 2.2L12 19l-1.9-5.8L4 11l6.1-2.2z"/><path d="m19 14 1.1 2.2L22 17l-1.9.8L19 20l-1.1-2.2L16 17l1.9-.8z"/>',
    "bell": '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/>',
    "user": '<path d="M20 21a8 8 0 0 0-16 0"/><circle cx="12" cy="8" r="4"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 11h18"/>',
    "check": '<path d="m5 12 4 4L19 6"/><circle cx="12" cy="12" r="9"/>',
    "arrow-up-right": '<path d="M7 17 17 7M7 7h10v10"/>',
}


def icon_svg(name: str, size: int = 20) -> str:
    paths = ICON_PATHS.get(name, ICON_PATHS["wallet"])
    return (
        f'<svg aria-hidden="true" width="{size}" height="{size}" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" '
        f'stroke-linejoin="round">{paths}</svg>'
    )


def apply_theme() -> None:
    st.markdown(
        """
        <style>
          :root {
            --canvas: #f5f7f5;
            --surface: #ffffff;
            --surface-soft: #f8faf8;
            --ink: #172b25;
            --muted: #718078;
            --line: #e3eae5;
            --green: #237a5c;
            --green-soft: #eaf4ee;
            --blue: #4e7890;
            --blue-soft: #edf4f6;
            --red: #bf6258;
            --red-soft: #fff0ee;
            --shadow: 0 8px 24px rgba(23, 43, 37, .045);
          }
          html, body, [class*="css"] {
            font-family: Inter, "Segoe UI", ui-sans-serif, system-ui, sans-serif;
            letter-spacing: 0 !important;
          }
          .stApp { background: var(--canvas); color: var(--ink); }
          [data-testid="stAppViewContainer"] > .main .block-container {
            max-width: 1560px;
            padding: 2rem 2.25rem 3.5rem;
          }
          [data-testid="stSidebar"] {
            width: 268px !important;
            min-width: 268px !important;
            background: #ffffff !important;
            border-right: 1px solid #e3eae5;
          }
          [data-testid="stSidebarNav"] { display: none !important; }
          [data-testid="stSidebarContent"] { padding: 1.45rem 1rem 1rem; background: #ffffff; }
          [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: .55rem; }
          [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] { color: #263a32; }
          [data-testid="stSidebar"] [data-testid="stPopoverButton"] {
            color: #263a32 !important; background: #ffffff !important;
            border-color: #dce5df !important;
          }
          [data-testid="stSidebar"] [data-testid="stPopoverButton"]:hover {
            color: #172b25 !important; background: #f2f6f3 !important;
            border-color: #cbd8d0 !important;
          }
          [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] {
            color: #52625a !important; background: transparent !important;
            border-color: transparent !important;
          }
          [data-testid="stRadio"] > label {
            display: block; color: #718078; font-size: .68rem; font-weight: 700;
            letter-spacing: .11em; text-transform: uppercase; padding: .65rem .55rem .35rem;
          }
          [data-testid="stRadio"] [role="radiogroup"] { gap: .28rem; }
          [data-testid="stRadio"] [role="radio"] {
            min-height: 46px; padding: .62rem .72rem; border: 1px solid transparent;
            border-radius: 10px; color: #52625a;
            transition: background .15s ease, border-color .15s ease, color .15s ease;
          }
          [data-testid="stRadio"] [role="radio"]:hover {
            background: #f2f6f3; border-color: #e3eae5; color: #172b25;
          }
          [data-testid="stRadio"] [role="radio"][aria-checked="true"] {
            background: #eaf4ee;
            border-color: #c7dfd0;
            color: #1b684d;
            font-weight: 650;
          }
          [data-testid="stRadioOption"] span[role="img"] {
            margin-right: .4rem; font-size: 20px !important;
            font-variation-settings: "FILL" 1;
          }
          [data-testid="stRadioOption"] span[aria-label="space_dashboard icon"] { color: #3478c7 !important; }
          [data-testid="stRadioOption"] span[aria-label="receipt_long icon"] { color: #168477 !important; }
          [data-testid="stRadioOption"] span[aria-label="savings icon"] { color: #c47a16 !important; }
          [data-testid="stRadioOption"] span[aria-label="flag icon"] { color: #c65372 !important; }
          [data-testid="stRadioOption"] span[aria-label="monitoring icon"] { color: #64803b !important; }
          [data-testid="stRadioOption"] span[aria-label="query_stats icon"] { color: #5268b5 !important; }
          [data-testid="stRadioOption"] span[aria-label="auto_awesome icon"] { color: #d46848 !important; }
          [data-testid="stMetric"] {
            min-height: 132px;
            padding: 1.15rem 1.25rem;
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 14px;
            box-shadow: var(--shadow);
          }
          [data-testid="stMetricLabel"] { color: var(--muted); font-size: .83rem; }
          [data-testid="stMetricValue"] { color: var(--ink); font-size: 1.65rem; font-weight: 650; }
          [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--line);
            border-radius: 14px;
            background: var(--surface);
            box-shadow: var(--shadow);
          }
          h1 { color: var(--ink); font-size: 2rem !important; font-weight: 720 !important; letter-spacing: -.035em !important; }
          h2, h3 { color: var(--ink); letter-spacing: 0 !important; }
          [data-testid="stCaptionContainer"] { color: var(--muted); }
          .stButton > button, [data-testid="stPopover"] > button, [data-testid="stFormSubmitButton"] > button {
            min-height: 2.55rem;
            border-radius: 10px;
            border-color: var(--line);
            font-weight: 600;
            transition: transform .15s ease, box-shadow .15s ease, background .15s ease;
          }
          .stButton > button:hover, [data-testid="stPopover"] > button:hover { transform: translateY(-1px); box-shadow: 0 5px 14px rgba(23,43,37,.08); }
          .stButton > button[kind="primary"] {
            color: #fff;
            background: var(--green);
            border-color: var(--green);
          }
          .stButton > button[kind="primary"]:hover {
            background: #1b684d;
            border-color: #1b684d;
          }
          [data-testid="stDataFrame"] { border: 0; }
          [data-testid="stAlert"] { border-radius: 11px; }
          [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
          [data-testid="stDateInput"] input, [data-testid="stTextArea"] textarea,
          [data-testid="stSelectbox"] input,
          [data-testid="stSelectbox"] [data-baseweb="select"] > div {
            border-radius: 9px; border-color: #dce5df; background: #fff;
            color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important;
            opacity: 1 !important;
          }
          [data-testid="stTextInput"] input::placeholder,
          [data-testid="stTextArea"] textarea::placeholder,
          [data-testid="stSelectbox"] input::placeholder {
            color: #68776f !important; -webkit-text-fill-color: #68776f !important;
            opacity: 1 !important;
          }
          [data-testid="stTextInput"] input:focus,
          [data-testid="stNumberInput"] input:focus,
          [data-testid="stDateInput"] input:focus,
          [data-testid="stTextArea"] textarea:focus,
          [data-testid="stSelectbox"] input:focus {
            border-color: var(--green) !important;
            box-shadow: 0 0 0 1px var(--green) !important;
            outline: none;
          }
          [data-testid="stTextInput"] input:disabled,
          [data-testid="stNumberInput"] input:disabled,
          [data-testid="stDateInput"] input:disabled,
          [data-testid="stTextArea"] textarea:disabled,
          [data-testid="stSelectbox"] [aria-disabled="true"] {
            color: #68776f !important; -webkit-text-fill-color: #68776f !important;
            background: #eef2ef !important; opacity: 1 !important; cursor: not-allowed;
          }
          [data-testid="stWidgetLabel"] p {
            margin-bottom: .32rem; color: #40534b; font-size: .82rem; font-weight: 650;
          }
          [data-testid="stForm"] {
            padding: 1.1rem 1.2rem; border: 1px solid var(--line); border-radius: 14px;
            background: var(--surface); box-shadow: var(--shadow);
          }
          [data-testid="stTabs"] [role="tab"] { border-radius: 9px 9px 0 0; font-weight: 600; }
          [data-testid="stTabs"] [role="tab"][aria-selected="true"] { color: var(--green); }
          .finance-brand { display:flex; align-items:center; gap:11px; padding:4px 5px 22px; }
          .finance-brand-mark { width:39px; height:39px; display:grid; place-items:center; border-radius:12px; color:#14352a; background:#a6d4b1; }
          .finance-brand-name { color:#172b25; font-size:15px; font-weight:720; line-height:1.2; }
          .finance-brand-sub { color:#718078; font-size:11px; margin-top:4px; }
          .sidebar-section-label { color:#718078; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.1em; padding:10px 8px 5px; }
          .sidebar-profile { display:flex; align-items:center; gap:10px; padding:14px 8px 5px; border-top:1px solid #e3eae5; margin-top:16px; }
          .sidebar-avatar { display:grid; place-items:center; width:35px; height:35px; border-radius:11px; background:#eaf4ee; color:#1b684d; font-size:14px; font-weight:700; }
          .sidebar-user { color:#263a32; font-size:12px; font-weight:650; }
          .sidebar-account { color:#718078; font-size:11px; margin-top:3px; }
          .page-intro { display:flex; align-items:flex-start; justify-content:space-between; gap:1rem; margin-bottom:1.25rem; }
          .page-greeting { color:var(--green); font-size:13px; font-weight:650; margin-bottom:5px; }
          .page-subtitle { color:var(--muted); font-size:14px; margin-top:-8px; }
          .summary-pill-wrap { display:flex; justify-content:flex-end; }
          .summary-pill {
            display:flex; flex-direction:column; gap:2px; min-width:150px; padding:14px 16px;
            border-radius:14px; background:linear-gradient(135deg, rgba(35,122,92,.12), rgba(35,122,92,.04));
            border:1px solid rgba(35,122,92,.12); box-shadow:0 10px 24px rgba(23,43,37,.04);
          }
          .summary-pill-label { color:var(--muted); font-size:10px; text-transform:uppercase; letter-spacing:.12em; }
          .summary-pill-value { color:var(--green); font-size:1.15rem; font-weight:700; }
          .mini-summary {
            margin-top:12px; display:flex; justify-content:space-between; align-items:center; gap:8px;
            padding:10px 12px; border-radius:10px; background:#f9fbfa; border:1px solid var(--line);
            color:var(--muted); font-size:11px;
          }
          .mini-summary strong { color:var(--ink); font-size:12px; }
          .finance-card { background:var(--surface); border:1px solid var(--line); border-radius:14px; padding:19px 20px; box-shadow:var(--shadow); height:100%; }
          .finance-card-title { color:var(--ink); font-size:16px; font-weight:680; }
          .finance-card-note { color:var(--muted); font-size:12px; margin-top:3px; }
          .finance-card-head { display:flex; justify-content:space-between; align-items:center; gap:10px; margin-bottom:14px; }
          .finance-card-icon { color:var(--green); display:grid; place-items:center; width:36px; height:36px; border-radius:10px; background:var(--green-soft); }
          .metric-card { box-sizing:border-box; background:#fff; border:1px solid var(--line); border-radius:14px; padding:18px; height:156px; min-height:156px; box-shadow:var(--shadow); }
          .metric-card-top { display:flex; align-items:center; justify-content:space-between; color:var(--muted); font-size:13px; font-weight:600; }
          .metric-card-icon { display:grid; place-items:center; width:36px; height:36px; border-radius:10px; color:var(--blue); background:var(--blue-soft); }
          .metric-card-icon.green { color:var(--green); background:var(--green-soft); }
          .metric-card-icon.red { color:var(--red); background:var(--red-soft); }
          .metric-card-value { color:var(--ink); font-size:25px; font-weight:700; margin-top:13px; line-height:1.15; }
          .metric-card-foot { color:var(--muted); font-size:11px; margin-top:8px; }
          .metric-card-foot strong { color:var(--green); font-weight:650; }
          .empty-state { display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; min-height:190px; padding:16px; }
          .empty-icon { width:46px; height:46px; display:grid; place-items:center; border-radius:13px; background:#edf5f0; color:#538271; margin-bottom:12px; }
          .empty-title { color:#263a49; font-size:14px; font-weight:650; }
          .empty-copy { color:var(--muted); font-size:12px; max-width:290px; margin:5px auto 12px; }
          .budget-row { padding:10px 0; border-bottom:1px solid #edf0f2; }
          .budget-row:last-child { border-bottom:0; }
          .budget-row-top { display:flex; justify-content:space-between; gap:10px; color:#314553; font-size:12px; }
          .budget-row-top strong { font-weight:650; }
          .budget-track { height:7px; margin:8px 0 5px; background:#edf1f3; border-radius:9px; overflow:hidden; }
          .budget-fill { height:100%; background:#4b9a7b; border-radius:9px; }
          .budget-fill.warning { background:#d99a4c; }
          .budget-fill.danger { background:#cd6c61; }
          .budget-row-foot { display:flex; justify-content:space-between; color:#87949d; font-size:11px; }
          .insight-item { display:flex; gap:10px; padding:10px 0; border-bottom:1px solid #edf0f2; }
          .insight-item:last-child { border-bottom:0; }
          .insight-icon { flex:0 0 30px; width:30px; height:30px; display:grid; place-items:center; color:#397863; background:#edf5f0; border-radius:7px; }
          .insight-title { color:#304553; font-size:12px; font-weight:650; }
          .insight-copy { color:var(--muted); font-size:11px; line-height:1.45; margin-top:3px; }
          @media (max-width: 900px) {
            [data-testid="stAppViewContainer"] > .main .block-container { padding:1.5rem 1.25rem 2.5rem; }
            [data-testid="stHorizontalBlock"] { gap:1rem; }
          }
          @media (max-width: 640px) {
            [data-testid="stAppViewContainer"] > .main .block-container { padding:1rem .8rem 1.75rem; }
            [data-testid="stSidebar"] { width:min(268px, 86vw) !important; min-width:min(268px, 86vw) !important; }
            [data-testid="stHorizontalBlock"] { flex-wrap:wrap; gap:.75rem; }
            [data-testid="stHorizontalBlock"] > [data-testid="column"] { min-width:100% !important; }
            h1 { font-size:1.6rem !important; }
            .metric-card { height:146px; min-height:146px; padding:15px; }
            .metric-card-value { font-size:22px; }
            .finance-card { padding:15px; }
            .page-intro { gap:.5rem; }
            [data-testid="stMetric"] { min-height:110px; }
          }
        </style>
        """,
        unsafe_allow_html=True,
    )