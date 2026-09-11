"""
RULE-BASED GAMBIAN AGRONOMIST
=============================
This is not a paid AI API. It is Python if/else knowledge about Gambian farming.

DATA FLOW:
  Button in index.html  ->  app.js POST /api/ai-advice  ->  main.py
  ->  database.get_all_harvests()  ->  generate_localized_advice()  ->  JSON
  ->  app.js paints the AI Farm Advisory card
"""

from collections import defaultdict

REGION_FOCUS = {
    "West Coast Region (WCR)": (
        "Kombo and Brikama market gardens sit close to Greater Banjul. "
        "Watch coastal humidity, tomato/pepper disease pressure, and salt spray "
        "on low-lying plots after high tides."
    ),
    "North Bank Region (NBR)": (
        "NBR is a groundnut and early-millet belt on lighter sandy soils. "
        "The dry season (November–May) dries the profile quickly — conserve "
        "moisture with residue mulch and avoid late ploughing that buries trash."
    ),
    "Lower River Region (LRR)": (
        "LRR mixes upland millet/sorghum with tidal and mangrove rice along the "
        "river. Bunds, salinity, and flood timing matter more here than inland."
    ),
    "Central River Region (CRR)": (
        "CRR hugs the Gambia River (Jahaly–Pacharr and swamp rice). "
        "Use the river for dry-season irrigation, but time pumping around floods "
        "and keep canals clear of weeds."
    ),
    "Upper River Region (URR)": (
        "URR is hotter and drier inland: sorghum, millet, groundnuts, and "
        "lateritic soils. Plant with the first reliable rains and protect soil "
        "from runoff on sloping fields."
    ),
}

CROP_TIPS = {
    "rice": {
        "CRR": "Keep paddies bunded; stagger transplanting so labour and bird-scaring are manageable. Dry-season rice needs reliable river pumping.",
        "LRR": "On tidal/mangrove rice, check salinity after spring tides. Repair bunds before the rains so fields hold fresh water.",
        "default": "Rice wants standing water at tillering. Avoid letting fields crack in the dry season unless you are fallowing.",
    },
    "groundnuts": {
        "NBR": "On NBR sands, calcium at pegging (gypsum or wood ash where available) helps pods fill. Dry nuts quickly on clean tarps to cut aflatoxin.",
        "URR": "Lift when leaves yellow so you do not leave pods in hard dry soil. Store only well-dried kernels off the ground.",
        "default": "Do not stack damp haulms. Aflatoxin risk rises when nuts dry slowly in humidity.",
    },
    "maize": {
        "WCR": "Fall armyworm can build in successive plantings. Scout whorls weekly and avoid leaving volunteer maize.",
        "default": "Plant with the rains, side-dress nitrogen at knee height, and intercrop with cowpea if soil is tired.",
    },
    "millet": {
        "NBR": "Early millet escapes the worst mid-season drought on NBR sands. Thin stands so each hill can tiller.",
        "URR": "Use open-pollinated landraces that finish before the rains stop. Bird damage rises near settlements — harvest promptly.",
        "default": "Millet copes with poor soils better than maize. Keep weeds down for the first 30 days.",
    },
    "sorghum": {
        "URR": "Watch Striga on tired URR fields. Rotate with groundnuts or cowpea and avoid sowing sorghum after sorghum.",
        "default": "Sorghum handles mid-season dry spells. Harvest when grain is hard to reduce bird and mould losses.",
    },
    "tomatoes": {
        "WCR": "Peri-urban WCR gardens sell well in Banjul/Serekunda. Stake plants, mulch, and water in the cool of the day to limit blight.",
        "CRR": "Dry-season tomatoes near the river need regular irrigation but good drainage so bacterial wilt does not spread.",
        "default": "Rotate away from other solanums. Cracked fruit often means irregular watering.",
    },
    "potatoes": {
        "default": "Irish potato is a cool-season, irrigated crop in The Gambia. Use certified seed and loose, well-drained beds.",
    },
    "cassava": {
        "default": "Cassava likes well-drained upland soils. Harvest from 8–12 months; do not leave roots in waterlogged LRR/CRR swamps.",
    },
    "sesame": {
        "LRR": "Sesame fits LRR uplands after early rains. Harvest as soon as lower pods yellow so seed does not shatter.",
        "default": "Sesame is drought-hardy. Avoid waterlogged river-edge soils.",
    },
    "fonio": {
        "default": "Fonio (findi) is a short-season cereal for hungry-season food. Sow on light soils as rains establish; bird-scare at grain fill.",
    },
    "soybeans": {
        "default": "Inoculate if you can get rhizobia. Soybean likes the rains but hates waterlogging — keep it off swamp rice land.",
    },
    "coffee": {
        "default": "Coffee is uncommon in The Gambia's climate. Shade and year-round moisture would be required; consider horticulture instead.",
    },
    "wheat": {
        "default": "Wheat is not a rainy-season crop here. If you trial it, use the cool dry months with irrigation, not the rains.",
    },
}

REGION_CODE = {
    "West Coast Region (WCR)": "WCR",
    "North Bank Region (NBR)": "NBR",
    "Lower River Region (LRR)": "LRR",
    "Central River Region (CRR)": "CRR",
    "Upper River Region (URR)": "URR",
}


def _crop_key(name):
    return name.strip().lower()


def _region_code(location):
    return REGION_CODE.get(location, "")


def _tip_for(crop, location):
    tips = CROP_TIPS.get(_crop_key(crop))
    if not tips:
        return (
            f"{crop} is on the ledger. Match planting to the June–October rains, "
            "and use river or well irrigation only where the crop truly needs a dry-season slot."
        )
    code = _region_code(location)
    return tips.get(code, tips.get("default"))


def generate_localized_advice(harvests):
    """
    Read the ledger (list of dicts from SQLite) and return structured text
    for the AI Farm Advisory card. Called by POST /api/ai-advice in main.py.
    """
    if not harvests:
        return {
            "headline": "No harvests in the ledger yet",
            "summary": (
                "Log at least one crop with a Gambian region, then generate advice. "
                "The agronomist reads SQLite the same way the table does."
            ),
            "sections": [],
        }

    by_region = defaultdict(list)
    for row in harvests:
        by_region[row.get("location") or "West Coast Region (WCR)"].append(row)

    total_kg = sum(float(row["yield_kg"]) for row in harvests)
    regions_used = len(by_region)

    sections = []
    for location in sorted(by_region.keys()):
        rows = by_region[location]
        crops = sorted({row["crop_type"] for row in rows})
        kg = sum(float(row["yield_kg"]) for row in rows)
        field_names = sorted({row["field_name"] for row in rows})

        bullets = [REGION_FOCUS.get(location, "Apply good agronomy for this site.")]
        for crop in crops:
            bullets.append(_tip_for(crop, location))

        if kg < 200:
            bullets.append(
                "Recorded yield for this region is still small — treat figures as a trial "
                "and weigh sacks at market so the next season's ledger is accurate."
            )
        elif kg > 5000:
            bullets.append(
                "You have a commercial-scale volume here. Plan drying, storage, and "
                "NBR/WCR market transport before peak humidity after harvest."
            )

        code = _region_code(location) or location
        sections.append(
            {
                "location": location,
                "kicker": code,
                "headline": f"{', '.join(crops)} · {len(rows)} harvest(s) · {kg:,.0f} kg",
                "fields": ", ".join(field_names),
                "bullets": bullets,
            }
        )

    summary = (
        f"Ledger holds {len(harvests)} harvest(s) totalling {total_kg:,.0f} kg "
        f"across {regions_used} Gambian region(s). Advice below is location-specific "
        f"and based on your saved crop types — not a live internet model."
    )

    return {
        "headline": "Localized notes from your GreenLedger agronomist",
        "summary": summary,
        "sections": sections,
    }
