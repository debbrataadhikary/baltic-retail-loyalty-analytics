// =====================================================================================
// POWER QUERY (M) STAR SCHEMA CONNECTOR & POS CLEANING PIPELINE
// Instructions: In Power BI Desktop -> Get Data -> Blank Query -> Advanced Editor
// =====================================================================================
let
    SourceFolder = "d:/DW- Internship/Lidl-Loyalty-Data-Analyst/baltic-retail-loyalty-analytics/data/processed/",

    // 1. Load Raw POS Transactions & Execute Silver-to-Gold Data Cleaning
    RawPOS = Csv.Document(
        File.Contents("d:/DW- Internship/Lidl-Loyalty-Data-Analyst/baltic-retail-loyalty-analytics/data/raw/sample_50k_raw_pos_transactions.csv"),
        [Delimiter=",", Columns=18, Encoding=65001, QuoteStyle=QuoteStyle.None]
    ),
    PromotedHeaders = Table.PromoteHeaders(RawPOS, [PromoteAllScalars=true]),
    TypedPOS = Table.TransformColumnTypes(PromotedHeaders, {
        {"transaction_id", type text},
        {"transaction_date", type date},
        {"fiscal_week", Int64.Type},
        {"country_code", type text},
        {"store_id", type text},
        {"is_loyalty_scan", Int64.Type},
        {"customer_id", type text},
        {"customer_archetype", type text},
        {"coupon_applied", Int64.Type},
        {"campaign_id", type text},
        {"items_count", Int64.Type},
        {"promo_item_spend_eur", type number},
        {"non_promo_halo_spend_eur", type number},
        {"gross_basket_eur", type number},
        {"discount_amount_eur", type number},
        {"net_sales_eur", type number},
        {"net_margin_eur", type number},
        {"record_status", type text}
    }),

    // Step A: Remove Duplicate Cashier / App Scans
    DeduplicatedPOS = Table.Distinct(TypedPOS, {"transaction_id"}),

    // Step B: Filter out Negative Refund Rows & Unredeemed Coupon Glitches
    CleanValidSales = Table.SelectRows(DeduplicatedPOS, each ([record_status] = "VALID_POS_SALE") and ([net_sales_eur] > 0)),

    // Step C: Impute any Missing Store IDs
    ImputedStoreIDs = Table.ReplaceValue(CleanValidSales, null, "LT-1001", Replacer.ReplaceValue, {"store_id"})
in
    ImputedStoreIDs
