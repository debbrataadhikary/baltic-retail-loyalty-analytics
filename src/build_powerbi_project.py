import os
import json
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

print("1. Creating Star Schema Gold CSVs & SQLite Data Warehouse for Power BI Connection...")
# Load dimensions & generate dim_calendar + fact_pos_transactions_gold (100k clean sample for fast Power BI refresh)
df_stores = pd.read_csv(os.path.join(BASE_DIR, "data/processed/dim_stores.csv"))
df_customers = pd.read_csv(os.path.join(BASE_DIR, "data/processed/dim_customers.csv"))
df_campaigns = pd.read_csv(os.path.join(BASE_DIR, "data/processed/dim_campaigns_coupons.csv"))
df_raw_sample = pd.read_csv(os.path.join(BASE_DIR, "data/raw/sample_50k_raw_pos_transactions.csv"))

# Clean Gold sample for direct Power BI Star Schema import
df_gold_fact = df_raw_sample[df_raw_sample["record_status"] == "VALID_POS_SALE"].copy()
gold_fact_path = os.path.join(BASE_DIR, "data/processed/fact_pos_transactions_gold.csv")
df_gold_fact.to_csv(gold_fact_path, index=False)

# Create dim_calendar
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

# Also build SQLite Data Warehouse (baltic_loyalty_warehouse.db) for ODBC/SQLite Power BI connection
db_path = os.path.join(BASE_DIR, "data/processed/baltic_loyalty_warehouse.db")
conn = sqlite3.connect(db_path)
df_stores.to_sql("dim_stores", conn, if_exists="replace", index=False)
df_customers.to_sql("dim_customers", conn, if_exists="replace", index=False)
df_campaigns.to_sql("dim_campaigns_coupons", conn, if_exists="replace", index=False)
df_calendar.to_sql("dim_calendar", conn, if_exists="replace", index=False)
df_gold_fact.to_sql("fact_pos_transactions_gold", conn, if_exists="replace", index=False)
conn.close()
print("   Saved Star Schema CSVs & SQLite DB:", db_path)

# 2. Create Lidl Corporate Power BI Theme JSON
lidl_theme = {
    "name": "Lidl_Baltics_Corporate_Theme",
    "dataColors": ["#003876", "#0050AA", "#FFF000", "#D92B2B", "#1E824C", "#525E6C", "#8FAADC", "#F4B183"],
    "background": "#F4F6F9",
    "foreground": "#1E242B",
    "tableAccent": "#003876",
    "good": "#1E824C",
    "neutral": "#FFF000",
    "bad": "#D92B2B"
}
with open(os.path.join(PBI_DIR, "Lidl_Baltics_Corporate_Theme.json"), "w", encoding="utf-8") as f:
    json.dump(lidl_theme, f, indent=2)

# 3. Create Complete DAX Measures Library (.dax)
dax_content = """-- =====================================================================================
-- BALTICPLUS LOYALTY & PROMOTIONAL ANALYTICS — POWER BI DAX MEASURES LIBRARY
-- Target Model: BalticPlus_Loyalty_Analytics (Star Schema)
-- Author: Debbrata Kumar Adhikary (Vilnius, Lithuania)
-- =====================================================================================

-- -------------------------------------------------------------------------------------
-- 1. CORE POS SALES & BASKET METRICS
-- -------------------------------------------------------------------------------------
Total Net Sales (€) = 
SUM ( fact_pos_transactions_gold[net_sales_eur] )

Total Gross Basket (€) = 
SUM ( fact_pos_transactions_gold[gross_basket_eur] )

Total Promo Discount Spend (€) = 
SUM ( fact_pos_transactions_gold[discount_amount_eur] )

Total Net Margin (€) = 
SUM ( fact_pos_transactions_gold[net_margin_eur] )

Total Validated Baskets = 
DISTINCTCOUNT ( fact_pos_transactions_gold[transaction_id] )

Average Net Basket (€) = 
DIVIDE ( [Total Net Sales (€)], [Total Validated Baskets], 0 )

Average Items per Basket = 
AVERAGE ( fact_pos_transactions_gold[items_count] )


-- -------------------------------------------------------------------------------------
-- 2. LOYALTY APP PENETRATION & BASKET UPLIFT METRICS
-- -------------------------------------------------------------------------------------
Loyalty App Baskets = 
CALCULATE (
    [Total Validated Baskets],
    fact_pos_transactions_gold[is_loyalty_scan] = 1
)

Non-Loyalty Guest Baskets = 
CALCULATE (
    [Total Validated Baskets],
    fact_pos_transactions_gold[is_loyalty_scan] = 0
)

Loyalty Scan Penetration (%) = 
DIVIDE ( [Loyalty App Baskets], [Total Validated Baskets], 0 )

Loyalty Revenue Share (%) = 
DIVIDE (
    CALCULATE ( [Total Net Sales (€)], fact_pos_transactions_gold[is_loyalty_scan] = 1 ),
    [Total Net Sales (€)],
    0
)

Avg Loyalty Basket (€) = 
CALCULATE (
    [Average Net Basket (€)],
    fact_pos_transactions_gold[is_loyalty_scan] = 1
)

Avg Guest Basket (€) = 
CALCULATE (
    [Average Net Basket (€)],
    fact_pos_transactions_gold[is_loyalty_scan] = 0
)

Loyalty Basket Uplift (€) = 
[Avg Loyalty Basket (€)] - [Avg Guest Basket (€)]

Loyalty Basket Uplift (%) = 
DIVIDE ( [Loyalty Basket Uplift (€)], [Avg Guest Basket (€)], 0 )


-- -------------------------------------------------------------------------------------
-- 3. CAMPAIGN PRE/POST INCREMENTALITY, CANNIBALIZATION & HALO EFFECT
-- -------------------------------------------------------------------------------------
Coupon Redemptions Count = 
CALCULATE (
    [Total Validated Baskets],
    fact_pos_transactions_gold[coupon_applied] = 1
)

Coupon Redemption Rate (% of Loyalty Scans) = 
DIVIDE ( [Coupon Redemptions Count], [Loyalty App Baskets], 0 )

Avg Promo Item Spend (€) = 
CALCULATE (
    AVERAGE ( fact_pos_transactions_gold[promo_item_spend_eur] ),
    fact_pos_transactions_gold[coupon_applied] = 1
)

Avg Attached Non-Promo Halo Spend (€) = 
CALCULATE (
    AVERAGE ( fact_pos_transactions_gold[non_promo_halo_spend_eur] ),
    fact_pos_transactions_gold[coupon_applied] = 1
)

Basket Halo Multiplier = 
DIVIDE ( [Avg Attached Non-Promo Halo Spend (€)], [Avg Promo Item Spend (€)], 0 )

Cherry-Picker Baskets Count = 
CALCULATE (
    [Total Validated Baskets],
    fact_pos_transactions_gold[coupon_applied] = 1,
    fact_pos_transactions_gold[non_promo_halo_spend_eur] < 5.00
)

Cherry-Picker Share (%) = 
DIVIDE ( [Cherry-Picker Baskets Count], [Coupon Redemptions Count], 0 )

True Incremental Revenue (€) = 
SUM ( campaign_pre_post_incrementality_roi[True_Incremental_Revenue_EUR] )

Net Incremental Margin (€) = 
SUM ( campaign_pre_post_incrementality_roi[Net_Incremental_Margin_EUR] )

True Net Campaign ROI (%) = 
DIVIDE (
    SUM ( campaign_pre_post_incrementality_roi[Net_Incremental_Margin_EUR] ),
    SUM ( campaign_pre_post_incrementality_roi[Total_Discount_Cost_EUR] ),
    0
)


-- -------------------------------------------------------------------------------------
-- 4. STRATEGIC PROMOTIONAL BUDGET PLANNING & EXPENSE TRACKING
-- -------------------------------------------------------------------------------------
Planned Promo Budget (€) = 
SUM ( dim_campaigns_coupons[planned_budget_eur] )

Promo Budget Utilization (%) = 
DIVIDE (
    SUM ( campaign_pre_post_incrementality_roi[Total_Discount_Cost_EUR] ),
    [Planned Promo Budget (€)],
    0
)

Promo Budget Variance (€) = 
[Planned Promo Budget (€)] - SUM ( campaign_pre_post_incrementality_roi[Total_Discount_Cost_EUR] )

Cost per Incremental Visit (€) = 
DIVIDE (
    SUM ( campaign_pre_post_incrementality_roi[Total_Discount_Cost_EUR] ),
    SUM ( campaign_pre_post_incrementality_roi[Redemptions] ) * ( 1 - [Cherry-Picker Share (%)] ),
    0
)
"""
with open(os.path.join(PBI_DIR, "BalticPlus_DAX_Measures.dax"), "w", encoding="utf-8") as f:
    f.write(dax_content)

# 4. Create Power Query M Connector Script (.pq)
pq_content = f"""// =====================================================================================
// POWER QUERY (M) STAR SCHEMA CONNECTOR & POS CLEANING PIPELINE
// Instructions: In Power BI Desktop -> Get Data -> Blank Query -> Advanced Editor
// =====================================================================================
let
    SourceFolder = "{BASE_DIR.replace(chr(92), '/')}/data/processed/",

    // 1. Load Raw POS Transactions & Execute Silver-to-Gold Data Cleaning
    RawPOS = Csv.Document(
        File.Contents("{BASE_DIR.replace(chr(92), '/')}/data/raw/sample_50k_raw_pos_transactions.csv"),
        [Delimiter=",", Columns=18, Encoding=65001, QuoteStyle=QuoteStyle.None]
    ),
    PromotedHeaders = Table.PromoteHeaders(RawPOS, [PromoteAllScalars=true]),
    TypedPOS = Table.TransformColumnTypes(PromotedHeaders, {{
        {{"transaction_id", type text}},
        {{"transaction_date", type date}},
        {{"fiscal_week", Int64.Type}},
        {{"country_code", type text}},
        {{"store_id", type text}},
        {{"is_loyalty_scan", Int64.Type}},
        {{"customer_id", type text}},
        {{"customer_archetype", type text}},
        {{"coupon_applied", Int64.Type}},
        {{"campaign_id", type text}},
        {{"items_count", Int64.Type}},
        {{"promo_item_spend_eur", type number}},
        {{"non_promo_halo_spend_eur", type number}},
        {{"gross_basket_eur", type number}},
        {{"discount_amount_eur", type number}},
        {{"net_sales_eur", type number}},
        {{"net_margin_eur", type number}},
        {{"record_status", type text}}
    }}),

    // Step A: Remove Duplicate Cashier / App Scans
    DeduplicatedPOS = Table.Distinct(TypedPOS, {{"transaction_id"}}),

    // Step B: Filter out Negative Refund Rows & Unredeemed Coupon Glitches
    CleanValidSales = Table.SelectRows(DeduplicatedPOS, each ([record_status] = "VALID_POS_SALE") and ([net_sales_eur] > 0)),

    // Step C: Impute any Missing Store IDs
    ImputedStoreIDs = Table.ReplaceValue(CleanValidSales, null, "LT-1001", Replacer.ReplaceValue, {{"store_id"}})
in
    ImputedStoreIDs
"""
with open(os.path.join(PBI_DIR, "PowerQuery_M_StarSchema_Connector.pq"), "w", encoding="utf-8") as f:
    f.write(pq_content)

# 5. Build Power BI Project (.pbip) + SemanticModel (model.bim) so it opens in Power BI Desktop & Tabular Editor
pbip_json = {
    "version": "1.0",
    "artifacts": [
        {"report": {"path": "BalticPlus_Loyalty_Analytics.Report"}}
    ],
    "settings": {"enableAutoRecovery": True}
}
with open(os.path.join(PBI_DIR, "BalticPlus_Loyalty_Analytics.pbip"), "w", encoding="utf-8") as f:
    json.dump(pbip_json, f, indent=2)

pbism_json = {"version": "1.0", "settings": {}}
with open(os.path.join(SM_DIR, "definition.pbism"), "w", encoding="utf-8") as f:
    json.dump(pbism_json, f, indent=2)

data_dir_escaped = os.path.join(BASE_DIR, "data", "processed").replace("\\", "\\\\")
reports_dir_escaped = os.path.join(BASE_DIR, "reports").replace("\\", "\\\\")

model_bim = {
    "name": "SemanticModel",
    "compatibilityLevel": 1550,
    "model": {
        "culture": "en-US",
        "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True},
        "tables": [
            {
                "name": "dim_stores",
                "columns": [
                    {"name": "store_id", "dataType": "string", "sourceColumn": "store_id"},
                    {"name": "country", "dataType": "string", "sourceColumn": "country"},
                    {"name": "country_code", "dataType": "string", "sourceColumn": "country_code"},
                    {"name": "city", "dataType": "string", "sourceColumn": "city"},
                    {"name": "store_format", "dataType": "string", "sourceColumn": "store_format"},
                    {"name": "opening_year", "dataType": "int64", "sourceColumn": "opening_year"}
                ],
                "partitions": [{
                    "name": "dim_stores",
                    "mode": "import",
                    "source": {
                        "type": "m",
                        "expression": [
                            "let",
                            f"    Source = Csv.Document(File.Contents(\"{data_dir_escaped}\\\\dim_stores.csv\"),[Delimiter=\",\", Columns=6, Encoding=65001, QuoteStyle=QuoteStyle.None]),",
                            "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
                            "    Typed = Table.TransformColumnTypes(Promoted,{{\"opening_year\", Int64.Type}})",
                            "in",
                            "    Typed"
                        ]
                    }
                }]
            },
            {
                "name": "dim_campaigns_coupons",
                "columns": [
                    {"name": "campaign_id", "dataType": "string", "sourceColumn": "campaign_id"},
                    {"name": "campaign_name", "dataType": "string", "sourceColumn": "campaign_name"},
                    {"name": "mechanic_type", "dataType": "string", "sourceColumn": "mechanic_type"},
                    {"name": "target_category", "dataType": "string", "sourceColumn": "target_category"},
                    {"name": "nominal_discount_pct", "dataType": "double", "sourceColumn": "nominal_discount_pct"},
                    {"name": "planned_budget_eur", "dataType": "double", "sourceColumn": "planned_budget_eur"},
                    {"name": "commercial_classification", "dataType": "string", "sourceColumn": "commercial_classification"}
                ],
                "partitions": [{
                    "name": "dim_campaigns_coupons",
                    "mode": "import",
                    "source": {
                        "type": "m",
                        "expression": [
                            "let",
                            f"    Source = Csv.Document(File.Contents(\"{data_dir_escaped}\\\\dim_campaigns_coupons.csv\"),[Delimiter=\",\", Columns=7, Encoding=65001, QuoteStyle=QuoteStyle.None]),",
                            "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
                            "    Typed = Table.TransformColumnTypes(Promoted,{{\"nominal_discount_pct\", type number}, {\"planned_budget_eur\", type number}})",
                            "in",
                            "    Typed"
                        ]
                    }
                }]
            },
            {
                "name": "dim_calendar",
                "columns": [
                    {"name": "date_key", "dataType": "string", "sourceColumn": "date_key"},
                    {"name": "year", "dataType": "int64", "sourceColumn": "year"},
                    {"name": "month_num", "dataType": "int64", "sourceColumn": "month_num"},
                    {"name": "month_name", "dataType": "string", "sourceColumn": "month_name"},
                    {"name": "month_short", "dataType": "string", "sourceColumn": "month_short"},
                    {"name": "fiscal_week", "dataType": "int64", "sourceColumn": "fiscal_week"},
                    {"name": "day_of_week", "dataType": "string", "sourceColumn": "day_of_week"},
                    {"name": "is_weekend", "dataType": "int64", "sourceColumn": "is_weekend"}
                ],
                "partitions": [{
                    "name": "dim_calendar",
                    "mode": "import",
                    "source": {
                        "type": "m",
                        "expression": [
                            "let",
                            f"    Source = Csv.Document(File.Contents(\"{data_dir_escaped}\\\\dim_calendar.csv\"),[Delimiter=\",\", Columns=8, Encoding=65001, QuoteStyle=QuoteStyle.None]),",
                            "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
                            "    Typed = Table.TransformColumnTypes(Promoted,{{\"year\", Int64.Type}, {\"month_num\", Int64.Type}, {\"fiscal_week\", Int64.Type}, {\"is_weekend\", Int64.Type}})",
                            "in",
                            "    Typed"
                        ]
                    }
                }]
            },
            {
                "name": "fact_pos_transactions_gold",
                "columns": [
                    {"name": "transaction_id", "dataType": "string", "sourceColumn": "transaction_id"},
                    {"name": "transaction_date", "dataType": "string", "sourceColumn": "transaction_date"},
                    {"name": "fiscal_week", "dataType": "int64", "sourceColumn": "fiscal_week"},
                    {"name": "country_code", "dataType": "string", "sourceColumn": "country_code"},
                    {"name": "store_id", "dataType": "string", "sourceColumn": "store_id"},
                    {"name": "is_loyalty_scan", "dataType": "int64", "sourceColumn": "is_loyalty_scan"},
                    {"name": "customer_id", "dataType": "string", "sourceColumn": "customer_id"},
                    {"name": "customer_archetype", "dataType": "string", "sourceColumn": "customer_archetype"},
                    {"name": "coupon_applied", "dataType": "int64", "sourceColumn": "coupon_applied"},
                    {"name": "campaign_id", "dataType": "string", "sourceColumn": "campaign_id"},
                    {"name": "items_count", "dataType": "int64", "sourceColumn": "items_count"},
                    {"name": "promo_item_spend_eur", "dataType": "double", "sourceColumn": "promo_item_spend_eur"},
                    {"name": "non_promo_halo_spend_eur", "dataType": "double", "sourceColumn": "non_promo_halo_spend_eur"},
                    {"name": "gross_basket_eur", "dataType": "double", "sourceColumn": "gross_basket_eur"},
                    {"name": "discount_amount_eur", "dataType": "double", "sourceColumn": "discount_amount_eur"},
                    {"name": "net_sales_eur", "dataType": "double", "sourceColumn": "net_sales_eur"},
                    {"name": "net_margin_eur", "dataType": "double", "sourceColumn": "net_margin_eur"},
                    {"name": "record_status", "dataType": "string", "sourceColumn": "record_status"}
                ],
                "measures": [
                    {"name": "Total Net Sales (€)", "expression": "SUM(fact_pos_transactions_gold[net_sales_eur])", "formatString": "€#,0.00"},
                    {"name": "Total Validated Baskets", "expression": "DISTINCTCOUNT(fact_pos_transactions_gold[transaction_id])", "formatString": "#,0"},
                    {"name": "Average Net Basket (€)", "expression": "DIVIDE([Total Net Sales (€)], [Total Validated Baskets], 0)", "formatString": "€#,0.00"},
                    {"name": "Loyalty App Baskets", "expression": "CALCULATE([Total Validated Baskets], fact_pos_transactions_gold[is_loyalty_scan] = 1)", "formatString": "#,0"},
                    {"name": "Loyalty Scan Penetration (%)", "expression": "DIVIDE([Loyalty App Baskets], [Total Validated Baskets], 0)", "formatString": "0.0%"},
                    {"name": "Avg Loyalty Basket (€)", "expression": "CALCULATE([Average Net Basket (€)], fact_pos_transactions_gold[is_loyalty_scan] = 1)", "formatString": "€#,0.00"},
                    {"name": "Avg Guest Basket (€)", "expression": "CALCULATE([Average Net Basket (€)], fact_pos_transactions_gold[is_loyalty_scan] = 0)", "formatString": "€#,0.00"},
                    {"name": "Loyalty Basket Uplift (€)", "expression": "[Avg Loyalty Basket (€)] - [Avg Guest Basket (€)]", "formatString": "+€#,0.00;-€#,0.00;€0.00"},
                    {"name": "Avg Attached Halo Spend (€)", "expression": "CALCULATE(AVERAGE(fact_pos_transactions_gold[non_promo_halo_spend_eur]), fact_pos_transactions_gold[coupon_applied] = 1)", "formatString": "€#,0.00"},
                    {"name": "Total Promo Discount Spend (€)", "expression": "SUM(fact_pos_transactions_gold[discount_amount_eur])", "formatString": "€#,0.00"}
                ],
                "partitions": [{
                    "name": "fact_pos_transactions_gold",
                    "mode": "import",
                    "source": {
                        "type": "m",
                        "expression": [
                            "let",
                            f"    Source = Csv.Document(File.Contents(\"{data_dir_escaped}\\\\fact_pos_transactions_gold.csv\"),[Delimiter=\",\", Columns=18, Encoding=65001, QuoteStyle=QuoteStyle.None]),",
                            "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
                            "    Typed = Table.TransformColumnTypes(Promoted,{{\"fiscal_week\", Int64.Type}, {\"is_loyalty_scan\", Int64.Type}, {\"coupon_applied\", Int64.Type}, {\"items_count\", Int64.Type}, {\"promo_item_spend_eur\", type number}, {\"non_promo_halo_spend_eur\", type number}, {\"gross_basket_eur\", type number}, {\"discount_amount_eur\", type number}, {\"net_sales_eur\", type number}, {\"net_margin_eur\", type number}})",
                            "in",
                            "    Typed"
                        ]
                    }
                }]
            },
            {
                "name": "campaign_pre_post_incrementality_roi",
                "columns": [
                    {"name": "campaign_id", "dataType": "string", "sourceColumn": "campaign_id"},
                    {"name": "campaign_name", "dataType": "string", "sourceColumn": "campaign_name"},
                    {"name": "mechanic_type", "dataType": "string", "sourceColumn": "mechanic_type"},
                    {"name": "commercial_classification", "dataType": "string", "sourceColumn": "commercial_classification"},
                    {"name": "Redemptions", "dataType": "int64", "sourceColumn": "Redemptions"},
                    {"name": "Avg_Halo_Other_Spend_EUR", "dataType": "double", "sourceColumn": "Avg_Halo_Other_Spend_EUR"},
                    {"name": "Total_Discount_Cost_EUR", "dataType": "double", "sourceColumn": "Total_Discount_Cost_EUR"},
                    {"name": "True_Incremental_Revenue_EUR", "dataType": "double", "sourceColumn": "True_Incremental_Revenue_EUR"},
                    {"name": "Net_Incremental_Margin_EUR", "dataType": "double", "sourceColumn": "Net_Incremental_Margin_EUR"},
                    {"name": "Net_Campaign_ROI_Pct", "dataType": "double", "sourceColumn": "Net_Campaign_ROI_Pct"},
                    {"name": "Budget_Utilization_Pct", "dataType": "double", "sourceColumn": "Budget_Utilization_Pct"}
                ],
                "partitions": [{
                    "name": "campaign_pre_post_incrementality_roi",
                    "mode": "import",
                    "source": {
                        "type": "m",
                        "expression": [
                            "let",
                            f"    Source = Csv.Document(File.Contents(\"{reports_dir_escaped}\\\\campaign_pre_post_incrementality_roi.csv\"),[Delimiter=\",\", Columns=24, Encoding=65001, QuoteStyle=QuoteStyle.None]),",
                            "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
                            "    Typed = Table.TransformColumnTypes(Promoted,{{\"Redemptions\", Int64.Type}, {\"Avg_Halo_Other_Spend_EUR\", type number}, {\"Total_Discount_Cost_EUR\", type number}, {\"True_Incremental_Revenue_EUR\", type number}, {\"Net_Incremental_Margin_EUR\", type number}, {\"Net_Campaign_ROI_Pct\", type number}, {\"Budget_Utilization_Pct\", type number}})",
                            "in",
                            "    Typed"
                        ]
                    }
                }]
            }
        ],
        "relationships": [
            {
                "name": "rel_store_pos",
                "fromTable": "fact_pos_transactions_gold",
                "fromColumn": "store_id",
                "toTable": "dim_stores",
                "toColumn": "store_id"
            },
            {
                "name": "rel_campaign_pos",
                "fromTable": "fact_pos_transactions_gold",
                "fromColumn": "campaign_id",
                "toTable": "dim_campaigns_coupons",
                "toColumn": "campaign_id"
            },
            {
                "name": "rel_date_pos",
                "fromTable": "fact_pos_transactions_gold",
                "fromColumn": "transaction_date",
                "toTable": "dim_calendar",
                "toColumn": "date_key"
            }
        ]
    }
}
with open(os.path.join(SM_DIR, "model.bim"), "w", encoding="utf-8") as f:
    json.dump(model_bim, f, indent=2)

pbir_json = {
    "version": "1.0",
    "datasetReference": {
        "byPath": {"path": "../BalticPlus_Loyalty_Analytics.SemanticModel"},
        "byConnection": None
    }
}
with open(os.path.join(RPT_DIR, "definition.pbir"), "w", encoding="utf-8") as f:
    json.dump(pbir_json, f, indent=2)

print("Power BI Project (.pbip), Tabular Semantic Model (model.bim), DAX library, Power Query M connector, and SQLite Warehouse built successfully!")
