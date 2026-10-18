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

# Copy CY25SU11.json from existing working PBIX on D: drive
ref_pbix = r"D:\Google Data Analytics\SQL-Ecommoerce Project\E-Commerce_Churn_&_RFM_Dashboard.pbix"
if os.path.exists(ref_pbix):
    with zipfile.ZipFile(ref_pbix, "r") as z:
        theme_bytes = z.read("Report/StaticResources/SharedResources/BaseThemes/CY25SU11.json")
        with open(os.path.join(STATIC_THEME_DIR, "CY25SU11.json"), "wb") as tf:
            tf.write(theme_bytes)

print("1. Creating Star Schema Gold CSVs & SQLite Data Warehouse...")
df_stores = pd.read_csv(os.path.join(BASE_DIR, "data/processed/dim_stores.csv"))
df_customers = pd.read_csv(os.path.join(BASE_DIR, "data/processed/dim_customers.csv"))
df_campaigns = pd.read_csv(os.path.join(BASE_DIR, "data/processed/dim_campaigns_coupons.csv"))
df_raw_sample = pd.read_csv(os.path.join(BASE_DIR, "data/raw/sample_50k_raw_pos_transactions.csv"))

df_gold_fact = df_raw_sample[df_raw_sample["record_status"] == "VALID_POS_SALE"].copy()
gold_fact_path = os.path.join(BASE_DIR, "data/processed/fact_pos_transactions_gold.csv")
df_gold_fact.to_csv(gold_fact_path, index=False)

dates = pd.date_range("2026-04-01", "2026-09-30", freq="D")
df_calendar = pd.DataFrame({
    "date_key": dates.strftime("%Y-%m-%d"),
    "year": dates.year,
    "month_num": dates.month,
    "month_name": dates.strftime("%B"),
    "month_short": dates.strftime("%b %Y"),
    "fiscal_week": np.clip(((dates - pd.to_datetime("2026-04-01")).days // 7 + 1), 1, 26),
    "day_of_week": dates.strftime("%A"),
    "is_weekend": dates.weekday.isin([5, 6]).astype(int)
})
cal_path = os.path.join(BASE_DIR, "data/processed/dim_calendar.csv")
df_calendar.to_csv(cal_path, index=False)

db_path = os.path.join(BASE_DIR, "data/processed/baltic_loyalty_warehouse.db")
conn = sqlite3.connect(db_path)
df_stores.to_sql("dim_stores", conn, if_exists="replace", index=False)
df_customers.to_sql("dim_customers", conn, if_exists="replace", index=False)
df_campaigns.to_sql("dim_campaigns_coupons", conn, if_exists="replace", index=False)
df_calendar.to_sql("dim_calendar", conn, if_exists="replace", index=False)
df_gold_fact.to_sql("fact_pos_transactions_gold", conn, if_exists="replace", index=False)
conn.close()

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

# Build valid report.json with pre-configured visuals on Page 1
def make_bar_visual(name, x, y, w, h, z, entity, cat_col, val_col, title_text):
    cfg = {
        "name": name,
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": z}}],
        "singleVisual": {
            "visualType": "barChart",
            "projections": {
                "Category": [{"queryRef": f"{entity}.{cat_col}", "active": True}],
                "Y": [{"queryRef": f"Sum({entity}.{val_col})"}]
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "t", "Entity": entity, "Type": 0}],
                "Select": [
                    {"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": cat_col}, "Name": f"{entity}.{cat_col}", "NativeReferenceName": cat_col},
                    {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": val_col}}, "Function": 0}, "Name": f"Sum({entity}.{val_col})", "NativeReferenceName": val_col}
                ],
                "OrderBy": [{"Direction": 2, "Expression": {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": val_col}}, "Function": 0}}}]
            },
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "vcObjects": {
                "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "text": {"expr": {"Literal": {"Value": f"'{title_text}'"}}} }}]
            }
        }
    }
    return {"x": x, "y": y, "z": z, "width": w, "height": h, "config": json.dumps(cfg)}

v1 = make_bar_visual("v1campRoi", 16, 20, 620, 330, 1000, "campaign_pre_post_incrementality_roi", "campaign_name", "Net_Campaign_ROI_Pct", "1. Campaign Pre/Post True Net Incremental ROI (%)")
v2 = make_bar_visual("v2balticSales", 650, 20, 610, 330, 2000, "baltic_executive_country_kpis", "Country", "Avg_Basket_Loyalty_EUR", "2. Baltic Average Loyalty Basket Value (€) by Country")
v3 = make_bar_visual("v3rfmSeg", 16, 365, 620, 330, 3000, "customer_rfm_promo_segmentation", "customer_archetype", "Avg_Net_Basket_EUR", "3. Customer RFM Archetypes: Average Net Basket (€)")
v4 = make_bar_visual("v4funnel", 650, 365, 610, 330, 4000, "loyalty_app_customer_journey_funnel", "Funnel_Stage", "Users_Count", "4. Loyalty App Customer Journey Funnel (50,000 Members)")

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
            "visualContainers": [v1, v2, v3, v4],
            "config": "{}",
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

print("Updated Power BI Project (.pbip) with full report.json visuals and powerBI_V3 model.bim!")
