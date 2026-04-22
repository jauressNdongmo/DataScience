# Sources de donnees jusqu'a 2025 (officielles)

Objectif: alimenter la plateforme avec des donnees recentes, puis continuer en mode incremental.

## 1) Production/rendement agricole (historique officiel)

- FAOSTAT - Agricultural production statistics 2010-2024 (release 31/12/2025):
  - https://www.fao.org/statistics/highlights-archive/highlights-detail/agricultural-production-statistics-2010-2024/
- FAOSTAT release calendar (update decembre 2025):
  - https://www.fao.org/statistics/events/events-detail/agricultural-production-statistics-2010-2025.-december-2025-update/

Notes:
- Ces releases couvrent les statistiques officielles crop/livestock, avec consolidation annuelle.
- Pour certains sous-domaines (produits transformes), la disponibilite peut etre arretee a une annee anterieure.

## 2) Meteo / pluie / temperature (quasi temps reel)

- NASA POWER Daily API (1981 -> near real-time):
  - https://power.larc.nasa.gov/docs/services/api/temporal/daily/
- NOAA CDO API v2 (meteo globale, token requis):
  - https://www.ncei.noaa.gov/cdo-web/webservices/v2
- CHIRPS v3 precipitation (1981 -> near-present):
  - https://www.chc.ucsb.edu/data/chirps3

## 3) Marche / prix commodities

- World Bank Commodity Markets (Pink Sheet, monthly updates):
  - https://www.worldbank.org/en/research/commodity-markets
- FAO Food Price Index (mensuel + CSV):
  - https://www.fao.org/worldfoodsituation/foodpricesindex/en/

## 4) Vegetation / NDVI (teledection)

- MODIS MOD13Q1 (NDVI/EVI, 16 jours):
  - https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD13Q1
- eVIIRS Global NDVI (near real-time, 10-day composites):
  - https://www.usgs.gov/centers/eros/science/usgs-eros-archive-vegetation-monitoring-eviirs-global-ndvi

## Strategie recommandee

1. Construire un "baseline" avec les donnees officielles consolidees (FAOSTAT + historique local).
2. Ajouter un pipeline incremental mensuel (meteo + prix + NDVI).
3. En 2025+, distinguer:
   - donnees "finales officielles" (stables)
   - donnees "provisoires / nowcasting" (mises a jour frequentes)
4. Mettre a jour le modele en fine-tune et ne promouvoir qu'en cas d'amelioration metrique.
