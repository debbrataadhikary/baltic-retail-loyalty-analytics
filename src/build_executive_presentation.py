import os
import subprocess
import docx
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

BASE_DIR = r"d:\DW- Internship\Lidl-Loyalty-Data-Analyst\baltic-retail-loyalty-analytics"

doc = docx.Document()
for s in doc.sections:
    s.page_width = Cm(21.0)
    s.page_height = Cm(29.7)
    s.top_margin = Cm(1.3)
    s.bottom_margin = Cm(1.3)
    s.left_margin = Cm(1.5)
    s.right_margin = Cm(1.5)

FONT_NAME = "Calibri"
COLOR_NAVY = RGBColor(0x00, 0x38, 0x76)
COLOR_TEXT = RGBColor(0x1E, 0x24, 0x2B)
COLOR_MUTED = RGBColor(0x52, 0x5E, 0x6C)

def add_bottom_border(paragraph, color_hex="003876", sz="10", space="3"):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), sz)
    bottom.set(qn('w:space'), space)
    bottom.set(qn('w:color'), color_hex)
    pBdr.append(bottom)
    pPr.append(pBdr)

def add_heading(title):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(title.upper())
    r.bold = True
    r.font.name = FONT_NAME
    r.font.size = Pt(11)
    r.font.color.rgb = COLOR_NAVY
    add_bottom_border(p, color_hex="003876", sz="8", space="2")
    return p

# Title Banner
p_t = doc.add_paragraph()
p_t.paragraph_format.space_before = Pt(0)
p_t.paragraph_format.space_after = Pt(2)
rt = p_t.add_run("BALTICPLUS LOYALTY & PROMOTIONAL ANALYTICS — EXECUTIVE BOARD REPORT")
rt.bold = True
rt.font.name = FONT_NAME
rt.font.size = Pt(16.5)
rt.font.color.rgb = COLOR_NAVY

p_sub = doc.add_paragraph()
p_sub.paragraph_format.space_before = Pt(0)
p_sub.paragraph_format.space_after = Pt(5)
rs = p_sub.add_run(
    "POS Data Quality Pipeline • Statistical A/B Testing (DiD) • Cohort Retention & 12M CLV • Market Basket Affinity • Q4 Budget Optimizer\n"
    "Author: Debbrata Kumar Adhikary (Vilnius, Lithuania)  |  Scope: 140 Baltic Stores (LT, LV, EE) • 50,000 Loyalty Members • 520,000 Validated Baskets"
)
rs.bold = True
rs.font.name = FONT_NAME
rs.font.size = Pt(9.0)
rs.font.color.rgb = COLOR_MUTED
add_bottom_border(p_sub, color_hex="D0D7DE", sz="6", space="4")

# Section 1
add_heading("1. Executive Overview & Baltic Market Performance (LT, LV, EE)")
p1 = doc.add_paragraph()
p1.paragraph_format.line_spacing = 1.12
p1.paragraph_format.space_after = Pt(3)
r1 = p1.add_run(
    "Across 528,390 raw POS transaction records ingested from 140 Baltic stores (87 in Lithuania, 30 in Latvia, 23 in Estonia), "
    "our automated SQL and Python data quality pipeline removed 3,420 duplicate receipt scans, isolated 2,180 negative refund rows, "
    "imputed 1,150 missing store terminal IDs, and reconciled 1,640 unredeemed coupon glitches—yielding 520,000 validated Gold-layer baskets "
    "representing €13.08M in net sales (68.0% Loyalty scan share; 79.1% revenue share; +€12.83 / +78.1% basket uplift vs. non-loyalty guests)."
)
r1.font.name = FONT_NAME
r1.font.size = Pt(9.2)
r1.font.color.rgb = COLOR_TEXT

ch3 = os.path.join(BASE_DIR, "assets/charts/03_baltic_country_basket_comparison.png")
if os.path.exists(ch3):
    p_img3 = doc.add_paragraph()
    p_img3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img3.paragraph_format.space_after = Pt(2)
    p_img3.add_run().add_picture(ch3, width=Cm(11.2))

# Section 2
add_heading("2. Campaign Pre/Post Incrementality, Statistical A/B Testing (Welch's t-Test) & Causal Uplift")
p2 = doc.add_paragraph()
p2.paragraph_format.line_spacing = 1.12
p2.paragraph_format.space_after = Pt(3)
r2 = p2.add_run(
    "Evaluating campaigns solely by redemption count hides two major margin leaks: (1) Cannibalization (subsidizing loyal customers who would have "
    "bought the item at full price) and (2) Pantry-Loading / Stockpiling (where deep discounts on non-perishables cause a -26.5% sales collapse in the "
    "4 weeks post-campaign). Using Difference-in-Differences (DiD) against unexposed holdout control groups and Welch's two-sample t-tests (p < 0.0001), "
    "we proved that Basket Stretch Thresholds (+€26.05 causal net lift) and Fresh Category Coupons (+€14.75 to +€14.95 causal lift) generate highly "
    "significant positive ROI, whereas standalone deep discounts on Coffee (-35%), Oil (BOGO), and Detergent (-40%) destroy -€11.36 per basket."
)
r2.font.name = FONT_NAME
r2.font.size = Pt(9.2)
r2.font.color.rgb = COLOR_TEXT

ch5 = os.path.join(BASE_DIR, "assets/charts/05_ab_testing_causal_uplift_forest_plot.png")
if os.path.exists(ch5):
    p_img5 = doc.add_paragraph()
    p_img5.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img5.paragraph_format.space_after = Pt(2)
    p_img5.add_run().add_picture(ch5, width=Cm(14.8))

# Section 3
add_heading("3. Monthly Retention Cohort Matrix, 12-Month CLV & 30-Day Churn Risk Scoring")
p3 = doc.add_paragraph()
p3.paragraph_format.line_spacing = 1.12
p3.paragraph_format.space_after = Pt(3)
r3 = p3.add_run(
    "Tracking monthly acquisition cohorts from April to September 2026 shows Month+1 retention improving from 78.4% to 84.1% as onboarding coupon "
    "workflows matured, stabilizing at 55.4% active retention by Month+5. Predictive 12-month Customer Lifetime Value (CLV) and 30-day churn risk "
    "modeling across our 50,000 members identifies €3,480 annual CLV among VIP Full-Basket Families (6.4% churn risk) vs. 68.4% churn risk among "
    "6,000 At-Risk / Slipping shoppers (€160.9k annual revenue at immediate risk, recoverable via automated Day-18 '€4 Off €25' push triggers)."
)
r3.font.name = FONT_NAME
r3.font.size = Pt(9.2)
r3.font.color.rgb = COLOR_TEXT

ch6 = os.path.join(BASE_DIR, "assets/charts/06_cohort_retention_and_clv.png")
if os.path.exists(ch6):
    p_img6 = doc.add_paragraph()
    p_img6.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img6.paragraph_format.space_after = Pt(2)
    p_img6.add_run().add_picture(ch6, width=Cm(15.2))

# Section 4
add_heading("4. Market Basket Affinity (Apriori) & Q4 €625k Promotional Budget Optimization")
p4 = doc.add_paragraph()
p4.paragraph_format.line_spacing = 1.12
p4.paragraph_format.space_after = Pt(3)
r4 = p4.add_run(
    "Apriori association rule mining proves that Fresh Bakery coupons drive a 3.12x cross-category Lift into Dairy & Cheese (€9.45 attached halo spend), "
    "and Weekend Grill Meat coupons drive a 2.88x Lift into Fresh Produce & Beverages (€14.20 attached halo spend). Conversely, standalone Coffee and "
    "Cooking Oil promos exhibit <0.80x Lift (cherry-picked in isolation). Reallocating €171,000 away from standalone deep discounts into High-Halo Fresh "
    "and €30/€40 Basket Thresholds under a budget-neutral €625,000 Q4 plan increases projected quarterly Net Incremental Margin from €457.3k to €813.4k (+€356.0k / +77.8%)."
)
r4.font.name = FONT_NAME
r4.font.size = Pt(9.2)
r4.font.color.rgb = COLOR_TEXT

ch7 = os.path.join(BASE_DIR, "assets/charts/07_market_basket_affinity_lift.png")
if os.path.exists(ch7):
    p_img7 = doc.add_paragraph()
    p_img7.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img7.paragraph_format.space_after = Pt(2)
    p_img7.add_run().add_picture(ch7, width=Cm(14.6))

ch8 = os.path.join(BASE_DIR, "assets/charts/08_q4_promotional_budget_optimizer.png")
if os.path.exists(ch8):
    p_img8 = doc.add_paragraph()
    p_img8.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img8.paragraph_format.space_after = Pt(0)
    p_img8.add_run().add_picture(ch8, width=Cm(14.8))

out_docx = os.path.join(BASE_DIR, "deliverables/Executive_Presentation_Baltic_Loyalty_Analytics.docx")
out_pdf = os.path.join(BASE_DIR, "deliverables/Executive_Presentation_Baltic_Loyalty_Analytics.pdf")
doc.save(out_docx)
print("Saved Executive Presentation docx:", out_docx)

try:
    from docx2pdf import convert
    convert(out_docx, out_pdf)
    print("Converted Executive Presentation to PDF:", out_pdf)
except Exception as e:
    print("docx2pdf fallback check:", e)
