# DVF transaction maps — Loire-Atlantique

| File | What it is | Needs a server? |
|---|---|---|
| `index.html` | landing page listing the available maps | no |
| `app.html?c=<slug>` | the map, over OpenStreetMap / CARTO tiles | **yes** — it fetches `data/<slug>.geojson` |
| `standalone-nantes.html` | Nantes only, fully self-contained, streets traced from the transaction coordinates | no — opens from `file://` |
| `data/<slug>.geojson` · `.csv` | one dataset per subject property | — |

Adding a new subject property is one command:

```
python3 tools/build_dvf_map.py \
    --csv "~/Downloads/*44212*.csv" \
    --slug vallet \
    --label "6-10 Rue du Ribateau, 44330 Vallet" \
    --subject-street "RUE DU RIBATEAU" \
    --out map/data
```

The script prints the same selection funnel shown below, so the numbers are auditable
every time. Then add the slug to the `COMMUNES` array at the top of `app.html`.

## The data

| Slug | Subject | Commune | Scope | Transactions |
|---|---|---|---|---|
| `nantes` | 51 Rue de la Ville en Pierre | 44109 | 1.5 km radius | 3 472 |
| `vallet` | 6-10 Rue du Ribateau | 44212 | whole commune | 507 |
| `ancenis` | 8 Rue Rayer | 44003 | whole commune | 440 |

Nantes uses a radius because the commune holds 26 584 clean sales and almost all of them are
irrelevant to a property in Doulon. Vallet and Ancenis are small enough that the commune *is* the
market, so they carry no radius: pass `--radius 0` and the map fits to the commune boundary, which
`app.html` pulls live from `geo.api.gouv.fr` and draws as a dashed outline.

Built from the raw `geo-dvf` commune files, one per year:

```
https://files.data.gouv.fr/geo-dvf/latest/csv/<year>/communes/44/44109.csv
```

Processing, in order:

1. keep `nature_mutation == "Vente"`
2. de-duplicate rows on `id_mutation, id_parcelle, type_local, surface_reelle_bati, nombre_pieces_principales, lot1_numero`
3. separate `Dépendance` rows — they carry no surface and must not count toward the unit count, though a sale that includes a garage is still a single-unit sale
4. group by `id_mutation`, keep single-type sales of `Appartement` or `Maison`
5. drop €/m² outside 800–16 000 €/m² (data-entry errors)
6. keep points within the radius, when one is set

Around a quarter of Ancenis mutations carry no coordinates — the BAN address match fails more often
there than in Nantes — so `ancenis` maps 440 of its 588 clean sales. Checked for bias: the geocoded
subset medians 2 594 €/m² against 2 477 €/m² for the dropped rows, a 4 % gap on a 148-row sample, so
the map is representative even though it is not complete.

`data/<slug>.csv` and `data/<slug>.geojson` carry the same rows. Both include `latitude` / `longitude`, so they import directly into uMap, QGIS, Felt, Datawrapper or Google My Maps.

## Encoding

- **Colour** — €/m² in five steps: <2 500 · 2 500–3 250 · 3 250–4 000 · 4 000–5 000 · >5 000
- **Size** — floor area
- **Shape** — circle for a flat, square for a house
- **Red crosshair** — the subject property, parcelle 44109000CH0276
- **Rings** — 200, 400, 600, 800 and 1 200 m; suppressed in whole-commune mode, where the dashed
  commune boundary replaces them

## Caveat on `standalone-nantes.html`

It has no real basemap. The street lines are fitted through the transaction points of each street (principal axis, split where consecutive points are more than 180 m apart). Point positions are exact; street shapes are approximate. It is a schematic, not a cadastral plan.

## Licences

- DVF data: **Licence Ouverte / Open Licence 2.0** (Etalab), DGFiP
- Basemap in `app.html`: © OpenStreetMap contributors (ODbL), © CARTO
