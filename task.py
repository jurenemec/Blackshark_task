#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 19 09:33:25 2021

@author: juren
"""
from sentinelhub import WmsRequest, CRS, BBox, DataCollection, SHConfig
import matplotlib.pyplot as plt
import numpy as np
from osgeo import gdal_array
import osgeo 
import subprocess

"""
Bounding box definition
"""

#  3) ``[min_x,min_y,max_x,max_y]``,
# bbox=[47.003436,15.370560,47.109626,15.506172]
bbox=[15.370560,47.003436,15.506172,47.109626]
search_bbox = BBox(bbox=bbox, crs=CRS.WGS84)

"""
Authetication for sentinelhub
"""
INSTANCE_ID = '33f0c3c8-4a08-4ae0-b1cc-7f8fd834c071'



if INSTANCE_ID:
    config = SHConfig()
    config.instance_id = INSTANCE_ID
else:
    config = None

    
"""
Request for the Sentinel 2 data from sentinelhub
"""    
wms_true_color_request = WmsRequest(
    data_collection=DataCollection.SENTINEL2_L1C,
    layer='TRUE-COLOR-S2-L2A',
    bbox=search_bbox,
    time='2020-08-08',
    width=2100,
    config=config
)

wms_true_color_img = wms_true_color_request.get_data()

"""
Raster preview
"""
raster=wms_true_color_img[0][:,:,0:3]
plt.imshow(raster)
plt.show()
plt.close()



new_raster=np.empty((3, raster.shape[0],raster.shape[1]) )
new_raster[0]=raster[:,:,0]
new_raster[1]=raster[:,:,1]
new_raster[2]=raster[:,:,2]
"""
Saving the array  a tif file
"""
gdal_array.SaveArray(new_raster, "graz_raster.tif")


"""
Defining data for the world file 
"""
world_file_data=[[(bbox[2]-bbox[0])/raster.shape[1]],
                 [0],
                 [0],
                 [(bbox[1]-bbox[3])/raster.shape[0]],
                 [bbox[0]],
                 [bbox[3]],
                 ]
"""
saving the raster file
"""
np.savetxt("graz_raster.tfw", world_file_data)

"""
Importing the overlaying graz and buildings rasters
"""
raster=gdal_array.LoadFile("graz.tif")
buildings=gdal_array.LoadFile("buildings.tif")

"""
defining a mask raster
"""
buildings_mask=np.zeros((buildings.shape[1],buildings.shape[2]))


"""
Setting values in the mask to 1 where the buildings ara
"""
for i in range(3):
    buildings_mask[np.where(buildings[i]!=255)]=1


for channel in range(3):
    raster[channel]=raster[channel]*buildings_mask
    
    
gdal_array.SaveArray(raster[0:3], "masked_raster.tif")


"""
Using gdal to save the masked raster to a GeoTiff
"""
driver=osgeo.gdal.GetDriverByName("GTiff")
options = ['PHOTOMETRIC=RGB', 'PROFILE=GeoTIFF']

dataset=driver.Create("masked_raster.tif",
                      raster.shape[2],
                      raster.shape[1],
                      3, 
                      osgeo.gdal.GDT_UInt16, options)        
dataset.GetRasterBand(1).WriteArray(raster[0])
dataset.GetRasterBand(2).WriteArray(raster[1])
dataset.GetRasterBand(3).WriteArray(raster[2])
dataset.FlushCache()
dataset = None


world_file_data=[[(bbox[2]-bbox[0])/raster.shape[2]],
                 [0],
                 [0],
                 [(bbox[1]-bbox[3])/raster.shape[1]],
                 [bbox[0]],
                 [bbox[3]],
                 ]

np.savetxt("masked_raster.tfw", world_file_data)


"""
Using gdal eddit to add the CRS tag and upperleft and lowerright tag
"""
bashCommand="gdal_edit.py -mo DATUM=WGS84 masked_raster.tif"
process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
output, error = process.communicate()
print(output, error)


bashCommand="gdal_edit.py -a_ullr "+str(bbox[0])+" "+str(bbox[3])+" "+str(bbox[2])+" "+str(bbox[1])+" masked_raster.tif"
process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
output, error = process.communicate()
print(output, error)

"""
Using gdalwarp to change the CRS from WGS84 to EPSG:3857
"""
bashCommand="gdalwarp -t_srs EPSG:3857 masked_raster.tif masked_raster_proj.tif"
process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
output, error = process.communicate()
print(output, error)

"""
Using gdal2tiles to get the 512 tiles -- NOT YET WORKING
"""
bashCommand="gdal2tiles.py -n -tilesize=512 -s EPSG:3857  masked_raster_proj.tif /home/juren/Dropbox/blackshark/tiles/"
process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
output, error = process.communicate()
print(output, error)