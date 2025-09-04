# Modelling-forest-fire-spread
Spread of forest fires are a persistent threat and are a tough challenge for organisations both private and government to manage. This project aims to create real time simulation and modelling of such fire spread considering factors like weather (temperature, precipitation, humidity, wind), terrain (slope, aspect, fuel availability), human activity in the Uttrakhand Area.

This project aims to create a per pixel probability that a 30m grid cell will have a fire tomorrow with a binary map + probabillities. As well as a simulation that, given ignitions in high risk areas, propagates the fire for 1/2/3/6/12 h modulated by wind, slope aspect, and fuels. 

## Grid Template:
This file is to create the template grid raster. This is essentially the "contract" that every other dataset will be alligned to. 
There are a few vairables that need to be explained here.

### CRS: Coordinate Reference System
Defines how the 2D coordinates in the raster (row/col indicies to x/y coordinates) relates to real world locations on Eath. Without this CRs, the raster is just pixels with no geographic meaning. In the code we see ESPG:32644. ESPG is a code registry of coordinate systems. 32644 specifically means: UTM (Universal Transverse Mercator), northern hemisphere, zone 44, on WGs84.  
We use UTM because it uses meters which makes our 30x30 pixels actually 30x30m on the gorund which is crucial for DEM slope/aspect and fire spread modelling. If we used geographic CRS such as CRS:4326 (lat/long in degrees) would make the pixel size 30 degrees which is nonesense. We use zone 44 because UK is mostly in long 77degE to 81degE which is in UTM zone 44N. Each UTM is 6deg wide 
### PIX:
Just means Pixels
### OUT:
Just shorthand for output file path. This is where the raster will be saved. 
    
