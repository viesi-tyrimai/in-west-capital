#!/usr/bin/env python3
"""
build_dvf_map.py — turn raw geo-DVF commune files into map data.

Input:  the per-year commune CSVs from
        https://files.data.gouv.fr/geo-dvf/latest/csv/<year>/communes/<dept>/<insee>.csv
Output: <slug>.geojson and <slug>.csv, ready for map/app.html, uMap, QGIS, Felt
        or Datawrapper.

Example
-------
    python3 tools/build_dvf_map.py \
        --csv ~/Downloads/44212*.csv \
        --slug vallet \
        --label "6-10 Rue du Ribateau, 44330 Vallet" \
        --subject-street "RUE DU RIBATEAU" \
        --subject-number 6 \
        --radius 1500 \
        --out map/data

If --subject-lat/--subject-lon are given they win. Otherwise the subject is
placed at the centroid of the transactions matching --subject-street (and
--subject-number when it is present in the data), which is accurate to the
address centroid the BAN assigns — typically within 20–30 m.

Why each filter exists is documented in map/README.md. The short version: DVF
repeats one sale across several rows, once per land segment, so a naive row
count roughly doubles the real number of transactions.
"""
import argparse, glob, json, math, os, sys

try:
    import pandas as pd
    import numpy as np
except ImportError:
    sys.exit("pandas ir numpy reikalingi:  pip install pandas numpy")

KEEP = ["Appartement", "Maison"]
DEDUP = ["id_mutation", "id_parcelle", "type_local",
         "surface_reelle_bati", "nombre_pieces_principales", "lot1_numero"]


def load(paths):
    frames = []
    for p in paths:
        d = pd.read_csv(p, low_memory=False)
        if "date_mutation" not in d.columns:
            sys.exit(f"{p}: nėra date_mutation stulpelio — ar tai tikrai geo-DVF failas?")
        d["year"] = d["date_mutation"].str[:4].astype(int)
        frames.append(d)
        print(f"  {os.path.basename(p):<28} {len(d):>8,} eilučių  {d['year'].mode()[0]}")
    return pd.concat(frames, ignore_index=True)


def clean(df, lo_psm, hi_psm):
    steps = [(len(df), "neapdorotos eilutės")]
    v = df[df["nature_mutation"] == "Vente"]
    steps.append((len(v), "nature_mutation = Vente"))
    loc = v[v["type_local"].notna()].drop_duplicates(subset=DEDUP)
    steps.append((len(loc), "dedublikuota"))
    main = loc[loc["type_local"] != "Dépendance"]
    steps.append((len(main), "be Dépendance eilučių"))
    dep = loc[loc["type_local"] == "Dépendance"].groupby("id_mutation").size().rename("nd")

    g = main.groupby("id_mutation").agg(
        date=("date_mutation", "first"), year=("year", "first"),
        price=("valeur_fonciere", "first"), n=("type_local", "size"),
        types=("type_local", lambda s: "|".join(sorted(set(s)))),
        surf=("surface_reelle_bati", "sum"), rooms=("nombre_pieces_principales", "sum"),
        num=("adresse_numero", "first"), voie=("adresse_nom_voie", "first"),
        cp=("code_postal", "first"), lat=("latitude", "first"), lon=("longitude", "first"),
        parc=("id_parcelle", "first"))
    g["nd"] = dep.reindex(g.index).fillna(0).astype(int)
    steps.append((len(g), "unikalūs sandoriai"))

    g = g[(g["n"] == 1) & g["types"].isin(KEEP)]
    steps.append((len(g), "vieno objekto butai ir namai"))
    g = g[(g["price"] > 0) & (g["surf"] > 0) & g["lat"].notna()]
    steps.append((len(g), "su kaina, plotu, koordinatėmis"))
    g = g.assign(psm=(g["price"] / g["surf"]).round(0))
    g = g[(g["psm"] > lo_psm) & (g["psm"] < hi_psm)]
    steps.append((len(g), f"be išskirčių ({lo_psm:,.0f}–{hi_psm:,.0f} €/m²)"))
    return g, steps


def locate(g, street, number, lat, lon):
    if lat is not None and lon is not None:
        return float(lat), float(lon), "nurodyta rankiniu būdu"
    if not street:
        sys.exit("Nurodykite --subject-street arba --subject-lat ir --subject-lon.")
    s = g[g["voie"].astype(str).str.upper().str.contains(street.upper(), na=False)]
    if s.empty:
        sys.exit(f"Gatvė '{street}' duomenyse nerasta. Patikrinkite rašybą arba "
                 f"nurodykite --subject-lat ir --subject-lon.")
    exact = s[s["num"] == number] if number is not None else s.iloc[0:0]
    src = exact if not exact.empty else s
    how = (f"{number} {street} sandorio koordinatės" if not exact.empty
           else f"gatvės '{street}' {len(s)} sandorių centroidas")
    return float(src["lat"].mean()), float(src["lon"].mean()), how


def main():
    ap = argparse.ArgumentParser(description="geo-DVF → žemėlapio duomenys")
    ap.add_argument("--csv", nargs="+", required=True, help="geo-DVF CSV failai (galima šablonas)")
    ap.add_argument("--slug", required=True, help="failų pavadinimas, pvz. vallet")
    ap.add_argument("--label", required=True, help="vertinamo objekto adresas, rodomas žemėlapyje")
    ap.add_argument("--subject-street", default=None)
    ap.add_argument("--subject-number", type=int, default=None)
    ap.add_argument("--subject-lat", type=float, default=None)
    ap.add_argument("--subject-lon", type=float, default=None)
    ap.add_argument("--radius", type=int, default=1500,
                    help="metrai; 0 = visa komuna, be atstumo filtro")
    ap.add_argument("--insee", default=None,
                    help="komunos kodas, pvz. 44212 — įrašomas į meta, kad žemėlapis "
                         "galėtų atsisiųsti komunos ribą iš geo.api.gouv.fr")
    ap.add_argument("--rings", default="200,400,600,800,1200", help="atstumo žiedai metrais")
    ap.add_argument("--psm-min", type=float, default=800)
    ap.add_argument("--psm-max", type=float, default=16000)
    ap.add_argument("--out", default="map/data")
    a = ap.parse_args()

    paths = sorted({p for pat in a.csv for p in glob.glob(os.path.expanduser(pat))})
    if not paths:
        sys.exit("Pagal duotą šabloną failų nerasta.")
    print("Įkeliama:")
    df = load(paths)

    g, steps = clean(df, a.psm_min, a.psm_max)
    lat0, lon0, how = locate(g, a.subject_street, a.subject_number, a.subject_lat, a.subject_lon)
    print(f"\nObjekto vieta: {lat0:.6f}, {lon0:.6f}  ({how})")

    k = math.cos(math.radians(lat0)) * 111320.0
    g["dist"] = np.sqrt(((g["lon"] - lon0) * k) ** 2 + ((g["lat"] - lat0) * 111320.0) ** 2).round(0)
    whole = a.radius <= 0
    if not whole:
        g = g[g["dist"] < a.radius].copy()
    else:
        g = g.copy()

    print("\nAtrankos piramidė:")
    for n, txt in steps:
        print(f"  {n:>9,}  {txt}")
    if whole:
        print(f"  {len(g):>9,}  visa komuna, be atstumo filtro  ← žemėlapis")
    else:
        print(f"  {len(g):>9,}  per {a.radius} m nuo objekto  ← žemėlapis")
    if len(g) < 40:
        print("\n  DĖMESIO: mažiau kaip 40 sandorių. Padidinkite --radius arba pridėkite metų.")

    g["voie"] = g["voie"].fillna("").astype(str)
    g["adresas"] = (g["num"].fillna(0).astype(int).astype(str).replace("0", "") + " " + g["voie"]).str.strip()
    g["tipas"] = np.where(g["types"] == "Maison", "namas", "butas")

    os.makedirs(a.out, exist_ok=True)
    cols = {"date": "data", "adresas": "adresas", "cp": "pasto_kodas", "tipas": "tipas",
            "surf": "plotas_m2", "rooms": "kambariai", "nd": "priklausiniai",
            "price": "kaina_eur", "psm": "eur_m2", "dist": "atstumas_m",
            "lat": "latitude", "lon": "longitude", "parc": "sklypas"}
    csv_path = os.path.join(a.out, a.slug + ".csv")
    g[list(cols)].rename(columns=cols).sort_values("atstumas_m").to_csv(csv_path, index=False)

    feats = []
    for _, r in g.iterrows():
        feats.append({"type": "Feature",
                      "geometry": {"type": "Point", "coordinates": [round(r["lon"], 6), round(r["lat"], 6)]},
                      "properties": {"data": r["date"], "adresas": r["adresas"], "tipas": r["tipas"],
                                     "plotas_m2": int(r["surf"]),
                                     "kambariai": int(r["rooms"]) if not pd.isna(r["rooms"]) else 0,
                                     "priklausiniai": int(r["nd"]), "kaina_eur": int(r["price"]),
                                     "eur_m2": int(r["psm"]), "atstumas_m": int(r["dist"]),
                                     "metai": int(r["year"]), "sklypas": r["parc"]}})
    feats.append({"type": "Feature",
                  "geometry": {"type": "Point", "coordinates": [round(lon0, 6), round(lat0, 6)]},
                  "properties": {"tipas": "objektas", "adresas": a.label,
                                 "vieta_nustatyta": how}})
    gj = {"type": "FeatureCollection",
          "name": a.slug,
          "meta": {"label": a.label, "lat": round(lat0, 6), "lon": round(lon0, 6),
                   "mode": "commune" if whole else "radius",
                   "insee": a.insee,
                   "radius_m": 0 if whole else a.radius,
                   "rings": [] if whole else [int(x) for x in a.rings.split(",")],
                   "years": sorted(int(y) for y in g["year"].unique()),
                   "count": len(g), "source": "geo-DVF / DGFiP, Licence Ouverte 2.0",
                   "files": [os.path.basename(p) for p in paths]},
          "features": feats}
    gj_path = os.path.join(a.out, a.slug + ".geojson")
    with open(gj_path, "w", encoding="utf-8") as f:
        json.dump(gj, f, ensure_ascii=False, separators=(",", ":"))

    print(f"\nParašyta:\n  {gj_path}  ({os.path.getsize(gj_path)/1024:.0f} KB)"
          f"\n  {csv_path}  ({os.path.getsize(csv_path)/1024:.0f} KB)")
    print(f"\nAtidarykite:  map/app.html?c={a.slug}")


if __name__ == "__main__":
    main()
