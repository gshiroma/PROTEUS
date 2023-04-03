#!/usr/bin/env python3
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# Compute Dynamic Surface Water Extent (DSWx) from HLS data
# 
# OPERA
#
# Copyright 2021, by the California Institute of Technology. ALL RIGHTS
# RESERVED. United States Government Sponsorship acknowledged.
# Any commercial use must be negotiated with the Office of Technology Transfer
# at the California Institute of Technology.
#
# This software may be subject to U.S. export control laws. By accepting this
# software, the user agrees to comply with all applicable U.S.
# export laws and regulations. User has the responsibility to obtain export
# licenses, or other export authority as may be required before exporting such
# information to foreign countries or providing access to foreign persons.
#
# 
# References:
# [1] J. W. Jones, "Efficient wetland surface water detection and 
# monitoring via Landsat: Comparison with in situ data from the Everglades 
# Depth Estimation Network", Remote Sensing, 7(9), 12503-12538. 
# http://dx.doi.org/10.3390/rs70912503, 2015
# 
# [2] R. Dittmeier, "LANDSAT DYNAMIC SURFACE WATER EXTENT (DSWE) ALGORITHM 
# DESCRIPTION DOCUMENT (ADD)", USGS, March 2018
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import os
import tempfile
import argparse
import logging
import glob
import plant
from proteus.dswx_hls import generate_dswx_layers, create_logger
 
logger = logging.getLogger('dswx_hls_process_and_mosaic')

def _get_parser():
    parser = argparse.ArgumentParser(description='',
                                          formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Inputs
    parser.add_argument('input_list',
                        type=str,
                        nargs='+',
                        help='Input YAML run configuration file or HLS product file(s)')

    parser.add_argument('--dem',    
                        dest='dem_file',
                        type=str,
                        help='Input digital elevation model (DEM)')

    parser.add_argument('--landcover',
                        dest='landcover_file',
                        type=str,
                        help='Input Land Cover Discrete-Classification-map')

    parser.add_argument('--built-up-cover-fraction',
                        '--builtup-cover-fraction',    
                        dest='worldcover_file',
                        type=str,
                        help='Input built-up cover fraction layer')

    # Outputs
    parser.add_argument('--od',
                        '--output-dir',
                        dest='output_dir',
                        type=str,
                        help='Output directory')

    parser.add_argument('-o',
                        '--output-file',
                        dest='output_file',
                        type=str,
                        help='Output masked DSWx layer')

    parser.add_argument('--output-rgb',
                        '--output-rgb-file',
                        dest='output_rgb_file',
                        type=str,
                        help='Output RGB file')

    parser.add_argument('--output-infrared-rgb',
                        '--output-infrared-rgb-file',
                        dest='output_infrared_rgb_file',
                        type=str,
                        help='Output infrared SWIR-1, NIR, and Red RGB'
                        '-color-composition file')

    # Parameters
    parser.add_argument('--log',
                        '--log-file',
                        dest='log_file',
                        type=str,
                        help='Log file')

    parser.add_argument('--save-intermediate-files',
                        '--save-intermediate-products',                    
                        dest='flag_save_intermediate_products',
                        action='store_true',
                        default=False,
                        help='Save intermediate DSWx-HLS products')

    parser.add_argument('--se',
                        '--skip-if-existent',
                        '--output-skip-if-existent',
                        dest='output_skip_if_existent',
                        action='store_true',
                        help='Skips pre-computed DSWx-HLS products')

    return parser


def main():
    scratch_dir = None
    parser = _get_parser()
    args = parser.parse_args()

    create_logger(args.log_file)

    files_to_mosaic_list = []
    rgb_files_to_mosaic_list = []
    infrared_rgb_files_to_mosaic_list = []

    for i, directory in enumerate(args.input_list):
        if not os.path.isdir(directory):
            continue
        print('===================================================')
        print(f'processing directory: {directory} ({i+1}/'
              f'{len(args.input_list)})')
        file_list = glob.glob(directory+'/*tif')

        # Output file name
        if not args.output_dir:
            args.output_dir = '.'
        if args.flag_save_intermediate_products:
            output_file = os.path.join(args.output_dir, directory,
                                       'dswx_hls.tif')
        else:
            output_file = tempfile.NamedTemporaryFile(
                dir=scratch_dir, suffix='.tif').name

        # RGB
        if args.output_rgb_file and args.flag_save_intermediate_products:
            output_rgb_file = os.path.join(args.output_dir, directory,
                os.path.basename(args.output_rgb_file))
        elif args.output_rgb_file:
            output_rgb_file = tempfile.NamedTemporaryFile(
                dir=scratch_dir, suffix='.tif').name
        else:
            output_rgb_file = None

        # Infrared RGB
        if args.output_infrared_rgb_file and args.flag_save_intermediate_products:
            output_infrared_rgb_file = os.path.join(args.output_dir, directory,
                os.path.basename(args.output_infrared_rgb_file))
        elif args.output_infrared_rgb_file:
            output_infrared_rgb_file = tempfile.NamedTemporaryFile(
                dir=scratch_dir, suffix='.tif').name
        else:
            output_infrared_rgb_file = None

        # Check for pre-computed files
        if (args.output_skip_if_existent and
                os.path.isfile(output_file) and
                (output_rgb_file is None or
                 os.path.isfile(output_rgb_file)) and
                (output_infrared_rgb_file is None or
                 os.path.isfile(output_infrared_rgb_file))):
            print(f'found pre-computed files. Skipping...')
            files_to_mosaic_list.append(output_file)
            if output_rgb_file:
                rgb_files_to_mosaic_list.append(output_rgb_file)
            if output_infrared_rgb_file:
                infrared_rgb_files_to_mosaic_list.append(output_infrared_rgb_file)
            continue

        if args.flag_save_intermediate_products:
            print(f'output file: {output_file}')
            if output_rgb_file:
                print(f'output RGB file: {output_rgb_file}')
            if output_infrared_rgb_file:
                print(f'output infrared RGB file: {output_infrared_rgb_file}')

        print('---------------------------------------------------')

        if generate_dswx_layers(
            file_list,
            output_file,
            output_rgb_file=output_rgb_file,
            output_infrared_rgb_file=output_infrared_rgb_file,
            dem_file=args.dem_file,
            landcover_file=args.landcover_file, 
            worldcover_file=args.worldcover_file,
            flag_offset_and_scale_inputs=False,
                scratch_dir=scratch_dir):
            files_to_mosaic_list.append(output_file)

            if args.output_rgb_file:
                rgb_files_to_mosaic_list.append(output_rgb_file)
            if args.output_infrared_rgb_file:
                infrared_rgb_files_to_mosaic_list.append(output_infrared_rgb_file)

    plant.mosaic(files_to_mosaic_list, output_file = args.output_file, 
                 no_average=True, force=True, out_null=255,
                 output_skip_if_existent = args.output_skip_if_existent,
                 interp='nearest')

    if args.output_rgb_file:
        plant.mosaic(rgb_files_to_mosaic_list,
                     output_file = args.output_rgb_file, 
                     output_skip_if_existent = args.output_skip_if_existent,
                     no_average=True, debug=True,
                     force=True, interp='average')

    if args.output_infrared_rgb_file:
        plant.mosaic(infrared_rgb_files_to_mosaic_list,
                     output_file = args.output_infrared_rgb_file, 
                     output_skip_if_existent = args.output_skip_if_existent,
                     no_average=True, debug=True,
                     force=True, interp='average')


if __name__ == '__main__':
    main()