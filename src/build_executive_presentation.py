import os
import docx
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

BASE_DIR = r"d:\DW- Internship\Lidl-Loyalty-Data-Analyst\baltic-retail-loyalty-analytics"

doc = docx.Document()
for s in doc.sections:
    s.page_width = Cm(21.0)
    s.page_height = Cm(29.7)
    s.top_margin = Cm(1.4)
    s.bottom_margin = Cm(1.4)
    s.left_margin = Cm(1.6)
    s.right_margin = Cm(1.6)

FONT_NAME = "Calibri"
COLOR_NAVY = RGBColor(0x00, 0x38, 0x76)
COLOR_ACCENT = RGBColor(0x00, 0x50, 0xAA)
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
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(title.upper())
    r.bold = True
    r.font.name = FONT_NAME
    r.font.size = Pt(11.5)
    r.font.color.rgb = COLOR_NAVY
    add_bottom_border(p, color_hex="003876", sz="8", space="2")
    return p

# Title Banner
p_t = doc.add_paragraph()
p_t.paragraph_format.space_before = Pt(0)
p_t.paragraph_format.space_after = Pt(2)
rt = p_t.add_run("BALTICPLUS LOYALTY & PROMOTIONAL ANALYTICS — BOARD REPORT")
rt.bold = True
rt.font.name = FONT_NAME
rt.font.size = Pt(17)
rt.font.color.rgb = COLOR_NAVY

p_sub = doc.add_paragraph()
p_sub.paragraph_format.space_before = Pt(0)
p_sub.paragraph_format.space_after = Pt(6)
rs = p_sub.add_run(
    "End-to-End POS Sales Data Cleaning • Pre/Post Campaign Incrementality • Basket Halo Effect • Customer RFM Segmentation\n"
    "Author: Debbrata Kumar Adhikary (Vilnius, Lithuania)  |  Scope: 140 Baltic Stores (LT, LV, EE) • 50,000 Loyalty Members • 520,000 Validated Baskets"
)
rs.bold = True
rs.font.name = FONT_NAME
rs.font.size = Pt(9.5)
rs.font.color.rgb = COLOR_MUTED
add_bottom_border(p_sub, color_hex="D0D7DE", sz="6", space="4")

# Section 1
add_heading("1. Executive Overview & Baltic Market Performance (LT, LV, EE)")
p1 = doc.add_paragraph()
p1.paragraph_format.line_spacing = 1.15
p1.paragraph_format.space_after = Pt(4)
r1 = p1.add_run(
    "Across 528,390 raw POS transaction records ingested from 140 Baltic stores (87 in Lithuania, 30 in Latvia, 23 in Estonia), "
    "our automated SQL and Python data quality pipeline removed 3,420 duplicate receipt scans, isolated 2,180 negative refund rows, "
    "imputed 1,150 missing store terminal IDs, and reconciled 1,640 unredeemed coupon glitches—yielding 520,000 validated Gold-layer baskets "
    "representing €13.08M in net sales.\n"
    "• Loyalty App Penetration: 68.0% of all Baltic transactions and 79.1% of total net revenue (€10.35M) are generated via Loyalty App scans.\n"
    "• Basket Value Uplift: Loyalty App baskets average €29.26 compared to €16.43 for non-loyalty guest baskets—an uplift of +€12.83 (+78.1%) per visit."
)
r1.font.name = FONT_NAME
r1.font.size = Pt(9.5)
r1.font.color.rgb = COLOR_TEXT

ch3 = os.path.join(BASE_DIR, "assets/charts/03_baltic_country_basket_comparison.png")
if os.path.exists(ch3):
    p_img3 = doc.add_paragraph()
    p_img3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img3.paragraph_format.space_after = Pt(2)
    p_img3.add_run().add_picture(ch3, width=Cm(11.8))

# Section 2
add_heading("2. End-to-End Campaign Pre/Post Incrementality & Market Basket Halo Effect")
p2 = doc.add_paragraph()
p2.paragraph_format.line_spacing = 1.12
p2.paragraph_format.space_after = Pt(3)
r2 = p2.add_run(
    "Evaluating campaigns solely by redemption count hides two major margin leaks: (1) Cannibalization (subsidizing loyal customers who would have "
    "bought the item at full price) and (2) Pantry-Loading / Stockpiling (where deep discounts on non-perishables cause a -26.5% sales collapse in the "
    "4 weeks post-campaign). Using Difference-in-Differences across 4 weeks Pre, Promo Week, and 4 weeks Post, we classified all 12 campaigns:"
)
r2.font.name = FONT_NAME
r2.font.size = Pt(9.5)
r2.font.color.rgb = COLOR_TEXT

ch1 = os.path.join(BASE_DIR, "assets/charts/01_campaign_net_incremental_roi.png")
if os.path.exists(ch1):
    p_img1 = doc.add_paragraph()
    p_img1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img1.paragraph_format.space_after = Pt(2)
    p_img1.add_run().add_picture(ch1, width=Cm(14.5))

ch2 = os.path.join(BASE_DIR, "assets/charts/02_pre_post_campaign_trajectory.png")
if os.path.exists(ch2):
    p_img2 = doc.add_paragraph()
    p_img2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img2.paragraph_format.space_after = Pt(2)
    p_img2.add_run().add_picture(ch2, width=Cm(12.8))

# Section 3
add_heading("3. Customer RFM & Promo-Sensitivity Segmentation & Strategic Board Recommendations")
p3 = doc.add_paragraph()
p3.paragraph_format.line_spacing = 1.12
p3.paragraph_format.space_after = Pt(3)
r3 = p3.add_run(
    "By combining RFM (Recency, Frequency, Monetary) scores with each customer's Coupon Dependency Ratio (%), we identified that 10,899 members "
    "(21.8% of the user base) act as 'Promo-Driven Cherry Pickers'—redeeming coupons on 78.1% of visits but generating an average attached non-promo "
    "basket of only €3.33 on deep item deals.\n"
    "• Recommendation 1 (Gate Deep Discounts Behind a €20 Basket Threshold): Requiring a minimum €20 total basket spend to unlock -35%/-40% coupons on Coffee, Oil, and Detergent eliminates cherry-picking and recovers an estimated €168,400 in annual Baltic retail margin.\n"
    "• Recommendation 2 (Reallocate Promo Budget to High-Halo Fresh Categories): Shift 25% of non-perishable promo budget into Fresh Meat, Produce, and Bakery app coupons, which generate €33.80+ in attached cross-category spend and +289% to +479% Net ROI.\n"
    "• Recommendation 3 (Automated Day-18 Churn Win-Back Trigger): Deploy an automated '€4 Off €25' push coupon when an active shopper reaches 18 days without a POS scan, capturing slipping shoppers before the 21-day churn cliff."
)
r3.font.name = FONT_NAME
r3.font.size = Pt(9.5)
r3.font.color.rgb = COLOR_TEXT

ch4 = os.path.join(BASE_DIR, "assets/charts/04_customer_segmentation_matrix.png")
if os.path.exists(ch4):
    p_img4 = doc.add_paragraph()
    p_img4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img4.paragraph_format.space_after = Pt(0)
    p_img4.add_run().add_picture(ch4, width=Cm(13.2))

out_docx = os.path.join(BASE_DIR, "deliverables/Executive_Presentation_Baltic_Loyalty_Analytics.docx")
doc.save(out_docx)
print("Saved Executive Presentation docx:", out_docx)
