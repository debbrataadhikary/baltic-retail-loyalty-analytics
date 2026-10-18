import os
import json
import zipfile
import sqlite3
import pandas as pd
import numpy as np

BASE_DIR = r"d:\DW- Internship\Lidl-Loyalty-Data-Analyst\baltic-retail-loyalty-analytics"
PBI_DIR = os.path.join(BASE_DIR, "powerbi")
SM_DIR = os.path.join(PBI_DIR, "BalticPlus_Loyalty_Analytics.SemanticModel")
RPT_DIR = os.path.join(PBI_DIR, "BalticPlus_Loyalty_Analytics.Report")
STATIC_THEME_DIR = os.path.join(RPT_DIR, "StaticResources", "SharedResources", "BaseThemes")

for d in [PBI_DIR, SM_DIR, RPT_DIR, STATIC_THEME_DIR]:
    os.makedirs(d, exist_ok=True)

ref_pbix = r"D:\Google Data Analytics\SQL-Ecommoerce Project\E-Commerce_Churn_&_RFM_Dashboard.pbix"
if os.path.exists(ref_pbix):
    with zipfile.ZipFile(ref_pbix, "r") as z:
        theme_bytes = z.read("Report/StaticResources/SharedResources/BaseThemes/CY25SU11.json")
        with open(os.path.join(STATIC_THEME_DIR, "CY25SU11.json"), "wb") as tf:
            tf.write(theme_bytes)

data_dir_escaped = os.path.join(BASE_DIR, "data", "processed").replace("\\", "\\\\")
reports_dir_escaped = os.path.join(BASE_DIR, "reports").replace("\\", "\\\\")

def make_csv_table(tname, folder_escaped, filename, cols_spec, measures=None):
    columns = []
    m_types = []
    for cname, dtype, pq_type, summarize in cols_spec:
        col_obj = {
            "name": cname,
            "dataType": dtype,
            "sourceColumn": cname,
            "summarizeBy": summarize
        }
        if dtype == "double":
            col_obj["annotations"] = [{"name": "PBI_FormatHint", "value": "{\"isGeneralNumber\":true}"}]
        columns.append(col_obj)
        m_types.append(f"{{\"{cname}\", {pq_type}}}")

    types_str = ", ".join(m_types)
    tbl = {
        "name": tname,
        "columns": columns,
        "partitions": [{
            "name": tname,
            "mode": "import",
            "source": {
                "type": "m",
                "expression": [
                    "let",
                    f"    Source = Csv.Document(File.Contents(\"{folder_escaped}\\\\{filename}\"),[Delimiter=\",\", Columns={len(cols_spec)}, Encoding=65001, QuoteStyle=QuoteStyle.None]),",
                    "    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
                    f"    ChangedType = Table.TransformColumnTypes(PromotedHeaders,{{{types_str}}})",
                    "in",
                    "    ChangedType"
                ]
            }
        }],
        "annotations": [
            {"name": "PBI_NavigationStepName", "value": "Navigation"},
            {"name": "PBI_ResultType", "value": "Table"}
        ]
    }
    if measures:
        tbl["measures"] = measures
    return tbl

t_country = make_csv_table(
    "baltic_executive_country_kpis",
    reports_dir_escaped,
    "baltic_executive_country_kpis.csv",
    [
        ("Country", "string", "type text", "none"),
        ("Country_Code", "string", "type text", "none"),
        ("Active_Stores", "int64", "Int64.Type", "sum"),
        ("Total_Transactions", "int64", "Int64.Type", "sum"),
        ("Total_Net_Sales_EUR", "double", "type number", "sum"),
        ("Loyalty_Scan_Share_Pct", "double", "type number", "average"),
        ("Loyalty_Revenue_Share_Pct", "double", "type number", "average"),
        ("Avg_Basket_Loyalty_EUR", "double", "type number", "average"),
        ("Avg_Basket_Guest_EUR", "double", "type number", "average"),
        ("Basket_Uplift_EUR", "double", "type number", "average"),
        ("Basket_Uplift_Pct", "double", "type number", "average"),
        ("Coupon_Redemption_Rate_Pct", "double", "type number", "average"),
        ("Total_Promo_Discount_EUR", "double", "type number", "sum")
    ],
    measures=[
        {"name": "Total Baltic Net Sales (€)", "expression": "SUM(baltic_executive_country_kpis[Total_Net_Sales_EUR])", "formatString": "€#,0"},
        {"name": "Total Validated POS Baskets", "expression": "SUM(baltic_executive_country_kpis[Total_Transactions])", "formatString": "#,0"},
        {"name": "Loyalty Basket (€)", "expression": "AVERAGE(baltic_executive_country_kpis[Avg_Basket_Loyalty_EUR])", "formatString": "€#,0.00"},
        {"name": "Guest Basket (€)", "expression": "AVERAGE(baltic_executive_country_kpis[Avg_Basket_Guest_EUR])", "formatString": "€#,0.00"},
        {"name": "Loyalty Scan Share (%)", "expression": "AVERAGE(baltic_executive_country_kpis[Loyalty_Scan_Share_Pct]) / 100", "formatString": "0.0%"}
    ]
)

t_camp_roi = make_csv_table(
    "campaign_pre_post_incrementality_roi",
    reports_dir_escaped,
    "campaign_pre_post_incrementality_roi.csv",
    [
        ("campaign_id", "string", "type text", "none"),
        ("campaign_name", "string", "type text", "none"),
        ("mechanic_type", "string", "type text", "none"),
        ("target_category", "string", "type text", "none"),
        ("nominal_discount_pct", "double", "type number", "average"),
        ("planned_budget_eur", "double", "type number", "sum"),
        ("commercial_classification", "string", "type text", "none"),
        ("Redemptions", "int64", "Int64.Type", "sum"),
        ("Avg_Promo_Item_Spend_EUR", "double", "type number", "average"),
        ("Avg_Halo_Other_Spend_EUR", "double", "type number", "average"),
        ("Avg_Gross_Basket_EUR", "double", "type number", "average"),
        ("Avg_Net_Basket_EUR", "double", "type number", "average"),
        ("Total_Gross_Revenue_EUR", "double", "type number", "sum"),
        ("Total_Discount_Cost_EUR", "double", "type number", "sum"),
        ("Total_Net_Revenue_EUR", "double", "type number", "sum"),
        ("Total_Net_Margin_EUR", "double", "type number", "sum"),
        ("Cannibalization_Rate_Pct", "double", "type number", "average"),
        ("Post_Campaign_Pantry_Dip_Pct", "double", "type number", "average"),
        ("Cherry_Picker_Share_Pct", "double", "type number", "average"),
        ("True_Incremental_Revenue_EUR", "double", "type number", "sum"),
        ("Net_Incremental_Margin_EUR", "double", "type number", "sum"),
        ("Net_Campaign_ROI_Pct", "double", "type number", "average"),
        ("Budget_Utilization_Pct", "double", "type number", "average"),
        ("Budget_Variance_EUR", "double", "type number", "sum")
    ]
)

t_rfm = make_csv_table(
    "customer_rfm_promo_segmentation",
    reports_dir_escaped,
    "customer_rfm_promo_segmentation.csv",
    [
        ("customer_archetype", "string", "type text", "none"),
        ("Total_Transactions", "int64", "Int64.Type", "sum"),
        ("Unique_Customers", "int64", "Int64.Type", "sum"),
        ("Avg_Net_Basket_EUR", "double", "type number", "average"),
        ("Avg_Items_Per_Basket", "double", "type number", "average"),
        ("Coupon_Usage_Rate_Pct", "double", "type number", "average"),
        ("Total_Net_Sales_EUR", "double", "type number", "sum"),
        ("Total_Discount_Claimed_EUR", "double", "type number", "sum"),
        ("Total_Net_Margin_EUR", "double", "type number", "sum"),
        ("Recommended_CRM_Action", "string", "type text", "none")
    ]
)

t_funnel = make_csv_table(
    "loyalty_app_customer_journey_funnel",
    reports_dir_escaped,
    "loyalty_app_customer_journey_funnel.csv",
    [
        ("Stage_Order", "int64", "Int64.Type", "sum"),
        ("Funnel_Stage", "string", "type text", "none"),
        ("Users_Count", "int64", "Int64.Type", "sum"),
        ("Conversion_From_Prev_Pct", "double", "type number", "average"),
        ("Overall_Penetration_Pct", "double", "type number", "average")
    ]
)

t_stores = make_csv_table(
    "dim_stores",
    data_dir_escaped,
    "dim_stores.csv",
    [
        ("store_id", "string", "type text", "none"),
        ("country", "string", "type text", "none"),
        ("country_code", "string", "type text", "none"),
        ("city", "string", "type text", "none"),
        ("store_format", "string", "type text", "none"),
        ("opening_year", "int64", "Int64.Type", "none")
    ]
)

t_pos = make_csv_table(
    "fact_pos_transactions_gold",
    data_dir_escaped,
    "fact_pos_transactions_gold.csv",
    [
        ("transaction_id", "string", "type text", "none"),
        ("transaction_date", "string", "type text", "none"),
        ("fiscal_week", "int64", "Int64.Type", "none"),
        ("country_code", "string", "type text", "none"),
        ("store_id", "string", "type text", "none"),
        ("is_loyalty_scan", "int64", "Int64.Type", "sum"),
        ("customer_id", "string", "type text", "none"),
        ("customer_archetype", "string", "type text", "none"),
        ("coupon_applied", "int64", "Int64.Type", "sum"),
        ("campaign_id", "string", "type text", "none"),
        ("items_count", "int64", "Int64.Type", "sum"),
        ("promo_item_spend_eur", "double", "type number", "sum"),
        ("non_promo_halo_spend_eur", "double", "type number", "sum"),
        ("gross_basket_eur", "double", "type number", "sum"),
        ("discount_amount_eur", "double", "type number", "sum"),
        ("net_sales_eur", "double", "type number", "sum"),
        ("net_margin_eur", "double", "type number", "sum"),
        ("record_status", "string", "type text", "none")
    ],
    measures=[
        {"name": "Total Net Sales (€)", "expression": "SUM(fact_pos_transactions_gold[net_sales_eur])", "formatString": "€#,0.00"},
        {"name": "Total Validated Baskets", "expression": "DISTINCTCOUNT(fact_pos_transactions_gold[transaction_id])", "formatString": "#,0"},
        {"name": "Average Net Basket (€)", "expression": "DIVIDE([Total Net Sales (€)], [Total Validated Baskets], 0)", "formatString": "€#,0.00"},
        {"name": "Loyalty Scan Penetration (%)", "expression": "DIVIDE(CALCULATE([Total Validated Baskets], fact_pos_transactions_gold[is_loyalty_scan]=1), [Total Validated Baskets], 0)", "formatString": "0.0%"},
        {"name": "Avg Loyalty Basket (€)", "expression": "CALCULATE([Average Net Basket (€)], fact_pos_transactions_gold[is_loyalty_scan]=1)", "formatString": "€#,0.00"},
        {"name": "Avg Guest Basket (€)", "expression": "CALCULATE([Average Net Basket (€)], fact_pos_transactions_gold[is_loyalty_scan]=0)", "formatString": "€#,0.00"},
        {"name": "Loyalty Basket Uplift (€)", "expression": "[Avg Loyalty Basket (€)] - [Avg Guest Basket (€)]", "formatString": "+€#,0.00;-€#,0.00;€0.00"}
    ]
)

model_bim = {
    "name": "SemanticModel",
    "compatibilityLevel": 1550,
    "model": {
        "culture": "en-US",
        "dataAccessOptions": {
            "legacyRedirects": True,
            "returnErrorValuesAsNull": True
        },
        "defaultPowerBIDataSourceVersion": "powerBI_V3",
        "sourceQueryCulture": "en-US",
        "tables": [t_country, t_camp_roi, t_rfm, t_funnel, t_stores, t_pos],
        "relationships": [
            {
                "name": "rel_store_pos",
                "fromTable": "fact_pos_transactions_gold",
                "fromColumn": "store_id",
                "toTable": "dim_stores",
                "toColumn": "store_id"
            },
            {
                "name": "rel_camp_pos",
                "fromTable": "fact_pos_transactions_gold",
                "fromColumn": "campaign_id",
                "toTable": "campaign_pre_post_incrementality_roi",
                "toColumn": "campaign_id"
            }
        ],
        "annotations": [
            {
                "name": "PBI_QueryOrder",
                "value": "[\"baltic_executive_country_kpis\",\"campaign_pre_post_incrementality_roi\",\"customer_rfm_promo_segmentation\",\"loyalty_app_customer_journey_funnel\",\"dim_stores\",\"fact_pos_transactions_gold\"]"
            },
            {
                "name": "__PBI_TimeIntelligenceEnabled",
                "value": "1"
            }
        ]
    }
}

with open(os.path.join(SM_DIR, "model.bim"), "w", encoding="utf-8") as f:
    json.dump(model_bim, f, indent=2)

# =====================================================================================
# BUILD EXECUTIVE-GRADE DARK-NAVY & LIDL-STYLED DASHBOARD CANVAS (report.json)
# =====================================================================================

# 1. Top Header Banner (Styled Title Card)
v_header = {
    "x": 12, "y": 8, "z": 500, "width": 1256, "height": 46,
    "config": json.dumps({
        "name": "hdrBanner01",
        "layouts": [{"id": 0, "position": {"x": 12, "y": 8, "z": 500, "width": 1256, "height": 46, "tabOrder": 500}}],
        "singleVisual": {
            "visualType": "textbox",
            "objects": {
                "general": [{
                    "properties": {
                        "paragraphs": [{
                            "textRuns": [{
                                "value": "BALTICPLUS LOYALTY & PROMOTIONAL ANALYTICS — EXECUTIVE BOARD DASHBOARD (LT • LV • EE)",
                                "textStyle": {"fontWeight": "bold", "fontSize": "15pt", "color": "#FFF000"}
                            }],
                            "horizontalTextAlignment": "center"
                        }]
                    }
                }]
            },
            "vcObjects": {
                "background": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#002B5C'"}}}}}, "transparency": {"expr": {"Literal": {"Value": "0D"}}}}}],
                "border": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFF000'"}}}}}, "width": {"expr": {"Literal": {"Value": "2D"}}}}}]
            }
        }
    })
}

# 2. Top Row Multi-Metric Executive KPI Card (cardVisual)
v_kpis = {
    "x": 12, "y": 60, "z": 1000, "width": 960, "height": 115,
    "config": json.dumps({
        "name": "kpiCardsRow01",
        "layouts": [{"id": 0, "position": {"x": 12, "y": 60, "z": 1000, "width": 960, "height": 115, "tabOrder": 1000}}],
        "singleVisual": {
            "visualType": "cardVisual",
            "projections": {
                "Data": [
                    {"queryRef": "baltic_executive_country_kpis.Total Baltic Net Sales (€)"},
                    {"queryRef": "baltic_executive_country_kpis.Total Validated POS Baskets"},
                    {"queryRef": "baltic_executive_country_kpis.Loyalty Scan Share (%)"},
                    {"queryRef": "baltic_executive_country_kpis.Loyalty Basket (€)"},
                    {"queryRef": "baltic_executive_country_kpis.Guest Basket (€)"}
                ]
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "b", "Entity": "baltic_executive_country_kpis", "Type": 0}],
                "Select": [
                    {"Measure": {"Expression": {"SourceRef": {"Source": "b"}}, "Property": "Total Baltic Net Sales (€)"}, "Name": "baltic_executive_country_kpis.Total Baltic Net Sales (€)", "NativeReferenceName": "Total Net Sales (€)"},
                    {"Measure": {"Expression": {"SourceRef": {"Source": "b"}}, "Property": "Total Validated POS Baskets"}, "Name": "baltic_executive_country_kpis.Total Validated POS Baskets", "NativeReferenceName": "Validated Baskets"},
                    {"Measure": {"Expression": {"SourceRef": {"Source": "b"}}, "Property": "Loyalty Scan Share (%)"}, "Name": "baltic_executive_country_kpis.Loyalty Scan Share (%)", "NativeReferenceName": "Loyalty Scan %"},
                    {"Measure": {"Expression": {"SourceRef": {"Source": "b"}}, "Property": "Loyalty Basket (€)"}, "Name": "baltic_executive_country_kpis.Loyalty Basket (€)", "NativeReferenceName": "Avg Loyalty Basket"},
                    {"Measure": {"Expression": {"SourceRef": {"Source": "b"}}, "Property": "Guest Basket (€)"}, "Name": "baltic_executive_country_kpis.Guest Basket (€)", "NativeReferenceName": "Avg Guest Basket"}
                ]
            },
            "drillFilterOtherVisuals": True,
            "vcObjects": {
                "background": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}}, "transparency": {"expr": {"Literal": {"Value": "0D"}}}}}],
                "border": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#0050AA'"}}}}}, "width": {"expr": {"Literal": {"Value": "3D"}}}}}]
            }
        }
    })
}

# 3. Top-Right Interactive Baltic Country Filter Slicer
v_slicer = {
    "x": 982, "y": 60, "z": 1500, "width": 286, "height": 115,
    "config": json.dumps({
        "name": "slicerCountry01",
        "layouts": [{"id": 0, "position": {"x": 982, "y": 60, "z": 1500, "width": 286, "height": 115, "tabOrder": 1500}}],
        "singleVisual": {
            "visualType": "slicer",
            "projections": {"Values": [{"queryRef": "baltic_executive_country_kpis.Country", "active": True}]},
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "b", "Entity": "baltic_executive_country_kpis", "Type": 0}],
                "Select": [{"Column": {"Expression": {"SourceRef": {"Source": "b"}}, "Property": "Country"}, "Name": "baltic_executive_country_kpis.Country", "NativeReferenceName": "Baltic Country"}]
            },
            "drillFilterOtherVisuals": True,
            "objects": {
                "data": [{"properties": {"mode": {"expr": {"Literal": {"Value": "'Basic'"}}}}}],
                "header": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "text": {"expr": {"Literal": {"Value": "'BALTIC MARKET FILTER'"}}}, "bold": {"expr": {"Literal": {"Value": "true"}}}, "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#003876'"}}}}}}}]
            },
            "vcObjects": {
                "background": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}}, "transparency": {"expr": {"Literal": {"Value": "0D"}}}}}],
                "border": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFF000'"}}}}}, "width": {"expr": {"Literal": {"Value": "3D"}}}}}]
            }
        }
    })
}

# 4. Middle-Left: Campaign Pre/Post True Net Incremental ROI (%) with Custom Red/Green/Blue Data Point Colors & Data Labels ON
camp_color_rules = [
    ("Baltic Grill & Fresh Meat -20% Weekend", "#003876"),
    ("Fresh Bananas & Berries -25% App Deal", "#003876"),
    ("Baltic Fresh Bakery -30% App Coupon", "#003876"),
    ("Private Label Dairy & Cheese -20%", "#1E824C"),
    ("Spend €30 Get €3 Off Weekend Basket", "#0050AA"),
    ("Organic & BIO Range -25% Green Week", "#1E824C"),
    ("Digital Scratch Card €1.50 Instant Reward", "#28A197"),
    ("Inactive 21-Day Win-Back €4 Off €25", "#28A197"),
    ("Spend €40 Get €5 Off Family Stock-Up", "#0050AA"),
    ("Imported Coffee Beans XXL -35% Promo", "#D92B2B"),
    ("Household Detergent XXL -40% Coupon", "#D92B2B"),
    ("Cooking Oil 2L 1+1 Free App Coupon", "#D92B2B")
]
dp_camp = []
for cname, hex_c in camp_color_rules:
    dp_camp.append({
        "properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{hex_c}'"}}}}}},
        "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": {"Column": {"Expression": {"SourceRef": {"Entity": "campaign_pre_post_incrementality_roi"}}, "Property": "campaign_name"}}, "Right": {"Literal": {"Value": f"'{cname}'"}}}}}]}
    })

v_camp_roi = {
    "x": 12, "y": 184, "z": 2000, "width": 680, "height": 270,
    "config": json.dumps({
        "name": "v1campRoiStyled",
        "layouts": [{"id": 0, "position": {"x": 12, "y": 184, "z": 2000, "width": 680, "height": 270, "tabOrder": 2000}}],
        "singleVisual": {
            "visualType": "clusteredBarChart",
            "projections": {
                "Category": [{"queryRef": "campaign_pre_post_incrementality_roi.campaign_name", "active": True}],
                "Y": [{"queryRef": "Sum(campaign_pre_post_incrementality_roi.Net_Campaign_ROI_Pct)"}]
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "c", "Entity": "campaign_pre_post_incrementality_roi", "Type": 0}],
                "Select": [
                    {"Column": {"Expression": {"SourceRef": {"Source": "c"}}, "Property": "campaign_name"}, "Name": "campaign_pre_post_incrementality_roi.campaign_name", "NativeReferenceName": "Campaign"},
                    {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "c"}}, "Property": "Net_Campaign_ROI_Pct"}}, "Function": 0}, "Name": "Sum(campaign_pre_post_incrementality_roi.Net_Campaign_ROI_Pct)", "NativeReferenceName": "True Net ROI (%)"}
                ],
                "OrderBy": [{"Direction": 2, "Expression": {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "c"}}, "Property": "Net_Campaign_ROI_Pct"}}, "Function": 0}}}]
            },
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "objects": {
                "categoryAxis": [{"properties": {"showAxisTitle": {"expr": {"Literal": {"Value": "false"}}}}}],
                "valueAxis": [{"properties": {"showAxisTitle": {"expr": {"Literal": {"Value": "false"}}}, "gridlineShow": {"expr": {"Literal": {"Value": "true"}}}}}],
                "labels": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "enableDetailDataLabel": {"expr": {"Literal": {"Value": "false"}}}}}],
                "dataPoint": dp_camp
            },
            "vcObjects": {
                "background": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}}, "transparency": {"expr": {"Literal": {"Value": "0D"}}}}}],
                "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "text": {"expr": {"Literal": {"Value": "'1. Campaign Pre/Post True Net Incremental ROI (%) — Winners vs. Cherry-Picked Losses'"}}}, "bold": {"expr": {"Literal": {"Value": "true"}}}, "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#003876'"}}}}}, "alignment": {"expr": {"Literal": {"Value": "'center'"}}}}}],
                "border": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#003876'"}}}}}, "width": {"expr": {"Literal": {"Value": "3D"}}}}}]
            }
        }
    })
}

# 5. Middle-Right: Clustered Column Chart Comparing Avg Loyalty Basket (€) vs Avg Guest Basket (€) by Country
v_baltic_col = {
    "x": 702, "y": 184, "z": 2500, "width": 566, "height": 270,
    "config": json.dumps({
        "name": "v2balticColComparison",
        "layouts": [{"id": 0, "position": {"x": 702, "y": 184, "z": 2500, "width": 566, "height": 270, "tabOrder": 2500}}],
        "singleVisual": {
            "visualType": "clusteredColumnChart",
            "projections": {
                "Category": [{"queryRef": "baltic_executive_country_kpis.Country", "active": True}],
                "Y": [
                    {"queryRef": "Sum(baltic_executive_country_kpis.Avg_Basket_Loyalty_EUR)"},
                    {"queryRef": "Sum(baltic_executive_country_kpis.Avg_Basket_Guest_EUR)"}
                ]
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "b", "Entity": "baltic_executive_country_kpis", "Type": 0}],
                "Select": [
                    {"Column": {"Expression": {"SourceRef": {"Source": "b"}}, "Property": "Country"}, "Name": "baltic_executive_country_kpis.Country", "NativeReferenceName": "Country"},
                    {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "b"}}, "Property": "Avg_Basket_Loyalty_EUR"}}, "Function": 0}, "Name": "Sum(baltic_executive_country_kpis.Avg_Basket_Loyalty_EUR)", "NativeReferenceName": "Loyalty App Basket (€)"},
                    {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "b"}}, "Property": "Avg_Basket_Guest_EUR"}}, "Function": 0}, "Name": "Sum(baltic_executive_country_kpis.Avg_Basket_Guest_EUR)", "NativeReferenceName": "Non-Loyalty Guest Basket (€)"}
                ],
                "OrderBy": [{"Direction": 2, "Expression": {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "b"}}, "Property": "Avg_Basket_Loyalty_EUR"}}, "Function": 0}}}]
            },
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "objects": {
                "categoryAxis": [{"properties": {"showAxisTitle": {"expr": {"Literal": {"Value": "false"}}}}}],
                "valueAxis": [{"properties": {"showAxisTitle": {"expr": {"Literal": {"Value": "false"}}}}}],
                "labels": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
                "dataPoint": [
                    {"properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#003876'"}}}}}}, "selector": {"metadata": "Sum(baltic_executive_country_kpis.Avg_Basket_Loyalty_EUR)"}},
                    {"properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#F39C12'"}}}}}}, "selector": {"metadata": "Sum(baltic_executive_country_kpis.Avg_Basket_Guest_EUR)"}}
                ]
            },
            "vcObjects": {
                "background": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}}, "transparency": {"expr": {"Literal": {"Value": "0D"}}}}}],
                "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "text": {"expr": {"Literal": {"Value": "'2. Baltic Basket Uplift: Loyalty App (€29.3) vs. Guest (€16.4)'"}}}, "bold": {"expr": {"Literal": {"Value": "true"}}}, "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#003876'"}}}}}, "alignment": {"expr": {"Literal": {"Value": "'center'"}}}}}],
                "border": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#003876'"}}}}}, "width": {"expr": {"Literal": {"Value": "3D"}}}}}]
            }
        }
    })
}

# 6. Bottom-Left: Donut Chart of Revenue Share by Customer RFM Segment (€)
rfm_colors = [
    ("Core Weekly Loyal", "#003876"),
    ("VIP Full-Basket Family", "#1E824C"),
    ("Promo-Driven Cherry Picker", "#D92B2B"),
    ("At-Risk / Slipping", "#F39C12"),
    ("Single-Category Shopper", "#5F9EA0")
]
dp_rfm = []
for sname, hex_c in rfm_colors:
    dp_rfm.append({
        "properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{hex_c}'"}}}}}},
        "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": {"Column": {"Expression": {"SourceRef": {"Entity": "customer_rfm_promo_segmentation"}}, "Property": "customer_archetype"}}, "Right": {"Literal": {"Value": f"'{sname}'"}}}}}]}
    })

v_rfm_donut = {
    "x": 12, "y": 462, "z": 3000, "width": 615, "height": 248,
    "config": json.dumps({
        "name": "v3rfmDonutChart",
        "layouts": [{"id": 0, "position": {"x": 12, "y": 462, "z": 3000, "width": 615, "height": 248, "tabOrder": 3000}}],
        "singleVisual": {
            "visualType": "donutChart",
            "projections": {
                "Category": [{"queryRef": "customer_rfm_promo_segmentation.customer_archetype", "active": True}],
                "Y": [{"queryRef": "Sum(customer_rfm_promo_segmentation.Total_Net_Sales_EUR)"}]
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "r", "Entity": "customer_rfm_promo_segmentation", "Type": 0}],
                "Select": [
                    {"Column": {"Expression": {"SourceRef": {"Source": "r"}}, "Property": "customer_archetype"}, "Name": "customer_rfm_promo_segmentation.customer_archetype", "NativeReferenceName": "RFM Segment"},
                    {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "r"}}, "Property": "Total_Net_Sales_EUR"}}, "Function": 0}, "Name": "Sum(customer_rfm_promo_segmentation.Total_Net_Sales_EUR)", "NativeReferenceName": "Net Sales (€)"}
                ],
                "OrderBy": [{"Direction": 2, "Expression": {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "r"}}, "Property": "Total_Net_Sales_EUR"}}, "Function": 0}}}]
            },
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "objects": {
                "dataPoint": dp_rfm,
                "labels": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
                "legend": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}]
            },
            "vcObjects": {
                "background": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}}, "transparency": {"expr": {"Literal": {"Value": "0D"}}}}}],
                "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "text": {"expr": {"Literal": {"Value": "'3. Loyalty Revenue Share (€) by Customer RFM & Promo Segment'"}}}, "bold": {"expr": {"Literal": {"Value": "true"}}}, "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#003876'"}}}}}, "alignment": {"expr": {"Literal": {"Value": "'center'"}}}}}],
                "border": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#003876'"}}}}}, "width": {"expr": {"Literal": {"Value": "3D"}}}}}]
            }
        }
    })
}

# 7. Bottom-Right: Loyalty App Customer Journey Conversion Funnel (funnel visual)
v_funnel_chart = {
    "x": 638, "y": 462, "z": 4000, "width": 630, "height": 248,
    "config": json.dumps({
        "name": "v4funnelChart",
        "layouts": [{"id": 0, "position": {"x": 638, "y": 462, "z": 4000, "width": 630, "height": 248, "tabOrder": 4000}}],
        "singleVisual": {
            "visualType": "funnel",
            "projections": {
                "Category": [{"queryRef": "loyalty_app_customer_journey_funnel.Funnel_Stage", "active": True}],
                "Y": [{"queryRef": "Sum(loyalty_app_customer_journey_funnel.Users_Count)"}]
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "f", "Entity": "loyalty_app_customer_journey_funnel", "Type": 0}],
                "Select": [
                    {"Column": {"Expression": {"SourceRef": {"Source": "f"}}, "Property": "Funnel_Stage"}, "Name": "loyalty_app_customer_journey_funnel.Funnel_Stage", "NativeReferenceName": "Journey Stage"},
                    {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "f"}}, "Property": "Users_Count"}}, "Function": 0}, "Name": "Sum(loyalty_app_customer_journey_funnel.Users_Count)", "NativeReferenceName": "Active Members"}
                ],
                "OrderBy": [{"Direction": 2, "Expression": {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "f"}}, "Property": "Users_Count"}}, "Function": 0}}}]
            },
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "objects": {
                "labels": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
                "dataPoint": [{"properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#0050AA'"}}}}}}}]
            },
            "vcObjects": {
                "background": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}}, "transparency": {"expr": {"Literal": {"Value": "0D"}}}}}],
                "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "text": {"expr": {"Literal": {"Value": "'4. Loyalty App Customer Journey Funnel (50,000 Registered Members)'"}}}, "bold": {"expr": {"Literal": {"Value": "true"}}}, "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#003876'"}}}}}, "alignment": {"expr": {"Literal": {"Value": "'center'"}}}}}],
                "border": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#003876'"}}}}}, "width": {"expr": {"Literal": {"Value": "3D"}}}}}]
            }
        }
    })
}

section_config = {
    "objects": {
        "background": [{"properties": {"color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#0B2239'"}}}}}, "transparency": {"expr": {"Literal": {"Value": "0D"}}}}}],
        "outspace": [{"properties": {"color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#071726'"}}}}}}}]
    }
}

report_json = {
    "id": 0,
    "resourcePackages": [
        {
            "resourcePackage": {
                "name": "SharedResources",
                "type": 2,
                "items": [{"type": 202, "path": "BaseThemes/CY25SU11.json", "name": "CY25SU11"}],
                "disabled": False
            }
        }
    ],
    "sections": [
        {
            "id": 0,
            "name": "ReportSection1",
            "displayName": "Baltic Loyalty Executive Dashboard",
            "filters": "[]",
            "ordinal": 0,
            "visualContainers": [v_header, v_kpis, v_slicer, v_camp_roi, v_baltic_col, v_rfm_donut, v_funnel_chart],
            "config": json.dumps(section_config),
            "displayOption": 1,
            "width": 1280,
            "height": 720
        }
    ],
    "config": "{\"version\":\"5.68\",\"themeCollection\":{\"baseTheme\":{\"name\":\"CY25SU11\",\"type\":2,\"version\":{\"visual\":\"2.4.0\",\"report\":\"3.0.0\",\"page\":\"2.3.0\"}}},\"activeSectionIndex\":0,\"defaultDrillFilterOtherVisuals\":true,\"linguisticSchemaSyncVersion\":2,\"settings\":{\"useNewFilterPaneExperience\":true,\"allowChangeFilterTypes\":true,\"useStylableVisualContainerHeader\":true,\"queryLimitOption\":6,\"exportDataMode\":1,\"useDefaultAggregateDisplayName\":true,\"useEnhancedTooltips\":true}}",
    "layoutOptimization": 0
}

with open(os.path.join(RPT_DIR, "report.json"), "w", encoding="utf-8") as f:
    json.dump(report_json, f, indent=2)

print("Executive Lidl-Branded Dark-Navy Power BI Dashboard layout (report.json) built successfully!")
