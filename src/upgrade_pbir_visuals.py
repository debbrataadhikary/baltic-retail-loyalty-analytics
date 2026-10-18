import os
import json
import shutil

BASE_DIR = r"d:\DW- Internship\Lidl-Loyalty-Data-Analyst\baltic-retail-loyalty-analytics"
PAGES_ROOT = os.path.join(BASE_DIR, "powerbi", "BalticPlus_Loyalty_Analytics.Report", "definition", "pages")

# Remove any leftover legacy model.bim or root report.json that conflicts with PBIR v4.0 / TMDL v4.2
legacy_bim = os.path.join(BASE_DIR, "powerbi", "BalticPlus_Loyalty_Analytics.SemanticModel", "model.bim")
legacy_rpt = os.path.join(BASE_DIR, "powerbi", "BalticPlus_Loyalty_Analytics.Report", "report.json")
for p in [legacy_bim, legacy_rpt]:
    if os.path.exists(p):
        os.remove(p)

# Write pages.json for 3-Page Executive Power BI Application
pages_meta = {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
    "pageOrder": [
        "ReportSection1",
        "ReportSection2",
        "ReportSection3"
    ],
    "activePageName": "ReportSection1"
}
with open(os.path.join(PAGES_ROOT, "pages.json"), "w", encoding="utf-8") as f:
    json.dump(pages_meta, f, indent=2)

def init_page(section_name, display_name):
    pdir = os.path.join(PAGES_ROOT, section_name)
    vdir = os.path.join(pdir, "visuals")
    shutil.rmtree(vdir, ignore_errors=True)
    os.makedirs(vdir, exist_ok=True)
    page_json = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
        "name": section_name,
        "displayName": display_name,
        "displayOption": "FitToPage",
        "height": 720,
        "width": 1280,
        "objects": {
            "background": [{
                "properties": {
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#0B2239'"}}}}},
                    "transparency": {"expr": {"Literal": {"Value": "0D"}}}
                }
            }],
            "outspace": [{
                "properties": {
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#071726'"}}}}}
                }
            }]
        }
    }
    with open(os.path.join(pdir, "page.json"), "w", encoding="utf-8") as f:
        json.dump(page_json, f, indent=2)
    return vdir

def save_visual(vdir, vname, payload):
    vfolder = os.path.join(vdir, vname)
    os.makedirs(vfolder, exist_ok=True)
    with open(os.path.join(vfolder, "visual.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

def agg_field(entity, prop, func=0):
    return {
        "field": {
            "Aggregation": {
                "Expression": {
                    "Column": {
                        "Expression": {"SourceRef": {"Entity": entity}},
                        "Property": prop
                    }
                },
                "Function": func
            }
        },
        "queryRef": f"Sum({entity}.{prop})",
        "nativeQueryRef": prop
    }

def col_field(entity, prop):
    return {
        "field": {
            "Column": {
                "Expression": {"SourceRef": {"Entity": entity}},
                "Property": prop
            }
        },
        "queryRef": f"{entity}.{prop}",
        "nativeQueryRef": prop,
        "active": True
    }

def card_container_style(title_text, border_hex="#0050AA"):
    return {
        "background": [{
            "properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}},
                "transparency": {"expr": {"Literal": {"Value": "0D"}}}
            }
        }],
        "title": [{
            "properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "text": {"expr": {"Literal": {"Value": f"'{title_text}'"}}},
                "bold": {"expr": {"Literal": {"Value": "true"}}},
                "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#003876'"}}}}},
                "alignment": {"expr": {"Literal": {"Value": "'center'"}}}
            }
        }],
        "border": [{
            "properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "color": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{border_hex}'"}}}}},
                "width": {"expr": {"Literal": {"Value": "3D"}}}
            }
        }]
    }

def add_top_banner(vdir, banner_text):
    save_visual(vdir, "v0header", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
        "name": "v0header",
        "position": {"x": 12, "y": 8, "z": 500, "height": 46, "width": 1256, "tabOrder": 500},
        "visual": {
            "visualType": "textbox",
            "objects": {
                "general": [{
                    "properties": {
                        "paragraphs": [{
                            "textRuns": [{
                                "value": banner_text,
                                "textStyle": {"fontWeight": "bold", "fontSize": "14pt", "color": "#FFF000"}
                            }],
                            "horizontalTextAlignment": "center"
                        }]
                    }
                }]
            },
            "visualContainerObjects": {
                "background": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#002B5C'"}}}}},
                        "transparency": {"expr": {"Literal": {"Value": "0D"}}}
                    }
                }],
                "border": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFF000'"}}}}},
                        "width": {"expr": {"Literal": {"Value": "2D"}}}
                    }
                }]
            }
        }
    })

# ==============================================================================
# PAGE 1: BALTIC EXECUTIVE OVERVIEW (LT, LV, EE)
# ==============================================================================
vdir1 = init_page("ReportSection1", "1. Baltic Executive Overview")
add_top_banner(vdir1, "PAGE 1: BALTICPLUS LOYALTY & PROMOTIONAL ANALYTICS — EXECUTIVE BOARD DASHBOARD (LT • LV • EE)")

save_visual(vdir1, "v0kpis", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
    "name": "v0kpis",
    "position": {"x": 12, "y": 60, "z": 1000, "height": 110, "width": 960, "tabOrder": 1000},
    "visual": {
        "visualType": "multiRowCard",
        "query": {
            "queryState": {
                "Values": {
                    "projections": [
                        agg_field("baltic_executive_country_kpis", "Total_Net_Sales_EUR", 0),
                        agg_field("baltic_executive_country_kpis", "Total_Transactions", 0),
                        agg_field("baltic_executive_country_kpis", "Active_Stores", 0),
                        agg_field("baltic_executive_country_kpis", "Total_Promo_Discount_EUR", 0)
                    ]
                }
            }
        },
        "visualContainerObjects": card_container_style("BALTIC EXECUTIVE KPI OVERVIEW (NET SALES € • VALIDATED BASKETS • ACTIVE STORES • PROMO SPEND €)", "#0050AA"),
        "drillFilterOtherVisuals": True
    }
})

save_visual(vdir1, "v0slicer", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
    "name": "v0slicer",
    "position": {"x": 982, "y": 60, "z": 1500, "height": 110, "width": 286, "tabOrder": 1500},
    "visual": {
        "visualType": "slicer",
        "query": {
            "queryState": {
                "Values": {
                    "projections": [col_field("baltic_executive_country_kpis", "Country")]
                }
            }
        },
        "objects": {
            "data": [{"properties": {"mode": {"expr": {"Literal": {"Value": "'Basic'"}}}}}]
        },
        "visualContainerObjects": card_container_style("BALTIC MARKET FILTER (LT / LV / EE)", "#FFF000"),
        "drillFilterOtherVisuals": True
    }
})

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

save_visual(vdir1, "v1campRoi", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
    "name": "v1campRoi",
    "position": {"x": 12, "y": 178, "z": 2000, "height": 266, "width": 680, "tabOrder": 2000},
    "visual": {
        "visualType": "clusteredBarChart",
        "query": {
            "queryState": {
                "Category": {"projections": [col_field("campaign_pre_post_incrementality_roi", "campaign_name")]},
                "Y": {"projections": [agg_field("campaign_pre_post_incrementality_roi", "Net_Campaign_ROI_Pct", 0)]}
            },
            "sortDefinition": {
                "sort": [{
                    "field": agg_field("campaign_pre_post_incrementality_roi", "Net_Campaign_ROI_Pct", 0)["field"],
                    "direction": "Descending"
                }],
                "isDefaultSort": True
            }
        },
        "objects": {
            "labels": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
            "dataPoint": dp_camp
        },
        "visualContainerObjects": card_container_style("1. Campaign Pre/Post True Net Incremental ROI (%) — Winners vs. Cherry-Picked Losses", "#003876"),
        "drillFilterOtherVisuals": True
    }
})

save_visual(vdir1, "v2balticSales", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
    "name": "v2balticSales",
    "position": {"x": 702, "y": 178, "z": 2500, "height": 266, "width": 566, "tabOrder": 2500},
    "visual": {
        "visualType": "clusteredColumnChart",
        "query": {
            "queryState": {
                "Category": {"projections": [col_field("baltic_executive_country_kpis", "Country")]},
                "Y": {
                    "projections": [
                        agg_field("baltic_executive_country_kpis", "Avg_Basket_Loyalty_EUR", 0),
                        agg_field("baltic_executive_country_kpis", "Avg_Basket_Guest_EUR", 0)
                    ]
                }
            }
        },
        "objects": {
            "labels": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
            "dataPoint": [
                {"properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#003876'"}}}}}}, "selector": {"metadata": "Sum(baltic_executive_country_kpis.Avg_Basket_Loyalty_EUR)"}},
                {"properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#F39C12'"}}}}}}, "selector": {"metadata": "Sum(baltic_executive_country_kpis.Avg_Basket_Guest_EUR)"}}
            ]
        },
        "visualContainerObjects": card_container_style("2. Baltic Basket Uplift: Loyalty App (€29.3) vs. Non-Loyalty Guest (€16.4)", "#003876"),
        "drillFilterOtherVisuals": True
    }
})

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

save_visual(vdir1, "v3rfmSeg", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
    "name": "v3rfmSeg",
    "position": {"x": 12, "y": 452, "z": 3000, "height": 256, "width": 615, "tabOrder": 3000},
    "visual": {
        "visualType": "donutChart",
        "query": {
            "queryState": {
                "Category": {"projections": [col_field("customer_rfm_promo_segmentation", "customer_archetype")]},
                "Y": {"projections": [agg_field("customer_rfm_promo_segmentation", "Total_Net_Sales_EUR", 0)]}
            }
        },
        "objects": {
            "labels": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
            "dataPoint": dp_rfm
        },
        "visualContainerObjects": card_container_style("3. Loyalty Revenue Share (€) by Customer RFM & Promo Segment", "#003876"),
        "drillFilterOtherVisuals": True
    }
})

save_visual(vdir1, "v4funnel", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
    "name": "v4funnel",
    "position": {"x": 638, "y": 452, "z": 4000, "height": 256, "width": 630, "tabOrder": 4000},
    "visual": {
        "visualType": "funnel",
        "query": {
            "queryState": {
                "Category": {"projections": [col_field("loyalty_app_customer_journey_funnel", "Funnel_Stage")]},
                "Y": {"projections": [agg_field("loyalty_app_customer_journey_funnel", "Users_Count", 0)]}
            },
            "sortDefinition": {
                "sort": [{
                    "field": agg_field("loyalty_app_customer_journey_funnel", "Users_Count", 0)["field"],
                    "direction": "Descending"
                }],
                "isDefaultSort": True
            }
        },
        "objects": {
            "labels": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
            "dataPoint": [{"properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#0050AA'"}}}}}}}]
        },
        "visualContainerObjects": card_container_style("4. Loyalty App Customer Journey Funnel (50,000 Registered Members)", "#003876"),
        "drillFilterOtherVisuals": True
    }
})

# ==============================================================================
# PAGE 2: CAMPAIGN INCREMENTALITY, HALO EFFECT & BUDGET ANALYTICS
# ==============================================================================
vdir2 = init_page("ReportSection2", "2. Campaign ROI, Halo & Budget")
add_top_banner(vdir2, "PAGE 2: END-TO-END CAMPAIGN INCREMENTALITY, CANNIBALIZATION, HALO SPEND & BUDGET VARIANCE")

save_visual(vdir2, "p2_kpis", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
    "name": "p2_kpis",
    "position": {"x": 12, "y": 60, "z": 1000, "height": 110, "width": 940, "tabOrder": 1000},
    "visual": {
        "visualType": "multiRowCard",
        "query": {
            "queryState": {
                "Values": {
                    "projections": [
                        agg_field("campaign_pre_post_incrementality_roi", "planned_budget_eur", 0),
                        agg_field("campaign_pre_post_incrementality_roi", "Total_Discount_Cost_EUR", 0),
                        agg_field("campaign_pre_post_incrementality_roi", "True_Incremental_Revenue_EUR", 0),
                        agg_field("campaign_pre_post_incrementality_roi", "Net_Incremental_Margin_EUR", 0)
                    ]
                }
            }
        },
        "visualContainerObjects": card_container_style("CAMPAIGN PORTFOLIO FINANCIAL SUMMARY (PLANNED BUDGET € • ACTUAL DISCOUNT € • TRUE INCREMENTAL SALES € • NET MARGIN €)", "#0050AA"),
        "drillFilterOtherVisuals": True
    }
})

save_visual(vdir2, "p2_slicer", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
    "name": "p2_slicer",
    "position": {"x": 962, "y": 60, "z": 1500, "height": 110, "width": 306, "tabOrder": 1500},
    "visual": {
        "visualType": "slicer",
        "query": {
            "queryState": {
                "Values": {
                    "projections": [col_field("campaign_pre_post_incrementality_roi", "commercial_classification")]
                }
            }
        },
        "objects": {
            "data": [{"properties": {"mode": {"expr": {"Literal": {"Value": "'Basic'"}}}}}]
        },
        "visualContainerObjects": card_container_style("CAMPAIGN CLASSIFICATION FILTER", "#FFF000"),
        "drillFilterOtherVisuals": True
    }
})

# Visual P2-1: Promo Item Spend vs Non-Promo Attached Halo Spend (€) per Basket
save_visual(vdir2, "p2_halo", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
    "name": "p2_halo",
    "position": {"x": 12, "y": 178, "z": 2000, "height": 266, "width": 630, "tabOrder": 2000},
    "visual": {
        "visualType": "clusteredBarChart",
        "query": {
            "queryState": {
                "Category": {"projections": [col_field("campaign_pre_post_incrementality_roi", "campaign_name")]},
                "Y": {
                    "projections": [
                        agg_field("campaign_pre_post_incrementality_roi", "Avg_Halo_Other_Spend_EUR", 0),
                        agg_field("campaign_pre_post_incrementality_roi", "Avg_Promo_Item_Spend_EUR", 0)
                    ]
                }
            },
            "sortDefinition": {
                "sort": [{
                    "field": agg_field("campaign_pre_post_incrementality_roi", "Avg_Halo_Other_Spend_EUR", 0)["field"],
                    "direction": "Descending"
                }],
                "isDefaultSort": True
            }
        },
        "objects": {
            "labels": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
            "dataPoint": [
                {"properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#1E824C'"}}}}}}, "selector": {"metadata": "Sum(campaign_pre_post_incrementality_roi.Avg_Halo_Other_Spend_EUR)"}},
                {"properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#0050AA'"}}}}}}, "selector": {"metadata": "Sum(campaign_pre_post_incrementality_roi.Avg_Promo_Item_Spend_EUR)"}}
            ]
        },
        "visualContainerObjects": card_container_style("1. Basket Halo Decomposition: Non-Promo Attached Spend (€) vs. Promo Item Spend (€)", "#003876"),
        "drillFilterOtherVisuals": True
    }
})

# Visual P2-2: Cannibalization Rate (%) vs Post-Campaign Pantry Dip (%) by Campaign
save_visual(vdir2, "p2_cannib", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
    "name": "p2_cannib",
    "position": {"x": 652, "y": 178, "z": 2500, "height": 266, "width": 616, "tabOrder": 2500},
    "visual": {
        "visualType": "clusteredColumnChart",
        "query": {
            "queryState": {
                "Category": {"projections": [col_field("campaign_pre_post_incrementality_roi", "mechanic_type")]},
                "Y": {
                    "projections": [
                        agg_field("campaign_pre_post_incrementality_roi", "Cannibalization_Rate_Pct", 1),
                        agg_field("campaign_pre_post_incrementality_roi", "Post_Campaign_Pantry_Dip_Pct", 1),
                        agg_field("campaign_pre_post_incrementality_roi", "Cherry_Picker_Share_Pct", 1)
                    ]
                }
            }
        },
        "objects": {
            "labels": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
            "dataPoint": [
                {"properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#F39C12'"}}}}}}, "selector": {"metadata": "Avg(campaign_pre_post_incrementality_roi.Cannibalization_Rate_Pct)"}},
                {"properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#D92B2B'"}}}}}}, "selector": {"metadata": "Avg(campaign_pre_post_incrementality_roi.Post_Campaign_Pantry_Dip_Pct)"}},
                {"properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#8E44AD'"}}}}}}, "selector": {"metadata": "Avg(campaign_pre_post_incrementality_roi.Cherry_Picker_Share_Pct)"}}
            ]
        },
        "visualContainerObjects": card_container_style("2. Erosion Drivers by Mechanic: Cannibalization % • Pantry Dip % • Cherry-Picker Share %", "#003876"),
        "drillFilterOtherVisuals": True
    }
})

# Visual P2-3: Bottom-Left Planned Promotional Budget vs Actual Discount Spend (€)
save_visual(vdir2, "p2_budget", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
    "name": "p2_budget",
    "position": {"x": 12, "y": 452, "z": 3000, "height": 256, "width": 630, "tabOrder": 3000},
    "visual": {
        "visualType": "clusteredColumnChart",
        "query": {
            "queryState": {
                "Category": {"projections": [col_field("campaign_pre_post_incrementality_roi", "target_category")]},
                "Y": {
                    "projections": [
                        agg_field("campaign_pre_post_incrementality_roi", "planned_budget_eur", 0),
                        agg_field("campaign_pre_post_incrementality_roi", "Total_Discount_Cost_EUR", 0)
                    ]
                }
            }
        },
        "objects": {
            "labels": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
            "dataPoint": [
                {"properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#003876'"}}}}}}, "selector": {"metadata": "Sum(campaign_pre_post_incrementality_roi.planned_budget_eur)"}},
                {"properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#28A197'"}}}}}}, "selector": {"metadata": "Sum(campaign_pre_post_incrementality_roi.Total_Discount_Cost_EUR)"}}
            ]
        },
        "visualContainerObjects": card_container_style("3. Strategic Budget Tracking: Planned Budget (€) vs. Actual Discount Redemptions (€)", "#003876"),
        "drillFilterOtherVisuals": True
    }
})

# Visual P2-4: Bottom-Right Net Incremental Margin (€) by Campaign
save_visual(vdir2, "p2_margin", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
    "name": "p2_margin",
    "position": {"x": 652, "y": 452, "z": 3500, "height": 256, "width": 616, "tabOrder": 3500},
    "visual": {
        "visualType": "clusteredBarChart",
        "query": {
            "queryState": {
                "Category": {"projections": [col_field("campaign_pre_post_incrementality_roi", "campaign_name")]},
                "Y": {"projections": [agg_field("campaign_pre_post_incrementality_roi", "Net_Incremental_Margin_EUR", 0)]}
            },
            "sortDefinition": {
                "sort": [{
                    "field": agg_field("campaign_pre_post_incrementality_roi", "Net_Incremental_Margin_EUR", 0)["field"],
                    "direction": "Descending"
                }],
                "isDefaultSort": True
            }
        },
        "objects": {
            "labels": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
            "dataPoint": dp_camp
        },
        "visualContainerObjects": card_container_style("4. Net Incremental Profit Margin Impact (€) After Discount Cost & Cannibalization", "#003876"),
        "drillFilterOtherVisuals": True
    }
})

# ==============================================================================
# PAGE 3: CUSTOMER JOURNEY, RFM SEGMENTS & STORE FORMAT PERFORMANCE
# ==============================================================================
vdir3 = init_page("ReportSection3", "3. Customer RFM & Store Formats")
add_top_banner(vdir3, "PAGE 3: CUSTOMER RFM SEGMENTATION, WEEKLY POS TRAJECTORY & BALTIC STORE FORMAT ANALYTICS")

save_visual(vdir3, "p3_kpis", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
    "name": "p3_kpis",
    "position": {"x": 12, "y": 60, "z": 1000, "height": 110, "width": 940, "tabOrder": 1000},
    "visual": {
        "visualType": "multiRowCard",
        "query": {
            "queryState": {
                "Values": {
                    "projections": [
                        agg_field("customer_rfm_promo_segmentation", "Unique_Customers", 0),
                        agg_field("customer_rfm_promo_segmentation", "Total_Transactions", 0),
                        agg_field("customer_rfm_promo_segmentation", "Total_Net_Sales_EUR", 0),
                        agg_field("customer_rfm_promo_segmentation", "Total_Net_Margin_EUR", 0)
                    ]
                }
            }
        },
        "visualContainerObjects": card_container_style("LOYALTY MEMBER BASE SUMMARY (ACTIVE MEMBERS • LOYALTY BASKETS • LOYALTY NET SALES € • NET MARGIN €)", "#0050AA"),
        "drillFilterOtherVisuals": True
    }
})

save_visual(vdir3, "p3_slicer", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
    "name": "p3_slicer",
    "position": {"x": 962, "y": 60, "z": 1500, "height": 110, "width": 306, "tabOrder": 1500},
    "visual": {
        "visualType": "slicer",
        "query": {
            "queryState": {
                "Values": {
                    "projections": [col_field("customer_rfm_promo_segmentation", "customer_archetype")]
                }
            }
        },
        "objects": {
            "data": [{"properties": {"mode": {"expr": {"Literal": {"Value": "'Basic'"}}}}}]
        },
        "visualContainerObjects": card_container_style("CUSTOMER RFM ARCHETYPE FILTER", "#FFF000"),
        "drillFilterOtherVisuals": True
    }
})

# Visual P3-1: Average Net Basket (€) vs Coupon Dependency Rate (%) by RFM Segment
save_visual(vdir3, "p3_rfmBasket", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
    "name": "p3_rfmBasket",
    "position": {"x": 12, "y": 178, "z": 2000, "height": 266, "width": 630, "tabOrder": 2000},
    "visual": {
        "visualType": "clusteredBarChart",
        "query": {
            "queryState": {
                "Category": {"projections": [col_field("customer_rfm_promo_segmentation", "customer_archetype")]},
                "Y": {
                    "projections": [
                        agg_field("customer_rfm_promo_segmentation", "Avg_Net_Basket_EUR", 0),
                        agg_field("customer_rfm_promo_segmentation", "Coupon_Usage_Rate_Pct", 0)
                    ]
                }
            },
            "sortDefinition": {
                "sort": [{
                    "field": agg_field("customer_rfm_promo_segmentation", "Avg_Net_Basket_EUR", 0)["field"],
                    "direction": "Descending"
                }],
                "isDefaultSort": True
            }
        },
        "objects": {
            "labels": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
            "dataPoint": [
                {"properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#003876'"}}}}}}, "selector": {"metadata": "Sum(customer_rfm_promo_segmentation.Avg_Net_Basket_EUR)"}},
                {"properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#D92B2B'"}}}}}}, "selector": {"metadata": "Sum(customer_rfm_promo_segmentation.Coupon_Usage_Rate_Pct)"}}
            ]
        },
        "visualContainerObjects": card_container_style("1. Segment Economics: Average Net Basket (€) vs. Coupon Dependency Rate (%)", "#003876"),
        "drillFilterOtherVisuals": True
    }
})

# Visual P3-2: Weekly POS Net Sales & Gross Basket Trend across 26 Fiscal Weeks
save_visual(vdir3, "p3_weeklyTrend", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
    "name": "p3_weeklyTrend",
    "position": {"x": 652, "y": 178, "z": 2500, "height": 266, "width": 616, "tabOrder": 2500},
    "visual": {
        "visualType": "lineChart",
        "query": {
            "queryState": {
                "Category": {"projections": [col_field("fact_pos_transactions_gold", "fiscal_week")]},
                "Y": {
                    "projections": [
                        agg_field("fact_pos_transactions_gold", "net_sales_eur", 0),
                        agg_field("fact_pos_transactions_gold", "non_promo_halo_spend_eur", 0)
                    ]
                }
            },
            "sortDefinition": {
                "sort": [{
                    "field": col_field("fact_pos_transactions_gold", "fiscal_week")["field"],
                    "direction": "Ascending"
                }],
                "isDefaultSort": True
            }
        },
        "objects": {
            "labels": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]
        },
        "visualContainerObjects": card_container_style("2. 26-Week POS Trajectory: Weekly Net Sales (€) vs. Non-Promo Halo Basket Spend (€)", "#003876"),
        "drillFilterOtherVisuals": True
    }
})

# Visual P3-3: Net Margin Contribution (€) vs Total Discount Claimed (€) by Customer Segment
save_visual(vdir3, "p3_segMargin", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
    "name": "p3_segMargin",
    "position": {"x": 12, "y": 452, "z": 3000, "height": 256, "width": 630, "tabOrder": 3000},
    "visual": {
        "visualType": "clusteredColumnChart",
        "query": {
            "queryState": {
                "Category": {"projections": [col_field("customer_rfm_promo_segmentation", "customer_archetype")]},
                "Y": {
                    "projections": [
                        agg_field("customer_rfm_promo_segmentation", "Total_Net_Margin_EUR", 0),
                        agg_field("customer_rfm_promo_segmentation", "Total_Discount_Claimed_EUR", 0)
                    ]
                }
            }
        },
        "objects": {
            "labels": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
            "dataPoint": [
                {"properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#1E824C'"}}}}}}, "selector": {"metadata": "Sum(customer_rfm_promo_segmentation.Total_Net_Margin_EUR)"}},
                {"properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E67E22'"}}}}}}, "selector": {"metadata": "Sum(customer_rfm_promo_segmentation.Total_Discount_Claimed_EUR)"}}
            ]
        },
        "visualContainerObjects": card_container_style("3. Profit Contribution (€) vs. Promotional Subsidy Claimed (€) by Segment", "#003876"),
        "drillFilterOtherVisuals": True
    }
})

# Visual P3-4: Store Network Distribution by Store Format & City (140 Baltic Stores)
save_visual(vdir3, "p3_storeFormats", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
    "name": "p3_storeFormats",
    "position": {"x": 652, "y": 452, "z": 3500, "height": 256, "width": 616, "tabOrder": 3500},
    "visual": {
        "visualType": "clusteredBarChart",
        "query": {
            "queryState": {
                "Category": {"projections": [col_field("dim_stores", "city")]},
                "Y": {"projections": [agg_field("dim_stores", "store_id", 2)]}
            }
        },
        "objects": {
            "labels": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
            "dataPoint": [{"properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#0050AA'"}}}}}}}]
        },
        "visualContainerObjects": card_container_style("4. Baltic Store Network Footprint by Municipality (140 Stores Across LT, LV, EE)", "#003876"),
        "drillFilterOtherVisuals": True
    }
})

print("Successfully upgraded Power BI Project (.pbip) to a 3-Page Executive Application!")
