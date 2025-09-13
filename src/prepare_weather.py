from pathlib import Path
import numpy as np
import xarray as xr
import rioxarray as rxr

ROOT = Path(__file__).resolve().parent.parent
TEMPL = ROOT / "grid" / "template_30m.tif"

RAW_DIR = ROOT / "data" / "weather"
INSTANT_NC = RAW_DIR / "data_stream-oper_stepType-instant.nc"  # t2m, d2m, u10, v10
ACCUM_NC   = RAW_DIR / "data_stream-oper_stepType-accum.nc"    # tp
OUT_DIR    = ROOT / "data" / "weather"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# lat decreases north->south in ERA5; slice expects (max, min)
LAT_MAX, LAT_MIN = 31.8, 28.2
LON_MIN, LON_MAX = 77.0, 81.8

def wind_speed_dir(u, v):
    """m/s and direction (deg, 0..360; 0=N, 90=E)."""
    spd = np.hypot(u, v)
    direc = (np.degrees(np.arctan2(u, v)) + 360) % 360
    return spd, direc

def rh_from_t_td(tk, tdk):
    """Relative humidity from 2m temp & dewpoint (Kelvin). Output in %."""
    tc, tdc = tk - 273.15, tdk - 273.15
    es = 6.112 * np.exp((17.67 * tc) / (tc + 243.5))
    e  = 6.112 * np.exp((17.67 * tdc) / (tdc + 243.5))
    return np.clip(100.0 * (e / es), 0, 100)

def to_template_tif(da_latlon, out_path, template_path=TEMPL):
    # ensure CRS + spatial dims set
    da = da_latlon.rio.write_crs("EPSG:4326", inplace=False)
    da = da.rio.set_spatial_dims(x_dim="longitude", y_dim="latitude", inplace=False)
    # open template once and reproject_match
    tmpl = rxr.open_rasterio(template_path, masked=True)
    # da has no band dimension; add one to satisfy rioxarray writer expectations
    da1 = da.expand_dims({"band": [1]})
    da_match = da1.rio.reproject_match(tmpl, resampling=rxr.rio._io.enums.Resampling.bilinear)
    # save
    da_match.rio.to_raster(out_path, compress="DEFLATE")

def main():
    if not INSTANT_NC.exists() or not ACCUM_NC.exists():
        raise FileNotFoundError("Missing ERA5 .nc files in data/weather/.")
    inst = xr.open_dataset(INSTANT_NC)
    accum = xr.open_dataset(ACCUM_NC)

    # crop to bbox (faster). ERA5 latitude is descending; use slice(max, min)
    inst = inst.sel(latitude=slice(LAT_MAX, LAT_MIN), longitude=slice(LON_MIN, LON_MAX))
    accum = accum.sel(latitude=slice(LAT_MAX, LAT_MIN), longitude=slice(LON_MIN, LON_MAX))

    # pull variables (names as provided by CDS)
    u10 = inst["u10"]   # m/s (instant)
    v10 = inst["v10"]   # m/s (instant)
    t2m = inst["t2m"]   # K   (instant)
    d2m = inst["d2m"]   # K   (instant)
    tp  = accum["tp"]   # m   (accum per hour); we sum to mm/day

    # daily aggregations
    u10_d = u10.resample(time="1D").mean()
    v10_d = v10.resample(time="1D").mean()
    t2m_d = t2m.resample(time="1D").mean()
    d2m_d = d2m.resample(time="1D").mean()
    tp_d  = (tp.resample(time="1D").sum()) * 1000.0  

    # iterate each date and write all outputs
    dates = [np.datetime_as_string(t, unit="D") for t in u10_d["time"].values]
    for d in dates:
        # Select slices
        u = u10_d.sel(time=d)
        v = v10_d.sel(time=d)
        t = t2m_d.sel(time=d)
        td = d2m_d.sel(time=d)
        p = tp_d.sel(time=d)

        # derivations
        spd_da, dir_da = wind_speed_dir(u, v)            
        rh_da = xr.apply_ufunc(rh_from_t_td, t, td)      

        # temperature to c
        t_c = t - 273.15

        
        to_template_tif(spd_da, OUT_DIR / f"{d}_wind_speed_30m.tif")
        to_template_tif(dir_da, OUT_DIR / f"{d}_wind_dir_30m.tif")
        to_template_tif(t_c,    OUT_DIR / f"{d}_t2m_30m.tif")
        to_template_tif(rh_da,  OUT_DIR / f"{d}_rh_30m.tif")
        to_template_tif(p,      OUT_DIR / f"{d}_tp_30m.tif")
        print(f"[ok] {d}")

    print("\n[done] Wrote daily weather rasters to:", OUT_DIR)

if __name__ == "__main__":
    main()
