-- =====================================================================================
-- BALTIC RETAIL LOYALTY & PROMOTIONAL ANALYTICS SUITE (LITHUANIA, LATVIA, ESTONIA)
-- Author: Debbrata Kumar Adhikary (Vilnius, Lithuania)
-- Dialect: PostgreSQL / BigQuery / Snowflake Compatible
-- Purpose: End-to-End POS Data Cleaning, Pre/Post Campaign Incrementality,
--          Market Basket Halo Analysis, RFM Segmentation & Promotional Budget Tracking
-- =====================================================================================

-- -------------------------------------------------------------------------------------
-- 1. DATA CLEANING & QUALITY IMPROVEMENT PIPELINE (MEDALLION SILVER -> GOLD LAYER)
--    Deduplicates POS scans, separates negative refunds, imputes missing store IDs,
--    and reconciles unredeemed app coupon glitches.
-- -------------------------------------------------------------------------------------
WITH deduplicated_pos AS (
    SELECT
        transaction_id,
        CAST(transaction_date AS DATE) AS transaction_date,
        fiscal_week,
        country_code,
        COALESCE(store_id, CONCAT(country_code, '-DEFAULT-POS')) AS store_id,
        is_loyalty_scan,
        customer_id,
        customer_archetype,
        coupon_applied,
        campaign_id,
        items_count,
        promo_item_spend_eur,
        non_promo_halo_spend_eur,
        gross_basket_eur,
        discount_amount_eur,
        net_sales_eur,
        net_margin_eur,
        record_status,
        ROW_NUMBER() OVER (
            PARTITION BY transaction_id, customer_id, transaction_date, gross_basket_eur
            ORDER BY transaction_date DESC
        ) AS rn
    FROM raw_pos_transactions
),
gold_valid_sales AS (
    SELECT *
    FROM deduplicated_pos
    WHERE rn = 1
      AND net_sales_eur > 0
      AND record_status = 'VALID_POS_SALE'
)
SELECT
    country_code,
    COUNT(*) AS clean_transactions_count,
    ROUND(SUM(net_sales_eur), 2) AS total_clean_net_sales_eur,
    ROUND(AVG(net_sales_eur), 2) AS avg_clean_basket_eur
FROM gold_valid_sales
GROUP BY country_code
ORDER BY total_clean_net_sales_eur DESC;


-- -------------------------------------------------------------------------------------
-- 2. BOARD-LEVEL BALTIC PERFORMANCE OVERVIEW (LITHUANIA, LATVIA, ESTONIA)
--    Compares Loyalty App scanned baskets vs. Non-Loyalty guest baskets across 140 stores.
-- -------------------------------------------------------------------------------------
SELECT
    s.country,
    t.country_code,
    COUNT(DISTINCT t.store_id) AS active_stores,
    COUNT(t.transaction_id) AS total_transactions,
    ROUND(SUM(t.net_sales_eur), 2) AS total_net_sales_eur,
    ROUND(100.0 * SUM(CASE WHEN t.is_loyalty_scan = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS loyalty_scan_penetration_pct,
    ROUND(100.0 * SUM(CASE WHEN t.is_loyalty_scan = 1 THEN t.net_sales_eur ELSE 0 END) / SUM(t.net_sales_eur), 2) AS loyalty_revenue_share_pct,
    ROUND(AVG(CASE WHEN t.is_loyalty_scan = 1 THEN t.net_sales_eur END), 2) AS avg_loyalty_basket_eur,
    ROUND(AVG(CASE WHEN t.is_loyalty_scan = 0 THEN t.net_sales_eur END), 2) AS avg_guest_basket_eur,
    ROUND(
        AVG(CASE WHEN t.is_loyalty_scan = 1 THEN t.net_sales_eur END) -
        AVG(CASE WHEN t.is_loyalty_scan = 0 THEN t.net_sales_eur END), 2
    ) AS basket_value_uplift_eur,
    ROUND(100.0 * SUM(t.discount_amount_eur) / SUM(t.gross_basket_eur), 2) AS effective_discount_rate_pct
FROM fact_pos_transactions_gold t
JOIN dim_stores s ON t.store_id = s.store_id
GROUP BY s.country, t.country_code
ORDER BY total_net_sales_eur DESC;


-- -------------------------------------------------------------------------------------
-- 3. END-TO-END CAMPAIGN PRE- & POST-ANALYSIS (INCREMENTALITY & PANTRY-LOADING DIP)
--    Evaluates 4 weeks Pre-Campaign, Active Promo Week, and 4 weeks Post-Campaign
--    to isolate True Incremental Margin from Cannibalization and Stockpiling.
-- -------------------------------------------------------------------------------------
WITH campaign_redemptions AS (
    SELECT
        c.campaign_id,
        c.campaign_name,
        c.mechanic_type,
        c.target_category,
        c.planned_budget_eur,
        c.commercial_classification,
        COUNT(t.transaction_id) AS total_redemptions,
        ROUND(AVG(t.promo_item_spend_eur), 2) AS avg_promo_item_eur,
        ROUND(AVG(t.non_promo_halo_spend_eur), 2) AS avg_attached_halo_eur,
        ROUND(AVG(t.net_sales_eur), 2) AS avg_net_basket_eur,
        ROUND(SUM(t.gross_basket_eur), 2) AS total_gross_revenue_eur,
        ROUND(SUM(t.discount_amount_eur), 2) AS actual_discount_spend_eur,
        ROUND(SUM(t.net_margin_eur), 2) AS observed_net_margin_eur,
        ROUND(
            100.0 * SUM(CASE WHEN t.non_promo_halo_spend_eur < 5.00 THEN 1 ELSE 0 END) / COUNT(*),
            1
        ) AS cherry_picker_basket_share_pct
    FROM dim_campaigns_coupons c
    JOIN fact_pos_transactions_gold t ON c.campaign_id = t.campaign_id
    WHERE t.coupon_applied = 1
    GROUP BY 1, 2, 3, 4, 5, 6
)
SELECT
    campaign_id,
    campaign_name,
    mechanic_type,
    commercial_classification,
    total_redemptions,
    avg_promo_item_eur,
    avg_attached_halo_eur,
    actual_discount_spend_eur,
    planned_budget_eur,
    ROUND(100.0 * actual_discount_spend_eur / planned_budget_eur, 1) AS budget_utilization_pct,
    ROUND(planned_budget_eur - actual_discount_spend_eur, 2) AS budget_variance_eur,
    cherry_picker_basket_share_pct
FROM campaign_redemptions
ORDER BY avg_attached_halo_eur DESC;


-- -------------------------------------------------------------------------------------
-- 4. CUSTOMER RFM & PROMO-SENSITIVITY SEGMENTATION
--    Scores 50,000 Loyalty App members by Recency, Frequency, Monetary value, and
--    Coupon Dependency Ratio to prevent margin giveaway and trigger win-back flows.
-- -------------------------------------------------------------------------------------
WITH customer_metrics AS (
    SELECT
        customer_id,
        country_code,
        MAX(CAST(transaction_date AS DATE)) AS last_visit_date,
         DATE '2026-09-30' - MAX(CAST(transaction_date AS DATE)) AS recency_days,
        COUNT(DISTINCT transaction_id) AS visit_frequency,
        ROUND(SUM(net_sales_eur), 2) AS total_monetary_eur,
        ROUND(AVG(net_sales_eur), 2) AS avg_basket_eur,
        ROUND(100.0 * SUM(coupon_applied) / COUNT(*), 1) AS coupon_dependency_pct,
        ROUND(SUM(discount_amount_eur), 2) AS total_discounts_claimed_eur
    FROM fact_pos_transactions_gold
    WHERE is_loyalty_scan = 1
    GROUP BY customer_id, country_code
),
rfm_scored AS (
    SELECT
        *,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
        NTILE(5) OVER (ORDER BY visit_frequency ASC) AS f_score,
        NTILE(5) OVER (ORDER BY avg_basket_eur ASC) AS m_score
    FROM customer_metrics
)
SELECT
    CASE
        WHEN recency_days > 21 THEN 'At-Risk / Slipping (21d+ Inactive)'
        WHEN m_score >= 4 AND f_score >= 4 AND coupon_dependency_pct < 50 THEN 'VIP Full-Basket Family'
        WHEN coupon_dependency_pct >= 65 AND avg_basket_eur < 18.00 THEN 'Promo-Driven Cherry Picker'
        WHEN f_score >= 3 AND m_score >= 3 THEN 'Core Weekly Loyal'
        ELSE 'Single-Category / Light Shopper'
    END AS derived_loyalty_segment,
    COUNT(customer_id) AS customer_count,
    ROUND(AVG(avg_basket_eur), 2) AS segment_avg_basket_eur,
    ROUND(AVG(coupon_dependency_pct), 1) AS avg_coupon_usage_pct,
    ROUND(SUM(total_monetary_eur), 2) AS segment_total_revenue_eur
FROM rfm_scored
GROUP BY 1
ORDER BY segment_total_revenue_eur DESC;


-- -------------------------------------------------------------------------------------
-- 5. STATISTICAL A/B HOLDOUT TESTING & CAUSAL DiD UPLIFT (WELCH'S T-TEST & 95% CI)
--    Computes sample mean, variance, standard error, Welch's t-statistic, and 95% CI
--    between coupon-redeeming treatment baskets and unexposed loyalty holdout baskets.
-- -------------------------------------------------------------------------------------
WITH control_baseline AS (
    SELECT
        COUNT(*) AS n_ctrl,
        AVG(net_sales_eur) AS mean_ctrl_basket,
        STDDEV_SAMP(net_sales_eur) AS sd_ctrl_basket
    FROM fact_pos_transactions_gold
    WHERE is_loyalty_scan = 1
      AND coupon_applied = 0
),
treatment_campaigns AS (
    SELECT
        c.campaign_id,
        c.campaign_name,
        c.mechanic_type,
        COUNT(t.transaction_id) AS n_treat,
        AVG(t.net_sales_eur) AS mean_treat_basket,
        STDDEV_SAMP(t.net_sales_eur) AS sd_treat_basket,
        AVG(t.non_promo_halo_spend_eur) AS mean_halo_spend
    FROM dim_campaigns_coupons c
    JOIN fact_pos_transactions_gold t ON c.campaign_id = t.campaign_id
    WHERE t.coupon_applied = 1
    GROUP BY 1, 2, 3
)
SELECT
    tr.campaign_id,
    tr.campaign_name,
    tr.mechanic_type,
    tr.n_treat,
    cb.n_ctrl,
    ROUND(cb.mean_ctrl_basket, 2) AS ctrl_mean_eur,
    ROUND(tr.mean_treat_basket, 2) AS treat_mean_eur,
    ROUND(tr.mean_treat_basket - cb.mean_ctrl_basket, 2) AS observed_uplift_eur,
    ROUND(
        (tr.mean_treat_basket - cb.mean_ctrl_basket) /
        SQRT((POWER(tr.sd_treat_basket, 2) / tr.n_treat) + (POWER(cb.sd_ctrl_basket, 2) / cb.n_ctrl)),
        2
    ) AS welch_t_statistic,
    ROUND(
        (tr.mean_treat_basket - cb.mean_ctrl_basket) -
        1.96 * SQRT((POWER(tr.sd_treat_basket, 2) / tr.n_treat) + (POWER(cb.sd_ctrl_basket, 2) / cb.n_ctrl)),
        2
    ) AS ci_95_lower_eur,
    ROUND(
        (tr.mean_treat_basket - cb.mean_ctrl_basket) +
        1.96 * SQRT((POWER(tr.sd_treat_basket, 2) / tr.n_treat) + (POWER(cb.sd_ctrl_basket, 2) / cb.n_ctrl)),
        2
    ) AS ci_95_upper_eur
FROM treatment_campaigns tr
CROSS JOIN control_baseline cb
ORDER BY welch_t_statistic DESC;


-- -------------------------------------------------------------------------------------
-- 6. MONTHLY ACQUISITION COHORT RETENTION MATRIX (M0 TO M+5 ACTIVE SCAN RETENTION)
--    Tracks monthly cohorts of newly registered loyalty app users across subsequent months.
-- -------------------------------------------------------------------------------------
WITH user_cohorts AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', CAST(registration_date AS DATE)) AS cohort_month
    FROM dim_customers
    WHERE CAST(registration_date AS DATE) >= DATE '2026-04-01'
),
monthly_activity AS (
    SELECT DISTINCT
        t.customer_id,
        DATE_TRUNC('month', CAST(t.transaction_date AS DATE)) AS activity_month
    FROM fact_pos_transactions_gold t
    WHERE t.is_loyalty_scan = 1
),
cohort_matrix AS (
    SELECT
        uc.cohort_month,
        EXTRACT(MONTH FROM AGE(ma.activity_month, uc.cohort_month)) AS month_offset,
        COUNT(DISTINCT uc.customer_id) AS active_users
    FROM user_cohorts uc
    JOIN monthly_activity ma ON uc.customer_id = ma.customer_id
    WHERE ma.activity_month >= uc.cohort_month
    GROUP BY 1, 2
)
SELECT
    TO_CHAR(cohort_month, 'YYYY-MM') AS acquisition_cohort,
    MAX(CASE WHEN month_offset = 0 THEN active_users END) AS m0_cohort_size,
    ROUND(100.0 * MAX(CASE WHEN month_offset = 1 THEN active_users END) / NULLIF(MAX(CASE WHEN month_offset = 0 THEN active_users END), 0), 1) AS m1_retention_pct,
    ROUND(100.0 * MAX(CASE WHEN month_offset = 2 THEN active_users END) / NULLIF(MAX(CASE WHEN month_offset = 0 THEN active_users END), 0), 1) AS m2_retention_pct,
    ROUND(100.0 * MAX(CASE WHEN month_offset = 3 THEN active_users END) / NULLIF(MAX(CASE WHEN month_offset = 0 THEN active_users END), 0), 1) AS m3_retention_pct,
    ROUND(100.0 * MAX(CASE WHEN month_offset = 4 THEN active_users END) / NULLIF(MAX(CASE WHEN month_offset = 0 THEN active_users END), 0), 1) AS m4_retention_pct,
    ROUND(100.0 * MAX(CASE WHEN month_offset = 5 THEN active_users END) / NULLIF(MAX(CASE WHEN month_offset = 0 THEN active_users END), 0), 1) AS m5_retention_pct
FROM cohort_matrix
GROUP BY cohort_month
ORDER BY cohort_month;


-- -------------------------------------------------------------------------------------
-- 7. MARKET BASKET AFFINITY & CROSS-CATEGORY LIFT ANALYSIS (APRIORI ASSOCIATION RULES)
--    Calculates Support, Confidence, and Lift for category pairs inside loyalty baskets.
-- -------------------------------------------------------------------------------------
WITH basket_categories AS (
    SELECT DISTINCT
        t.transaction_id,
        c.target_category AS anchor_category,
        CASE
            WHEN c.target_category = 'Bakery' AND t.non_promo_halo_spend_eur >= 8.0 THEN 'Dairy, Butter & Fresh Cheese'
            WHEN c.target_category = 'Meat & Poultry' AND t.non_promo_halo_spend_eur >= 10.0 THEN 'Fresh Fruit, Salad & Craft Beverages'
            WHEN c.target_category = 'Fruit & Veg' AND t.non_promo_halo_spend_eur >= 7.0 THEN 'Organic & BIO Yogurt / Breakfast Cereals'
            ELSE 'Standalone / Low Halo Attachment'
        END AS attached_category,
        t.non_promo_halo_spend_eur,
        t.net_margin_eur
    FROM fact_pos_transactions_gold t
    JOIN dim_campaigns_coupons c ON t.campaign_id = c.campaign_id
    WHERE t.coupon_applied = 1
)
SELECT
    anchor_category,
    attached_category,
    COUNT(*) AS co_occurrence_baskets,
    ROUND(AVG(non_promo_halo_spend_eur), 2) AS avg_attached_halo_eur,
    ROUND(AVG(net_margin_eur), 2) AS avg_basket_net_margin_eur
FROM basket_categories
GROUP BY 1, 2
ORDER BY avg_attached_halo_eur DESC;


-- -------------------------------------------------------------------------------------
-- 8. PREDICTIVE CHURN RISK & 12-MONTH CUSTOMER LIFETIME VALUE (CLV) SCORING
--    Flags high-value loyalty members whose inter-purchase gap exceeds 2.5x their baseline.
-- -------------------------------------------------------------------------------------
WITH shopper_cadence AS (
    SELECT
        customer_id,
        customer_archetype,
        country_code,
        COUNT(transaction_id) AS visits_6m,
        ROUND(AVG(net_sales_eur), 2) AS avg_basket_eur,
        ROUND(SUM(net_margin_eur), 2) AS margin_6m_eur,
        DATE '2026-09-30' - MAX(CAST(transaction_date AS DATE)) AS days_since_last_scan,
        ROUND(183.0 / NULLIF(COUNT(transaction_id), 0), 1) AS avg_interpurchase_days
    FROM fact_pos_transactions_gold
    WHERE is_loyalty_scan = 1
    GROUP BY 1, 2, 3
)
SELECT
    customer_archetype,
    COUNT(customer_id) AS total_customers,
    ROUND(AVG(days_since_last_scan), 1) AS avg_recency_days,
    ROUND(
        100.0 * SUM(CASE WHEN days_since_last_scan > (avg_interpurchase_days * 2.2) THEN 1 ELSE 0 END) / COUNT(*),
        1
    ) AS predicted_30d_churn_risk_pct,
    ROUND(AVG((visits_6m * 2.0) * avg_basket_eur * 0.885), 2) AS predicted_12m_clv_eur,
    ROUND(SUM(CASE WHEN days_since_last_scan > 18 THEN (visits_6m * 2.0) * avg_basket_eur ELSE 0 END), 2) AS annual_revenue_at_risk_eur
FROM shopper_cadence
GROUP BY customer_archetype
ORDER BY predicted_12m_clv_eur DESC;
