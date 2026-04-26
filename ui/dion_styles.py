DION_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

    :root {
        --blast-bg: #0e0a17;
        --blast-bg-2: #151022;
        --blast-surface: rgba(22, 17, 35, 0.84);
        --blast-surface-strong: rgba(30, 23, 48, 0.96);
        --blast-field: rgba(42, 28, 68, 0.72);
        --blast-field-strong: rgba(52, 34, 84, 0.84);
        --blast-border: rgba(203, 166, 247, 0.12);
        --blast-border-strong: rgba(203, 166, 247, 0.28);
        --blast-primary: #8b5cf6;
        --blast-primary-deep: #6d28d9;
        --blast-primary-soft: rgba(139, 92, 246, 0.12);
        --blast-accent: #c084fc;
        --blast-text: #f7f1ff;
        --blast-muted: #bdaed4;
        --blast-shadow: 0 26px 60px rgba(0, 0, 0, 0.34);
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(192, 132, 252, 0.10), transparent 28%),
            radial-gradient(circle at top right, rgba(139, 92, 246, 0.18), transparent 32%),
            linear-gradient(180deg, #120d1d 0%, var(--blast-bg) 55%, #09070f 100%);
    }

    .block-container {
        max-width: 100%;
        padding-top: 1.5rem;
        padding-bottom: 2.4rem;
        padding-left: 2.4rem;
        padding-right: 2.4rem;
    }

    html, body, [class*="css"] {
        font-family: 'Manrope', sans-serif;
        color: var(--blast-text);
    }

    h1, h2, h3 {
        color: var(--blast-text);
        letter-spacing: -0.03em;
        font-family: 'Manrope', sans-serif !important;
    }

    h1 {
        font-size: 3.05rem !important;
        line-height: 1.02 !important;
        margin-bottom: 0.3rem !important;
        font-weight: 800 !important;
    }

    h2 {
        font-size: 1.35rem !important;
        margin-bottom: 0.35rem !important;
        font-weight: 750 !important;
    }

    h3 {
        font-size: 1.04rem !important;
        margin-bottom: 0.2rem !important;
    }

    p, label, div[data-testid='stMarkdownContainer'] p, div[data-testid='stCaptionContainer'] {
        color: var(--blast-text);
        font-size: 1rem !important;
        line-height: 1.55 !important;
    }

    div[data-testid="stMarkdownContainer"] li,
    div[data-testid="stCaptionContainer"],
    div[data-testid="stMetricLabel"] {
        color: var(--blast-muted) !important;
    }

    .dion-hero {
        background:
            linear-gradient(135deg, rgba(50, 29, 82, 0.96), rgba(109, 40, 217, 0.9) 58%, rgba(139, 92, 246, 0.84));
        border: 1px solid rgba(255, 255, 255, 0.10);
        box-shadow: 0 30px 85px rgba(107, 33, 168, 0.35);
        border-radius: 32px;
        padding: 2rem 1.8rem;
        color: white;
        overflow: hidden;
        position: relative;
        margin-bottom: 1.1rem;
    }

    .dion-hero::after {
        content: "";
        position: absolute;
        inset: -20% -10% auto auto;
        width: 260px;
        height: 260px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.12);
        filter: blur(10px);
    }

    .dion-kicker {
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-size: 0.82rem;
        font-weight: 700;
        opacity: 0.86;
        margin-bottom: 0.7rem;
    }

    .dion-hero h1, .dion-hero p, .dion-hero div {
        color: white !important;
        position: relative;
        z-index: 1;
    }

    .dion-grid-card,
    .dion-panel,
    div[data-testid='stForm'] {
        background: var(--blast-surface);
        backdrop-filter: blur(14px);
        border: 1px solid var(--blast-border);
        border-radius: 26px;
        box-shadow: var(--blast-shadow);
    }

    .dion-grid-card {
        padding: 1rem 1rem;
        min-height: 120px;
    }

    .dion-panel {
        padding: 1.2rem 1.2rem;
        margin-bottom: 1.15rem;
    }

    div[data-testid='stForm'] {
        background:
            linear-gradient(180deg, rgba(28, 21, 44, 0.98), rgba(18, 14, 30, 0.96)) !important;
        border: 1px solid rgba(196, 181, 253, 0.12) !important;
        box-shadow: 0 30px 60px rgba(0, 0, 0, 0.34) !important;
        padding: 1.55rem 1.45rem 1.3rem 1.45rem;
    }

    .dion-soft-label {
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 0.8rem;
        color: var(--blast-muted);
        font-weight: 800;
        margin-bottom: 0.55rem;
    }

    .dion-brief {
        background: linear-gradient(180deg, rgba(139, 92, 246, 0.10), rgba(139, 92, 246, 0.04));
        border: 1px solid rgba(196, 181, 253, 0.12);
        border-radius: 20px;
        padding: 0.95rem 0.95rem 0.8rem 0.95rem;
        margin-bottom: 0.9rem;
    }

    .dion-pill {
        display: inline-block;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(216, 180, 254, 0.16);
        border-radius: 999px;
        padding: 0.33rem 0.68rem;
        margin-right: 0.4rem;
        margin-bottom: 0.45rem;
        font-size: 0.92rem;
        color: var(--blast-text);
    }

    .dion-scope-card {
        border-radius: 20px;
        padding: 0.95rem 0.95rem 0.8rem 0.95rem;
        background: linear-gradient(180deg, rgba(34, 25, 54, 0.98), rgba(21, 16, 34, 0.98));
        border: 1px solid rgba(196, 181, 253, 0.14);
        min-height: 128px;
        box-shadow: 0 16px 34px rgba(0, 0, 0, 0.26);
    }

    .dion-scope-card strong {
        display: block;
        font-size: 1.02rem;
        margin-bottom: 0.25rem;
        color: var(--blast-text);
    }

    .dion-metric-card {
        background: var(--blast-surface-strong);
        border: 1px solid rgba(196, 181, 253, 0.12);
        border-radius: 20px;
        padding: 0.85rem 0.95rem 0.8rem 0.95rem;
        box-shadow: 0 14px 32px rgba(0, 0, 0, 0.22);
    }

    .dion-section-space {
        margin-top: 0.2rem;
    }

    .dion-nav {
        display: flex;
        gap: 0.65rem;
        flex-wrap: wrap;
        margin: 1rem 0 0.2rem 0;
    }

    .dion-nav span {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.08);
        color: white;
        border-radius: 999px;
        padding: 0.38rem 0.75rem;
        font-size: 0.88rem;
    }

    div[data-baseweb="input"],
    div[data-baseweb="select"],
    div[data-baseweb="textarea"] {
        border-radius: 16px !important;
        background: transparent !important;
        box-shadow: none !important;
    }

    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div,
    div[data-baseweb="textarea"] > div {
        background:
            linear-gradient(180deg, rgba(50, 33, 80, 0.9), rgba(35, 23, 58, 0.9)) !important;
        border: 1px solid rgba(216, 180, 254, 0.14) !important;
        border-radius: 16px !important;
        color: var(--blast-text) !important;
        min-height: 58px !important;
        box-shadow: none !important;
        overflow: visible !important;
        display: flex !important;
        align-items: center !important;
        margin: 0 !important;
    }

    div[data-baseweb="input"] > div:hover,
    div[data-baseweb="select"] > div:hover,
    div[data-baseweb="textarea"] > div:hover {
        background:
            linear-gradient(180deg, rgba(57, 37, 91, 0.94), rgba(40, 27, 67, 0.94)) !important;
        border-color: rgba(216, 180, 254, 0.2) !important;
    }

    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div[data-testid="stDateInputField"],
    div[data-baseweb="input"] > div[data-testid="stNumberInputField"] {
        background:
            linear-gradient(180deg, rgba(50, 33, 80, 0.9), rgba(35, 23, 58, 0.9)) !important;
    }

    div[data-testid="stTextInput"] > div,
    div[data-testid="stNumberInput"] > div,
    div[data-testid="stDateInput"] > div,
    div[data-testid="stSelectbox"] > div,
    div[data-testid="stTextArea"] > div {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    div[data-testid="stDateInput"] [data-baseweb="input"],
    div[data-testid="stDateInput"] [data-baseweb="input"] > div,
    div[data-testid="stDateInput"] [data-baseweb="base-input"] {
        background:
            linear-gradient(180deg, rgba(50, 33, 80, 0.9), rgba(35, 23, 58, 0.9)) !important;
        border: 1px solid rgba(216, 180, 254, 0.14) !important;
        border-radius: 16px !important;
        box-shadow: none !important;
    }

    div[data-testid="stDateInput"] button {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: var(--blast-muted) !important;
        padding-right: 0.55rem !important;
    }

    div[data-testid="stDateInput"] svg {
        fill: var(--blast-muted) !important;
    }

    div[data-baseweb="input"] > div::before,
    div[data-baseweb="input"] > div::after,
    div[data-baseweb="select"] > div::before,
    div[data-baseweb="select"] > div::after,
    div[data-baseweb="textarea"] > div::before,
    div[data-baseweb="textarea"] > div::after {
        display: none !important;
        border: none !important;
        box-shadow: none !important;
    }

    input,
    textarea,
    div[data-baseweb="select"] input {
        color: var(--blast-text) !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        line-height: 1 !important;
        padding-top: 0.76rem !important;
        padding-bottom: 0.76rem !important;
        margin: 0 !important;
    }

    div[data-testid="stNumberInput"] input {
        color: var(--blast-text) !important;
        background: transparent !important;
    }

    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stDateInput"] input,
    div[data-testid="stSelectbox"] input {
        min-height: 1.35rem !important;
        transform: translateY(-3px);
    }

    div[data-testid="stTextArea"] textarea {
        background: transparent !important;
        min-height: 170px !important;
        padding-top: 0.8rem !important;
        padding-bottom: 0.8rem !important;
    }

    input::placeholder,
    textarea::placeholder {
        color: rgba(214, 196, 240, 0.8) !important;
        opacity: 1 !important;
    }

    div[data-testid="stSelectbox"] label,
    div[data-testid="stTextInput"] label,
    div[data-testid="stTextArea"] label,
    div[data-testid="stDateInput"] label,
    div[data-testid="stNumberInput"] label,
    div[data-testid="stCheckbox"] label {
        color: var(--blast-text) !important;
        font-weight: 600 !important;
    }

    button[kind="primary"] {
        background: linear-gradient(135deg, #7c3aed, #8b5cf6 55%, #6d28d9) !important;
        border: none !important;
        border-radius: 16px !important;
        color: white !important;
        font-weight: 800 !important;
        box-shadow: 0 16px 34px rgba(168, 85, 247, 0.28) !important;
    }

    button[kind="secondary"] {
        border-radius: 14px !important;
    }

    div[data-testid="stFormSubmitButton"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding-top: 0.4rem !important;
    }

    div[data-testid="stFormSubmitButton"] > div {
        background:
            linear-gradient(180deg, rgba(40, 27, 67, 0.72), rgba(24, 18, 40, 0.32)) !important;
        border: 1px solid rgba(196, 181, 253, 0.1) !important;
        border-radius: 20px !important;
        padding: 0.75rem !important;
        box-shadow: none !important;
    }

    div[data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(216, 180, 254, 0.12);
        border-radius: 18px;
    }

    .dion-form-section {
        margin-bottom: 1.5rem;
        padding-bottom: 1.35rem;
        border-bottom: 1px solid rgba(216, 180, 254, 0.10);
    }

    .dion-form-section:last-of-type {
        border-bottom: none;
        padding-bottom: 0;
    }

    .dion-form-section h3 {
        margin-bottom: 0.95rem !important;
    }

    .dion-form-subtle {
        color: var(--blast-muted);
        font-size: 0.98rem;
        margin-bottom: 1rem;
    }

    div[data-testid="stForm"] .stColumn {
        gap: 1.15rem;
    }

    .dion-output-shell {
        min-height: 780px;
    }

    .dion-output-empty {
        display: flex;
        flex-direction: column;
        justify-content: center;
        min-height: 440px;
    }

    /* Result cards (st.container with border=True) */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(180deg, rgba(34, 25, 54, 0.90), rgba(21, 16, 34, 0.90)) !important;
        border: 1px solid rgba(196, 181, 253, 0.16) !important;
        border-radius: 18px !important;
        box-shadow: 0 12px 28px rgba(0, 0, 0, 0.20) !important;
        margin-bottom: 0.5rem !important;
    }

    /* Link buttons */
    [data-testid="stLinkButton"] a {
        background: linear-gradient(135deg, #7c3aed, #8b5cf6 55%, #6d28d9) !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        border: none !important;
        font-size: 0.88rem !important;
        text-decoration: none !important;
        box-shadow: 0 8px 18px rgba(139, 92, 246, 0.25) !important;
    }

    /* Progress bar */
    .stProgress {
        background: rgba(139, 92, 246, 0.12) !important;
        border-radius: 999px !important;
        height: 6px !important;
        overflow: hidden !important;
    }

    .stProgress > div {
        background: linear-gradient(90deg, #7c3aed, #a855f7) !important;
        border-radius: 999px !important;
    }

    /* Metric values */
    [data-testid="stMetricValue"] {
        color: var(--blast-text) !important;
        font-size: 2.1rem !important;
        font-weight: 800 !important;
        font-family: 'Manrope', sans-serif !important;
    }

    /* Status widget (st.status) */
    [data-testid="stStatusWidget"] {
        background: rgba(34, 25, 54, 0.92) !important;
        border: 1px solid rgba(196, 181, 253, 0.16) !important;
        border-radius: 20px !important;
        box-shadow: 0 14px 32px rgba(0, 0, 0, 0.22) !important;
    }

    /* Alert boxes */
    [data-testid="stAlert"] {
        border-radius: 16px !important;
        font-family: 'Manrope', sans-serif !important;
    }

    /* Result block section header (lightweight, no box) */
    .dion-result-header {
        margin-top: 1.3rem;
        margin-bottom: 0.65rem;
        padding-bottom: 0.55rem;
        border-bottom: 1px solid rgba(216, 180, 254, 0.12);
    }

    .dion-result-header h3 {
        margin-bottom: 0 !important;
    }

</style>
"""
