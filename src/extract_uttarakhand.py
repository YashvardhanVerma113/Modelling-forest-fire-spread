import geopandas as gpd

gdf = gpd.read_file("data/aux/gadm41_IND_1.shp")
#checking if shapefile is printing states
#print(gdf.columns)
#print(gdf.head())
#print(gdf["NAME_1"].unique())
#filter UK
utt = gdf[gdf["NAME_1"] == "Uttarakhand"]
#saving to a GeoJSON
utt.to_file("data/aoi/uttarakhand.geojson", driver="GeoJSON")
