import glob
import numpy as np
import rasterio
from pathlib import Path
from rasterio.merge import merge
from rasterio.warp import reproject, Resampling

TEMPL = 'grid/template_30m.tif'
TILES_DIR = 'data/lulc/worldcover_tiles/*.tif'
LULC_IN = 'data/lulc/worldcover_2021.tif'     # will be created from tiles
LULC_30 = 'data/lulc/worldcover_30m.tif'
FUEL    = 'data/lulc/fuel_score_30m.tif'

#mosaic all tiles -> single file (if not already present)
tiles = sorted(glob.glob(TILES_DIR))
Path('data/lulc').mkdir(parents=True, exist_ok=True)
if tiles:
    srcs = [rasterio.open(p) for p in tiles]
    mosaic, transform = merge(srcs)
    meta = srcs[0].meta.copy()
    for s in srcs: s.close()
    meta.update(driver='GTiff', height=mosaic.shape[1], width=mosaic.shape[2],
                transform=transform, compress='DEFLATE')
    with rasterio.open(LULC_IN, 'w', **meta) as dst: dst.write(mosaic)
    print(f'[ok] mosaicked -> {LULC_IN}')

# warp to template @30 m 
with rasterio.open(TEMPL) as ref, rasterio.open(LULC_IN) as src:
    prof = ref.profile.copy(); prof.update(dtype='uint16', nodata=0, compress='DEFLATE')
    arr = np.zeros((ref.height, ref.width), dtype='uint16')
    reproject(
        source=rasterio.band(src,1), destination=arr,
        src_transform=src.transform, src_crs=src.crs,
        dst_transform=ref.transform, dst_crs=ref.crs,
        resampling=Resampling.nearest
    )
    with rasterio.open(LULC_30, 'w', **prof) as dst: dst.write(arr,1)

#map classes to fuel
with rasterio.open(LULC_30) as s:
    lc = s.read(1)
    TREE=10; SHRUB=20; GRASS=30; CROP=40; BUILT=50; BARE=60; SNOW=70; WATER=80; WET=90
    fuel = np.select(
        [lc==TREE, lc==SHRUB, lc==GRASS, lc==CROP, lc==BARE, lc==BUILT, lc==WATER, lc==WET],
        [1.0,      0.7,       0.7,       0.5,      0.1,      0.0,       0.0,       0.4],
        default=0.2
    ).astype('float32')
    prof = s.profile.copy(); prof.update(dtype='float32', nodata=np.nan, compress='DEFLATE')
    with rasterio.open(FUEL, 'w', **prof) as dst: dst.write(fuel,1)

print('[ok] wrote', LULC_30, 'and', FUEL)
