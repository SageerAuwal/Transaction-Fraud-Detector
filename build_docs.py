import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def create_document():
    doc = docx.Document()

    # Page Margins (1 inch everywhere)
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Styles & Fonts
    style_normal = doc.styles['Normal']
    font = style_normal.font
    font.name = 'Calibri'
    font.size = Pt(11)
    font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)

    # Color Palette
    PRIMARY_NAVY = RGBColor(0x0F, 0x17, 0x2A)  # #0f172a
    ACCENT_CYAN  = RGBColor(0x02, 0x84, 0xC7)  # #0284c7
    DARK_TEXT    = RGBColor(0x1E, 0x29, 0x3B)  # #1e293b
    MUTED_GRAY   = RGBColor(0x64, 0x74, 0x8B)  # #64748b

    # Title Banner / Header
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run("GOJO SENTINEL")
    run_title.font.name = 'Calibri'
    run_title.font.size = Pt(28)
    run_title.font.bold = True
    run_title.font.color.rgb = ACCENT_CYAN

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_sub.add_run("Hybrid Transaction Fraud Detection & Regulatory Compliance System for Nigerian Banking")
    run_sub.font.name = 'Calibri'
    run_sub.font.size = Pt(14)
    run_sub.font.italic = True
    run_sub.font.color.rgb = MUTED_GRAY

    doc.add_paragraph() # spacing

    # Executive Metadata Box Table
    table_meta = doc.add_table(rows=3, cols=2)
    table_meta.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        ("System Name:", "Gojo Sentinel Fraud Detection Platform"),
        ("Target Region:", "Nigeria Financial Sector (CBN / NIBSS / NIP / USSD Compliance)"),
        ("Architecture:", "Hybrid Engine: Rules Engine (CBN Policy) + Machine Learning (XGBoost)")
    ]
    for row_idx, (k, v) in enumerate(meta_data):
        cell_k = table_meta.cell(row_idx, 0)
        cell_v = table_meta.cell(row_idx, 1)
        cell_k.width = Inches(2.2)
        cell_v.width = Inches(4.3)
        set_cell_background(cell_k, "F1F5F9")
        set_cell_background(cell_v, "F8FAFC")
        
        pk = cell_k.paragraphs[0]
        rk = pk.add_run(k)
        rk.bold = True
        rk.font.color.rgb = PRIMARY_NAVY
        
        pv = cell_v.paragraphs[0]
        rv = pv.add_run(v)
        rv.font.color.rgb = DARK_TEXT

    doc.add_paragraph() # spacing

    def add_heading_1(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(18)
        h.paragraph_format.space_after = Pt(6)
        run = h.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(18)
        run.font.bold = True
        run.font.color.rgb = PRIMARY_NAVY
        return h

    def add_heading_2(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(12)
        h.paragraph_format.space_after = Pt(4)
        run = h.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(14)
        run.font.bold = True
        run.font.color.rgb = ACCENT_CYAN
        return h

    def add_body_p(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.15
        run = p.add_run(text)
        run.font.color.rgb = DARK_TEXT
        return p

    def add_bullet(bold_prefix, text):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(3)
        run_b = p.add_run(bold_prefix + ": ")
        run_b.bold = True
        run_b.font.color.rgb = PRIMARY_NAVY
        run_t = p.add_run(text)
        run_t.font.color.rgb = DARK_TEXT

    # 1. EXECUTIVE SUMMARY
    add_heading_1("1. Executive Summary")
    add_body_p(
        "Gojo Sentinel is an enterprise-grade, hybrid artificial intelligence and regulatory compliance transaction screening platform built specifically for the Nigerian financial ecosystem. Financial fraud in Nigeria across electronic payment channels—such as NIBSS Instant Payments (NIP), USSD banking, Mobile Money, and Web portals—poses critical security challenges. Gojo Sentinel addresses these risks by coupling deterministic Central Bank of Nigeria (CBN) regulatory compliance rules with probabilistic Machine Learning (XGBoost) fraud scoring."
    )
    add_body_p(
        "The system processes both single real-time transactions and large bulk datasets (CSV), delivering sub-second risk classification across four distinct verdicts: APPROVE (Low Risk), REVIEW (Medium Risk), DECLINE (High Risk), and BLOCK (Critical Policy Breach)."
    )

    # 2. SYSTEM ARCHITECTURE & ENGINE DESIGN
    add_heading_1("2. System Architecture & Design")
    add_body_p(
        "The system operates on a dual-engine architecture designed to ensure zero tolerance for statutory regulatory breaches while maintaining ultra-low false-positive rates using machine learning."
    )

    table_arch = doc.add_table(rows=5, cols=3)
    table_arch.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Layer / Module", "Technology / Stack", "Functional Purpose"]
    for i, h_text in enumerate(headers):
        cell = table_arch.cell(0, i)
        set_cell_background(cell, "0F172A")
        p = cell.paragraphs[0]
        r = p.add_run(h_text)
        r.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    arch_rows = [
        ("Backend REST API", "FastAPI / Python 3.10+", "High-throughput asynchronous API serving real-time prediction and dataset batch processing."),
        ("Compliance Engine", "Deterministic Rule Set (CBN)", "Instant verification against USSD caps, NIP single transfer limits, velocity thresholds, and restricted bank lists."),
        ("AI Machine Learning Engine", "XGBoost Classifier", "Probabilistic feature evaluation calculating exact fraud likelihood percentages based on historical transaction dynamics."),
        ("User Interface (Web & Mobile)", "HTML5, Vanilla CSS, JS, Cordova", "Responsive single-page web app & Cordova mobile APK featuring Gemini-style Collapsible Rail Sidebar, Live Terminal Logs, and Trend Analytics.")
    ]
    for row_idx, data in enumerate(arch_rows, start=1):
        for col_idx, text in enumerate(data):
            cell = table_arch.cell(row_idx, col_idx)
            set_cell_background(cell, "F8FAFC" if row_idx % 2 == 1 else "FFFFFF")
            p = cell.paragraphs[0]
            p.add_run(text)

    doc.add_paragraph()

    # 3. NIGERIAN BANKING REGULATORY COMPLIANCE MODULE
    add_heading_1("3. Nigerian Banking Regulatory Compliance Module")
    add_body_p(
        "Gojo Sentinel embeds native compliance logic aligned with Central Bank of Nigeria (CBN) operational guidelines for electronic payment channels:"
    )
    add_bullet("USSD Transfer Thresholds", "Transactions initiated via USSD channel (*901#, *737#, *894#, etc.) exceeding ₦100,000 NGN daily limit are automatically flagged as CRITICAL / BLOCK violations.")
    add_bullet("NIP Single Transfer Limit", "Single transfers over NIBSS Instant Payment (NIP) exceeding ₦5,000,000 NGN are flagged for mandatory compliance review.")
    add_bullet("Midnight Velocity Spikes", "High-value transfers occurring between 11:00 PM and 04:30 AM are subjected to elevated risk scoring due to historical fraud correlation during non-operating hours.")
    add_bullet("Restricted Bank List", "Automatic flagging of transactions routed to or from high-risk accounts or institutions with active regulatory flags.")

    # 4. MACHINE LEARNING & RISK VERDICT MATRIX
    add_heading_1("4. Machine Learning & Risk Verdict Matrix")
    add_body_p(
        "The XGBoost model processes multi-dimensional transaction features to output a normalized Fraud Probability Score (0.0% to 100.0%). This score is combined with the rules engine output into a final Risk Verdict Matrix:"
    )

    table_risk = doc.add_table(rows=5, cols=4)
    table_risk.alignment = WD_TABLE_ALIGNMENT.CENTER
    risk_headers = ["Risk Level", "Probability Score", "Action / Verdict", "System Behavior"]
    for i, h_text in enumerate(risk_headers):
        cell = table_risk.cell(0, i)
        set_cell_background(cell, "0284C7")
        p = cell.paragraphs[0]
        r = p.add_run(h_text)
        r.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    risk_data = [
        ("LOW RISK", "0.0% - 29.9%", "APPROVE", "Transaction cleared automatically without friction."),
        ("MEDIUM RISK", "30.0% - 59.9%", "REVIEW", "Transaction held for secondary verification or 2FA OTP prompt."),
        ("HIGH RISK", "60.0% - 84.9%", "DECLINE", "Transaction declined due to elevated fraud indicators."),
        ("CRITICAL RISK", "85.0% - 100.0%", "BLOCK", "Transaction blocked immediately; compliance audit alert generated.")
    ]
    for row_idx, data in enumerate(risk_data, start=1):
        bg = "F0FDF4" if row_idx == 1 else "FEFCE8" if row_idx == 2 else "FFF7ED" if row_idx == 3 else "FEF2F2"
        for col_idx, text in enumerate(data):
            cell = table_risk.cell(row_idx, col_idx)
            set_cell_background(cell, bg)
            p = cell.paragraphs[0]
            p.add_run(text)

    doc.add_paragraph()

    # 5. DATASET BATCH SCANNING & DATA FLOW PIPELINE
    add_heading_1("5. Dataset Batch Screening & Data Flow Pipeline")
    add_body_p(
        "For bulk dataset processing, Gojo Sentinel implements an interactive 4-stage data pipeline with real-time visual progress tracking:"
    )
    add_bullet("Stage 1 — CSV Ingestion", "Uploads and parses raw transaction records, validating schema and data types.")
    add_bullet("Stage 2 — Banking Rules Verification", "Executes bulk evaluation against CBN policy thresholds and flags violations.")
    add_bullet("Stage 3 — AI Fraud Model Scoring", "Passes feature vectors through the XGBoost engine to calculate individual risk scores.")
    add_bullet("Stage 4 — Risk Verdict & Audit Generation", "Generates summary statistics, interactive doughnut charts, and a filterable audited table exportable as CSV.")

    # 6. FRONTEND USER EXPERIENCE & DESIGN SYSTEM
    add_heading_1("6. Frontend Interface & User Experience Design")
    add_body_p(
        "The user interface incorporates modern web design standards tailored for high-density financial monitoring:"
    )
    add_bullet("Gemini-Style Collapsible Rail Sidebar", "Supports both Expanded Mode (260px with branding & text labels) and Collapsible Rail Mode (72px compact icon bar with centered SVGs and tooltips).")
    add_bullet("Real-Time Execution Console & Progress Bar", "Includes a dark green terminal logger streaming live timestamped pipeline logs alongside a smooth 0-100% progress bar.")
    add_bullet("30-Day Activity Trend Chart", "Permanently displayed on the main dashboard, dynamically updating legitimate vs. fraudulent volume trends in real time.")
    add_bullet("Vector SVG Design System", "All UI components use scalable SVG vector graphics instead of raster graphics or emojis for a professional, crisp financial software aesthetic.")

    # 7. MULTI-PLATFORM DEPLOYMENT & SECURITY
    add_heading_1("7. Multi-Platform Deployment & Security Framework")
    add_bullet("Cloud Hosting", "Backend and Web Frontend hosted on Hugging Face Spaces with Docker containerization.")
    add_bullet("Mobile Android APK", "Packaged using Apache Cordova, providing native mobile functionality across Android devices.")
    add_bullet("Authentication & Security", "JWT (JSON Web Token) authentication with role-based access control (Admin / Analyst roles).")

    # Save document
    filename_docx = "Gojo_Sentinel_System_Presentation_Document.docx"
    doc.save(filename_docx)
    print(f"[SUCCESS] Microsoft Word document created successfully: {filename_docx}")

    # Also generate Markdown version
    md_content = f"""# 🛡️ GOJO SENTINEL
## Hybrid Transaction Fraud Detection & Regulatory Compliance System for Nigerian Banking

---

### **Executive Summary**
Gojo Sentinel is an enterprise-grade, hybrid artificial intelligence and regulatory compliance transaction screening platform built specifically for the Nigerian financial ecosystem. Financial fraud in Nigeria across electronic payment channels—such as NIBSS Instant Payments (NIP), USSD banking, Mobile Money, and Web portals—poses critical security challenges. Gojo Sentinel addresses these risks by coupling deterministic Central Bank of Nigeria (CBN) regulatory compliance rules with probabilistic Machine Learning (XGBoost) fraud scoring.

The system processes both single real-time transactions and large bulk datasets (CSV), delivering sub-second risk classification across four distinct verdicts: **APPROVE (Low Risk)**, **REVIEW (Medium Risk)**, **DECLINE (High Risk)**, and **BLOCK (Critical Policy Breach)**.

---

### **1. System Architecture & Design**
The system operates on a dual-engine architecture designed to ensure zero tolerance for statutory regulatory breaches while maintaining ultra-low false-positive rates using machine learning:

| Layer / Module | Technology Stack | Functional Purpose |
| :--- | :--- | :--- |
| **Backend REST API** | FastAPI / Python 3.10+ | High-throughput asynchronous API serving real-time prediction and dataset batch processing. |
| **Compliance Engine** | Deterministic Rule Set (CBN) | Instant verification against USSD caps, NIP single transfer limits, velocity thresholds, and restricted bank lists. |
| **AI Machine Learning Engine** | XGBoost Classifier | Probabilistic feature evaluation calculating exact fraud likelihood percentages based on historical transaction dynamics. |
| **User Interface (Web & Mobile)** | HTML5, Vanilla CSS, JS, Cordova | Responsive single-page web app & Cordova mobile APK featuring Gemini-style Collapsible Rail Sidebar, Live Terminal Logs, and Trend Analytics. |

---

### **2. Central Bank of Nigeria (CBN) Compliance Module**
- **USSD Transfer Caps**: Transactions initiated via USSD channel (`*901#`, `*737#`, `*894#`, etc.) exceeding **₦100,000 NGN** daily limit are automatically flagged as `CRITICAL` / `BLOCK` violations.
- **NIP Single Transfer Limit**: Single transfers over NIBSS Instant Payment (NIP) exceeding **₦5,000,000 NGN** are flagged for mandatory compliance review.
- **Midnight Velocity Spikes**: High-value transfers occurring between 11:00 PM and 04:30 AM are subjected to elevated risk scoring due to historical fraud correlation during non-operating hours.
- **Restricted Bank List**: Automatic flagging of transactions routed to or from high-risk accounts or institutions with active regulatory flags.

---

### **3. Risk Verdict Matrix**
| Risk Level | Probability Score | Action / Verdict | System Behavior |
| :--- | :--- | :--- | :--- |
| **LOW RISK** | 0.0% - 29.9% | **APPROVE** | Transaction cleared automatically without friction. |
| **MEDIUM RISK** | 30.0% - 59.9% | **REVIEW** | Transaction held for secondary verification or 2FA OTP prompt. |
| **HIGH RISK** | 60.0% - 84.9% | **DECLINE** | Transaction declined due to elevated fraud indicators. |
| **CRITICAL RISK** | 85.0% - 100.0% | **BLOCK** | Transaction blocked immediately; compliance audit alert generated. |

---

### **4. Dataset Batch Screening & Data Flow Pipeline**
1. **Stage 1 — CSV Ingestion**: Uploads and parses raw transaction records, validating schema and data types.
2. **Stage 2 — Banking Rules Verification**: Executed bulk evaluation against CBN policy thresholds and flags violations.
3. **Stage 3 — AI Fraud Model Scoring**: Passes feature vectors through the XGBoost engine to calculate individual risk scores.
4. **Stage 4 — Risk Verdict & Audit Generation**: Generates summary statistics, interactive doughnut charts, and a filterable audited table exportable as CSV.

---

### **5. Frontend Interface & User Experience**
- **Gemini-Style Collapsible Rail Sidebar**: Supports both Expanded Mode (260px with branding & text labels) and Collapsible Rail Mode (72px compact icon bar with centered SVGs and tooltips).
- **Real-Time Execution Console & Progress Bar**: Includes a dark green terminal logger streaming live timestamped pipeline logs alongside a smooth 0-100% progress bar.
- **30-Day Activity Trend Chart**: Permanently displayed on the main dashboard, dynamically updating legitimate vs. fraudulent volume trends in real time.
- **Vector SVG Design System**: All UI components use scalable SVG vector graphics instead of raster graphics or emojis for a professional, crisp financial software aesthetic.

---

### **6. Multi-Platform Deployment & Security**
- **Cloud Hosting**: Backend and Web Frontend hosted on Hugging Face Spaces with Docker containerization.
- **Mobile Android APK**: Packaged using Apache Cordova, providing native mobile functionality across Android devices.
- **Authentication & Security**: JWT (JSON Web Token) authentication with role-based access control (Admin / Analyst roles).
"""

    with open("GOJO_SENTINEL_SYSTEM_DOCUMENTATION.md", "w", encoding="utf-8") as f:
        f.write(md_content)
    print("[SUCCESS] Markdown documentation created successfully: GOJO_SENTINEL_SYSTEM_DOCUMENTATION.md")

if __name__ == "__main__":
    create_document()
