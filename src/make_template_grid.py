from pathlib import Path
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.transform import from_origin

AOI = "data/aoi/uttarakhand.geojson"
#Coordinate Reference System"
CRS = "EPSG:32644" #UTM zone 4
PIX = 30
OUT = "grid/template_30m.tif"

Path("grid").mkdir(exist_ok=True)
poly = gpd.read_file(AOI).to_crs(CRS).geometry.unary_union
minx, miny, maxx, maxy = poly.bounds

minx = np.floor(minx/PIX)*PIX; miny = np.floor(miny/PIX)*PIX

maxx = np.ceil(maxx/PIX)*PIX; maxy = np.ceil(maxy/PIX)*PIX

W = int((maxx-minx)/PIX); H = int((maxy-miny)/PIX)

transform = from_origin(minx, maxy, PIX, PIX)

with rasterio.open(
    OUT, 'w', driver='GTiff', height=H, width=W, count=1, dtype='uint8', crs=CRS, transform=transform, nodata=0, compress='DEFLATE' 
) as dst:
    dst.write(np.zeros((1, H, W), dtype='uint8'))
print(f"[ok] wrote {OUT} ({W}x{H}@30m)")
