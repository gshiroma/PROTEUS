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
import argparse
import datetime
import shutil


def _get_parser():
    parser = argparse.ArgumentParser(description='',
                                          formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Inputs
    parser.add_argument('input_list',
                        type=str,
                        nargs='+',
                        help='Input YAML run configuration file or HLS product file(s)')

    return parser


def main():
    parser = _get_parser()
    args = parser.parse_args()
    dir_list = []
    dir_dict = {}
    for f in args.input_list:
        tile = f.split('.')[2]
        date = f.split('.')[3].split('T')[0]
        year = date[:4]
        day_of_the_year = date[4:]
        user_datetime = datetime.datetime.strptime(f'{year} {day_of_the_year}',
                                                   '%Y %j')
        day = user_datetime.day
        month = user_datetime.month
        # print(f'tile: {tile}')
        # print(f'date: {date}')
        # print(f'day of the year: {day_of_the_year}')
        # print(f'day: {day}')
        # print(f'month: {month}')
        date_str = f'{year}-{month:02}-{day:02}'
        dir_str = f'{date_str}/{tile}'
        # print(dir_str)
        if dir_str not in dir_list:
            dir_list.append(dir_str)
            if date_str not in dir_dict.keys():
                dir_dict[date_str] = []
            dir_dict[date_str].append(tile)
        # if not os.path.isdir(date_str):
        #     os.makedirs(date_str)
        if not os.path.isdir(dir_str):
            os.makedirs(dir_str)
        shutil.move(f, dir_str)
    # print(dir_list)
    # print(dir_dict)
    for k, v in dir_dict.items():
        print(k, len(v), v)



if __name__ == '__main__':
    main()
