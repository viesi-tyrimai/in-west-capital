# DVF transaction map — 51 Rue de la Ville en Pierre, Nantes

Two versions of the same dataset.

| File | Basemap | Needs a server? |
|---|---|---|
| `index.html` | OpenStreetMap / CARTO tiles | **Yes** — it fetches the GeoJSON |
| `standalone.html` | none; streets traced from the transaction coordinates themselves | No — fully self-contained, opens from `file://` |

`index.html` is the one published by GitHub Pages at `/map/`. `standalone.html` works offline and inside sandboxes that block external requests.

## The data

**3 472 transactions**, commune 44109 (Nantes), 2021–2025, within 1.5 km of the subject property.

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
6. keep points within 1 500 m of 47.224757, −1.528421

`dvf_sandoriai_geo.csv` and `dvf_sandoriai.geojson` carry the same rows. Both include `latitude` / `longitude`, so they import directly into uMap, QGIS, Felt, Datawrapper or Google My Maps.

## Encoding

- **Colour** — €/m² in five steps: <2 500 · 2 500–3 250 · 3 250–4 000 · 4 000–5 000 · >5 000
- **Size** — floor area
- **Shape** — circle for a flat, square for a house
- **Red crosshair** — the subject property, parcelle 44109000CH0276
- **Rings** — 200, 400, 600, 800 and 1 200 m

## Caveat on `standalone.html`

It has no real basemap. The street lines are fitted through the transaction points of each street (principal axis, split where consecutive points are more than 180 m apart). Point positions are exact; street shapes are approximate. It is a schematic, not a cadastral plan.

## Licences

- DVF data: **Licence Ouverte / Open Licence 2.0** (Etalab), DGFiP
- Basemap in `index.html`: © OpenStreetMap contributors (ODbL), © CARTO
