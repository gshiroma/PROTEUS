#!/usr/bin/env python3
import argparse
from osgeo import gdal
from proteus.dswx_hls import (
    band_description_dict,
    save_cloud_layer,
    save_dswx_product,
    save_array,
    get_diagnostic_layer_ctable)


def _get_parser():
    parser = argparse.ArgumentParser(
        description='Append color table to DSWx-HLS products or Q/A masks',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Inputs
    parser.add_argument('input_file',
                        type=str,
                        nargs=1,
                        help='Input DSWx-HLS product, DSWx-HLS layer, or Q/A mask')

    # Outputs
    parser.add_argument('-o',
                        '--output-file',
                        dest='output_file',
                        type=str,
                        required=True,
                        default='output_file',
                        help='Output GeoTIFF file with appended color table')

    # Parameters
    parser_dataset = parser.add_mutually_exclusive_group()
    parser_dataset.add_argument('--diag'
                                '--diag-layer',
                                action='store_true',
                                dest='diag_layer',
                                help='Append color table to cloud/cloud-shadow mask')
    parser_dataset.add_argument('--cloud'
                                '--cloud-mask',
                                action='store_true',
                                dest='cloud_layer',
                                help='Append color table to cloud/cloud-shadow mask')

    parser_dataset.add_argument('--wtr',
                                '--interpreted-band',
                                action='store_true',
                                dest='interpreted_dswx',
                                help='Append color table to interpreted DSWx layer')

    parser.add_argument('--wtr-1',
                        '--non-masked-dswx',
                        action='store_true',
                        dest='non_masked_dswx',
                        help='Append color table to non-masked DSWx layer file')

    parser.add_argument('--wtr-2',
                        '--shadow-masked-dswx',
                        action='store_true',
                        dest='shadow_masked_dswx',
                        help='Append color table to interpreted layer refined using'
                        ' land cover and terrain shadow testing ')

    return parser


def main():
    parser = _get_parser()

    args = parser.parse_args()

    layer_gdal_dataset = gdal.Open(args.input_file[0], gdal.GA_ReadOnly)
    geotransform = layer_gdal_dataset.GetGeoTransform()
    projection = layer_gdal_dataset.GetProjection()
    if layer_gdal_dataset.RasterCount > 1:

        band_description_keys_list = list(band_description_dict.keys())
        if args.non_masked_dswx:
            layer_name = 'WTR-1'
        elif args.shadow_masked_dswx:
            layer_name = 'WTR-2'
        elif args.cloud_layer:
            layer_name = 'CLOUD'
        elif args.diag_layer:
            layer_name = 'DIAG'
        else:
            layer_name = 'WTR'

        band = band_description_keys_list.index(layer_name) + 1
        print(f'Loading DSWx-HLS product (band: {band})')
        band = layer_gdal_dataset.GetRasterBand(band)
        image = band.ReadAsArray()
    else:
        image = layer_gdal_dataset.ReadAsArray()

    metadata_dict = {}
    if args.diag_layer:
        print('Appending color table to the DIAG layer')
        layer_name = 'DIAG'
        diag_ctable = get_diagnostic_layer_ctable(image)
        description = 'Diagnostic layer (DIAG)'
        save_array(image, args.output_file, metadata_dict, geotransform,
                   projection, output_dtype=gdal.GDT_UInt16,
                   description=description,
                   ctable=diag_ctable)

    elif args.cloud_mask:
        print('Appending color table to CLOUD layer')
        layer_name = 'CLOUD'
        save_cloud_layer(image, layer_name, args.output_file, metadata_dict,
                        geotransform, projection)
    else:
        print('Appending color table to interpreted DSWx layer')
        save_dswx_product(image, layer_name, args.output_file, metadata_dict,
                          geotransform, projection)


if __name__ == '__main__':
    main()