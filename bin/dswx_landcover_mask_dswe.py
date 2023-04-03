#!/usr/bin/env python3
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# Reference:
# [1] J. W. Jones, "Efficient wetland surface water detection and
# monitoring via Landsat: Comparison with in situ data from the Everglades
# Depth Estimation Network", Remote Sensing, 7(9), 12503-12538.
# http://dx.doi.org/10.3390/rs70912503, 2015
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import argparse
import logging
from proteus.dswx_hls import create_logger

from osgeo import gdal, gdal_array
import numpy as np
import geopandas as gpd
import glob
import time, os
    

logger = logging.getLogger('dswx_hls_landcover_mask')

def _get_parser():
    parser = argparse.ArgumentParser(
        description='Create landcover mask LAND combining Copernicus Global'
        ' Land Service (CGLS) Land Cover Layers collection 3 at 100m and ESA'
        ' WorldCover 10m',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Inputs
    parser.add_argument('input_file',
                        type=str,
                        help='Input HLS product')

    parser.add_argument('-c',
                        '--copernicus-landcover-100m',
                        '--landcover', '--land-cover',
                        dest='landcover_file',
                        required=True,
                        type=str,
                        help='Input Copernicus Land Cover'
                        ' Discrete-Classification-map 100m')

    parser.add_argument('-w',
                        '--world-cover-10m', '--worldcover', '--world-cover',
                        dest='worldcover_file',
                        required=True,
                        type=str,
                        help='Input ESA WorldCover 10m')

    # Outputs
    parser.add_argument('-o',
                        '--output-file',
                        dest='output_file',
                        required=True,
                        type=str,
                        default='output_file',
                        help='Output landcover file (GeoTIFF) over input HLS'
                             ' product grid')

    # Parameters
    parser.add_argument('--mask-type',
                        dest='mask_type',
                        type=str,
                        default='standard',
                        help='Options: "Standard", "Water Heavy", or "Batch"')

    parser.add_argument('--log',
                        '--log-file',
                        dest='log_file',
                        type=str,
                        help='Log file')

    parser.add_argument('--scratch-dir',
                        '--temp-dir',
                        '--temporary-dir',
                        dest='scratch_dir',
                        default='.',
                        type=str,
                        help='Scratch (temporary) directory')
    return parser


def main():
    parser = _get_parser()

    args = parser.parse_args()

    create_logger(args.log_file)

    create_landcover_mask(args.input_file, args.copernicus_landcover_file,
                          args.worldcover_file, args.output_file,
                          args.scratch_dir, args.mask_type)


def create_landcover_mask(DSWE_input, Copernicus_input,
                          ESA_input, dest_path, scratch_dir, mask_type):

    if not os.path.isfile(DSWE_input):
        logger.error(f'ERROR file not found: {DSWE_input}')
        return

    if not os.path.isfile(Copernicus_input):
        logger.error(f'ERROR file not found: {Copernicus_input}')
        return

    if not os.path.isfile(ESA_input):
        logger.error(f'ERROR file not found: {ESA_input}')
        return

    logger.info('')
    logger.info(f'Input file: {DSWE_input}')
    logger.info(f'Copernicus landcover 100 m file: {Copernicus_input}')
    logger.info(f'World cover 10 m file: {ESA_input}')
    logger.info('')

    layer_gdal_dataset = gdal.Open(DSWE_input, gdal.GA_ReadOnly)
    if layer_gdal_dataset is None:
        logger.error(f'ERROR invalid file: {DSWE_input}')
    geotransform = layer_gdal_dataset.GetGeoTransform()
    projection = layer_gdal_dataset.GetProjection()
    length = layer_gdal_dataset.RasterYSize
    width = layer_gdal_dataset.RasterXSize

    dy = geotransform[5]
    dx = geotransform[1]
    y0 = geotransform[3]
    x0 = geotransform[0]

    xf = x0 + width * dx
    yf = y0 + length * dy
    output_bounds = [x0, yf, xf, y0]

    layer_gdal_dataset = None
    del layer_gdal_dataset

    startTime = time.time()

    project_dir = scratch_dir
    if not os.path.isdir(project_dir):
        os.makedirs(project_dir)

    HLS_gdal = gdal.Open(DSWE_input, gdal.GA_ReadOnly)
    HLS_projection = HLS_gdal.GetProjection()
    
    def process_Copernicus(Copernicus_path):
        Copernicus_dataset = gdal.Open(Copernicus_path, gdal.GA_ReadOnly)
        reprojected_copernicus = project_dir + "/Copernicus_reproject_30m.tif"
        Copernicus_reproject = gdal.Warp(reprojected_copernicus, Copernicus_dataset, 
                                         dstSRS=HLS_projection, outputBounds = output_bounds, 
                                         xRes = 30, yRes = 30, resampleAlg='near')
        Copernicus_array = Copernicus_reproject.GetRasterBand(1).ReadAsArray().astype('uint16')
        Copernicus_reproject = None
        Copernicus_dataset = None
        return Copernicus_array

    Copernicus_arrray_30m = process_Copernicus(Copernicus_input)
    

    #ESA World Cover Processing -- Input Mosaaic GeoTiff

    def process_ESA(ESA_path, resolution):
        ESA_dataset = gdal.Open(ESA_path, gdal.GA_ReadOnly)
        ESA_path = project_dir + f"/ESA_reproject_{resolution}m.tif"
        ESA_reproject = gdal.Warp(ESA_path, ESA_dataset, dstSRS=HLS_projection, 
                                  outputBounds = output_bounds, xRes = resolution, yRes = resolution, resampleAlg='near')
        ESA_dataset =  None
        return ESA_reproject

    ESA_10m = process_ESA(ESA_input,10)

    # Conditional Reclassification

    #convert into array
    ESA_array_10m = ESA_10m.GetRasterBand(1).ReadAsArray().astype('uint16')

    # create binary layers of each value were interested in 
    water_binary_mask = np.where((ESA_array_10m == 80) | (ESA_array_10m == 90), 1, 0) #Where ESA array is water value: set to 1. All else: set to 0.
    urban_binary_mask = np.where((ESA_array_10m == 50) , 1,0) # Where ESA array is urban value: set to 1. All else: set to 0.  
    tree_binary_mask  = np.where((ESA_array_10m == 10) , 1,0) # Where ESA array is tree value: set to 1. All else: set to 0. 
    
    ## Aggregate sum 30m resolution 

    #read array back into gdaldataset, assign georeference 
    def aggregate_sum_raster(input_array, mask_name):
        Mask_no_Mask = gdal_array.OpenArray(input_array)
        Mask_no_Mask.SetGeoTransform(ESA_10m.GetGeoTransform())
        Mask_no_Mask.SetProjection(str(HLS_projection))
        reprojected_filename = project_dir +f"/aggregate_sum_{mask_name}_30m.tif"
        aggregate_ds = gdal.Warp(reprojected_filename, Mask_no_Mask, xRes=30, yRes=30, 
                                  outputBounds = output_bounds, dstSRS=HLS_projection, resampleAlg='sum')
        
        aggregate_array = aggregate_ds.GetRasterBand(1).ReadAsArray().astype('uint16')
      
        return aggregate_array
    
    def create_LCMASK(mask_flavor):
        def get_thresholds(mask_flavor):
            key = (mask_flavor).lower()
            threshold_dictionary = {
                "standard": [6, 3, 7, 3],
                "water heavy": [6, 3, 7, 1],
                }
            thresholds = threshold_dictionary[key]
            return thresholds
                       
        
        def assign_hierarchy():
            
            h20_aggregate_sum = aggregate_sum_raster(water_binary_mask, "80")
            urban_aggregate_sum = aggregate_sum_raster(urban_binary_mask, "50")
            tree_aggregate_sum = aggregate_sum_raster(tree_binary_mask, "10")
            
            # Filter sum by Evergreen Classificaiton
            
            tree_aggregate_sum = np.where((Copernicus_arrray_30m == 111), tree_aggregate_sum, 0 )
            
            def write_array(conglomerate_array, agg_sum, threshold, classification_val):
                flat_agg = agg_sum.reshape(-1)
                for position, value in enumerate(flat_agg):
                    if value > threshold:
                        conglomerate_array[position] = classification_val
                return
              
            hierarchy_combined = np.full(h20_aggregate_sum.reshape(-1).shape, 30000)
            
            threshold_list = get_thresholds(mask_flavor)
            write_array(hierarchy_combined, tree_aggregate_sum, threshold_list[0], 42) # aggregate sum value of 7/9 or higher is called tree
            write_array(hierarchy_combined, urban_aggregate_sum, threshold_list[1], 2019) # majority of pixels are urban 
            write_array(hierarchy_combined, urban_aggregate_sum, threshold_list[2], 20191) # high density urban at 7/9 or higher
            write_array(hierarchy_combined, h20_aggregate_sum, threshold_list[3], 25000 ) # water where 1/3 or more pixels
            
            hierarchy_combined = hierarchy_combined.reshape(h20_aggregate_sum.shape)
        
            return hierarchy_combined
        
        reclassified_array = assign_hierarchy()
        
        def array_to_geotiff(input_array, outpath):
    
            driver = gdal.GetDriverByName("GTiff") 
            driver.Register()
            out_ds = driver.Create(outpath, xsize = input_array.shape[0],
                                     ysize = input_array.shape[1], bands =1, 
                                     eType = gdal.GDT_UInt16)
            out_ds.SetGeoTransform(HLS_gdal.GetGeoTransform())
            out_ds.SetProjection(HLS_projection)
            outband = out_ds.GetRasterBand(1)
            outband.WriteArray(input_array)
            outband.SetNoDataValue(-9999)
            outband.FlushCache()
            
            #close datasets
            outband = None
            out_ds = None
            return

        # dest_path = output_dir+f"/{LOC_ID}_{mask_flavor.lower().replace(' ', '_')}_LCMASK_CGLS_LC100.tif"

        array_to_geotiff(reclassified_array, dest_path)

    if mask_type.lower() == 'batch':
        create_LCMASK('standard')
        create_LCMASK('water heavy')
    else:
        create_LCMASK(mask_type)
    

    executionTime = round((time.time() - startTime), 2)
    print(f'Total time: {executionTime} seconds')
    return print("Completed. Saved resulting LCMASK Geotiff(s)")


if __name__ == '__main__':
    main()