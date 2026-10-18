import os
import json
import shutil

BASE_DIR = r"d:\DW- Internship\Lidl-Loyalty-Data-Analyst\baltic-retail-loyalty-analytics"
PAGE_DIR = os.path.join(BASE_DIR, "powerbi", "BalticPlus_Loyalty_Analytics.Report", "definition", "pages", "ReportSection1")
VIS_DIR = os.path.join(PAGE_DIR, "visuals")

# Remove any leftover legacy model.bim or root report.json that conflicts with PBIR v4.0 / TMDL v4.2
legacy_bim = os.path.join(BASE_DIR, "powerbi", "BalticPlus_Loyalty_Analytics.SemanticModel", "model.bim")
legacy_rpt = os.path.join(BASE_DIR, "powerbi", "BalticPlus_Loyalty_Analytics.Report", "report.json")
for p in [legacy_bim, legacy_rpt]:
    if os.path.exists(p):
        os.remove(p)

# Clear old visuals and write upgraded 7 PBIR v4.0 visuals
shutil.rmtree(VIS_DIR, ignore_errors=True)
os.makedirs(VIS_DIR, exist_ok=True)

# 1. Update page.json with Dark-Navy Executive background
page_json = {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
    "name": "ReportSection1",
    "displayName": "Baltic Loyalty Executive Dashboard",
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
with open(os.path.join(PAGE_DIR, "page.json"), "w", encoding="utf-8") as f:
    json.dump(page_json, f, indent=2)

def save_visual(vname, payload):
    vfolder = os.path.join(VIS_DIR, vname)
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

# Visual 0: Top Title Header Banner
save_visual("v0header", {
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
                            "value": "BALTICPLUS LOYALTY & PROMOTIONAL ANALYTICS — EXECUTIVE BOARD DASHBOARD (LITHUANIA • LATVIA • ESTONIA)",
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

# Visual 1: Top Executive KPI Summary Table/Multi-Card (multiRowCard)
save_visual("v0kpis", {
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

# Visual 2: Top-Right Interactive Baltic Market Filter Slicer
save_visual("v0slicer", {
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

# Visual 3: Middle-Left Color-Coded Campaign Pre/Post True Net Incremental ROI (%)
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

save_visual("v1campRoi", {
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

# Visual 4: Middle-Right Side-by-Side Clustered Column Chart (Loyalty Basket € vs Guest Basket € by Country)
save_visual("v2balticSales", {
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

# Visual 5: Bottom-Left Donut Chart (Loyalty Revenue Share by Customer RFM Segment)
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

save_visual("v3rfmSeg", {
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

# Visual 6: Bottom-Right Loyalty App Customer Journey Funnel Chart
save_visual("v4funnel", {
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

print("Upgraded PBIR v4.0 visuals and page.json successfully!")
