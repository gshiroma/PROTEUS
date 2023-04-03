#!/usr/bin/env python3
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# Compute Dynamic Surface Water Extent (DSWx)
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
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import argparse
from osgeo import gdal
from dswx_hls import save_mask
import numpy as np


def _get_parser():
    parser = argparse.ArgumentParser(description='',
                                          formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Inputs
    parser.add_argument('input_file',
                        type=str,
                        nargs=1,
                        help='Input images')

    # Outputs
    parser.add_argument('-o',
                        '--output-file',
                        dest='output_file',
                        type=str,
                        required=True,
                        default='output_file',
                        help='Output file')

    # Parameters
    parser.add_argument('-b',
                        '--byte-value',
                        required=True,
                        type=int,
                        dest='byte_value',
                        help='Byte value.'
                        ' Examples: cloud: 10; adjacent: 100; cloud-shadow: 1000;'
                        ' snow: 10000; snow and adjacent: 10100.')

    parser.add_argument('--logic',
                        type=str,
                        default='contains',
                        choices=['contains', 'equal'],
                        dest='logic',
                        help='Logic: "contains" (default) or "equal"')

    return parser

def binary_to_decimal(binary): 
    decimal, i = 0, 0
    while(binary != 0):
        dec = binary % 10
        decimal = decimal + dec * pow(2, i)
        binary = binary//10
        i += 1
    print(decimal)
    return decimal


def main():
    parser = _get_parser()
    args = parser.parse_args()

    print(f'input file: {args.input_file[0]}')
    print(f'byte value: {args.byte_value}')
    print(f'logic: {args.logic}')
    decimal_from_byte_value = binary_to_decimal(args.byte_value)
    print(f'byte value (decimal): {decimal_from_byte_value}')
 
    layer_gdal_dataset = gdal.Open(args.input_file[0])
    geotransform = layer_gdal_dataset.GetGeoTransform()
    projection = layer_gdal_dataset.GetProjection()
    image = layer_gdal_dataset.ReadAsArray()

    if args.logic == 'contains':
        output_array = np.bitwise_and(image, decimal_from_byte_value) == \
            decimal_from_byte_value
    else:
        output_array = image == args.byte_value

    dswx_metadata_dict = {}
    description = f'FMask {args.logic} 0b{args.byte_value} ({decimal_from_byte_value})'
    print(f'description: {description}')
    output_file_list = []
    save_mask(output_array, args.output_file, dswx_metadata_dict, geotransform,
              projection, description, output_file_list)
    print(f'file saved: {args.output_file}')



if __name__ == '__main__':
    main()