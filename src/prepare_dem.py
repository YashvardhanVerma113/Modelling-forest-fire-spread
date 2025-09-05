from pathlib import Path
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterio.warp import reproject, Resampling

AOI = "data/aoi/uttarakhand.geojson"
DEM_IN = "data/dem/utt_dem_raw.tif" #raw dem
DEM_CLIP = "data/dem/utt_dem_clip.tif"
Template = "grid/template_30m.tif"
DEM_30 = "data/dem/utt_dem_30m.tif"
Slope = "data/dem/utt_slope_deg.tif"
Aspect = "data/dem/utt_aspect_deg.tif"

Path("data/dem").mkdir(parents=True, exist_ok=True)
#clip
aoi = gpd.read_file(AOI)
with rasterio.open(DEM_IN) as src:
    aoi = aoi.to_crs(src.crs)
    geoms = [aoi.geometry.unary_union.__geo_interface__]
    out_img, out_transforms = mask(src, geoms, crop=True)
    meta = src.meta.copy()
    meta.update({"height": out_img.shape[1], "width": out_img.shape[2], "transform": out_transforms})
    with rasterio.open(DEM_CLIP, 'w', **meta) as dst:
        dst.write(out_img)
    print(f"[ok] clipped -> {DEM_CLIP}")

#warp to template
with rasterio.open(Template) as ref, rasterio.open(DEM_CLIP) as src:
    prof = ref.profile.copy(); prof.update(dtype='float32', nodata=np.nan)
    arr = np.zeros((ref.height, ref.width), dtype='float32')
    reproject(
        source = rasterio.band(src,1), destination=arr,
        src_transform=src.transform, src_crs=src.crs,
        dst_transform=ref.transform, dst_crs=ref.crs,
        resampling=Resampling.bilinear
    )
    with rasterio.open(DEM_30, 'w', **prof) as dst: dst.write(arr,1)
print(f"[ok] warped -> {DEM_30}")

#Slope/Aspect
with rasterio.open(DEM_30) as dem:
    z = dem.read(1).astype('float32'); cell = dem.transform.a
    Z = np.pad(z, 1, mode='edge')
    dzdx = ((Z[1:-1,2:] + 2*Z[2:,2:] + Z[2:,1:-1]) - (Z[1:-1,0:-2] + 2*Z[2:,
0:-2] + Z[2:,1:-1]))/(8*cell)
    dzdy = ((Z[0:-2,1:-1] + 2*Z[0:-2,2:] + Z[1:-1,2:]) - (Z[1:-1,0:-2] +
2*Z[2:,0:-2] + Z[2:,1:-1]))/(8*cell)
    slope = np.degrees(np.arctan(np.hypot(dzdx, dzdy)))
    aspect = (np.degrees(np.arctan2(dzdx, -dzdy)) + 360) % 360
    prof = dem.profile.copy(); prof.update(dtype='float32', nodata=np.nan)
    with rasterio.open(Slope, 'w', **prof) as dst: dst.write(slope, 1)
    with rasterio.open(Aspect,'w', **prof) as dst: dst.write(aspect, 1)
print(f"[ok] wrote {Slope} & {Aspect}")

