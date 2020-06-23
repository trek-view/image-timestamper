# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Author: hq@trekview.org
# Created: 2020-06-15
# Copyright: Trek View
# Licence: GNU AGPLv3
# -------------------------------------------------------------------------------
import os
import argparse
import sys
import math
from pathlib import Path
from xml.etree import ElementTree
import xml.sax
import csv
import datetime
import ntpath
import time

import pandas as pd
import gpxpy
from exiftool_custom import exiftool


def get_files(path, isdir):
    """
    Return a list of files, or directories.
    """
    list_of_files = []

    for item in os.listdir(path):
        item_path = os.path.abspath(os.path.join(path, item))

        if isdir:
            if os.path.isdir(item_path):
                list_of_files.append(item_path)
        else:
            if os.path.isfile(item_path):
                list_of_files.append(item_path)

    return list_of_files


def filter_metadata(metadata, keys):
    """
    If metadata contains certain key values then return false
    """
    dict_metadata = metadata['METADATA']
    for key in keys:
        if dict_metadata[key]:
            return False
    return True


def parse_metadata(dfrow, keys):
    """
    get values in a metadata object
    """
    dict_metadata = dfrow['METADATA']
    values = []
    for key in keys:
        try:
            data = dict_metadata[key]
            values.append(data)
        except KeyError:
            print('\n\nAn image was encountered that did not have the required metadata.')
            print('Image: {0}'.format(dfrow['IMAGE_NAME']))
            print('Missing metadata key: {0}\n\n'.format(key.split(':')[-1]))
            input('Press any key to quit')
            quit()
    return values


def update_metadata_manual(df_images, start_time, interval):
    """
    Update Images OriginalDateTime or CreateDate from state_time and interval
    """
    start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d:%H:%M:%S:%z")
    i = 0

    df_images[['ORIGINAL_DATETIME', 'CREATE_DATE']] = df_images.apply(
            lambda x: [start_time, start_time], axis=1, result_type='expand')

    for i in range(len(df_images)):
        df_images.iat[i, df_images.columns.get_loc('ORIGINAL_DATETIME')] += datetime.timedelta(0, i * interval)
        df_images.iat[i, df_images.columns.get_loc('CREATE_DATE')] += datetime.timedelta(0, i * interval)

    return df_images


def update_metadata_offset(df_images, offset):
    """
    Update Images OriginalDateTime or CreateDate add offset from existing value
    """
    keys = ['EXIF:DateTimeOriginal', 'EXIF:CreateDate']
    df_images[['ORIGINAL_DATETIME', 'CREATE_DATE']] = df_images.apply(
        lambda x: parse_metadata(x, keys), axis=1, result_type='expand')

    df_images['ORIGINAL_DATETIME'] = df_images.\
        apply(lambda x: datetime.datetime.strptime(x['ORIGINAL_DATETIME'] + datetime.timedelta(0, offset)), axis=1)
    df_images['CREATE_DATE'] = df_images. \
        apply(lambda x: datetime.datetime.strptime(x['CREATE_DATE'] + datetime.timedelta(0, offset)), axis=1)

    return df_images


def update_metadata_inherit(df_images):
    """
    Update Images OriginalDateTime or CreateDate from GPS DateTime
    """
    keys = ['Composite:GPSDateTime', 'Composite:GPSDateTime']
    df_images[['ORIGINAL_DATETIME', 'CREATE_DATE']] = df_images.apply(
        lambda x: parse_metadata(x, keys), axis=1, result_type='expand')

    return df_images


def update_metadata_reverse(df_images):
    """
    Update Images GPS DateTime from OriginalDateTime or CreateDate
    """
    keys = ['EXIF:DateTimeOriginal']
    df_images[['GPS_DATETIME']] = df_images.apply(
        lambda x: parse_metadata(x, keys), axis=1, result_type='expand')

    return df_images


def clean_up_new_files(output_photo_directory, list_of_files):
    """
    As Exiftool creates a copy of the original image when processing,
    the new files are copied to the output directory,
    original files are renamed to original filename.
    """

    print('Cleaning up old and new files...')
    if not os.path.isdir(os.path.abspath(output_photo_directory)):
        os.mkdir(os.path.abspath(output_photo_directory))

    for image in list_of_files:
        image_head, image_name = ntpath.split(image)
        try:
            os.rename(image, os.path.join(os.path.abspath(output_photo_directory),
                                          '{0}_calculated.{1}'.format(image_name.split('.')[0], image.split('.')[-1])))
            os.rename(os.path.join(os.path.abspath(image_head), '{0}_original'.format(image_name)), image)
        except PermissionError:
            print("Image {0} is still in use by Exiftool's process or being moved'."
                  " Waiting before moving it...".format(image_name))
            time.sleep(3)
            os.rename(image, os.path.join(os.path.abspath(output_photo_directory),
                                          '{0}_calculated.{1}'.format(image_name.split('.')[0], image.split('.')[-1])))
            os.rename(os.path.join(os.path.abspath(image_head), '{0}_original'.format(image_name)), image)

    print('Output files saved to {0}'.format(os.path.abspath(output_photo_directory)))


def image_time_stamper(args):
    path = Path(__file__)
    input_photo_directory = os.path.abspath(args.input_path)
    output_photo_directory = os.path.abspath(args.output_directory)
    mode = args.mode
    start_time = args.start_time
    interval = int(args.interval)
    offset = int(args.offset)

    is_win_shell = True

    # Validate input paths
    if not os.path.isdir(input_photo_directory):
        if os.path.isdir(os.path.join(path.parent.resolve(), input_photo_directory)):
            input_photo_directory = os.path.join(path.parent.resolve(), input_photo_directory)
            if not os.path.isdir(output_photo_directory):
                output_photo_directory = os.path.join(path.parent.resolve(), output_photo_directory)
        else:
            input('No valid input folder is given!\nInput folder {0} or {1} does not exist!'.format(
                os.path.abspath(input_photo_directory),
                os.path.abspath(os.path.join(path.parent.resolve(), input_photo_directory))))
            input('Press any key to continue')
            quit()

    print('The following input folder will be used:\n{0}'.format(input_photo_directory))
    print('The following output folder will be used:\n{0}'.format(output_photo_directory))

    # Often the exiftool.exe will not be in Windows's PATH
    if args.executable_path == 'No path specified':
        if 'win' in sys.platform and not 'darwin' in sys.platform:
            if os.path.isfile(os.path.join(path.parent.resolve(), 'exiftool.exe')):
                exiftool.executable = os.path.join(path.parent.resolve(), 'exiftool.exe')
            else:
                input("""Executing this script on Windows requires either the "-e" option
                        or store the exiftool.exe file in the working directory.\n\nPress any key to quit...""")
                quit()
        else:
            is_win_shell = False

    else:
        exiftool.executable = args.executable_path

    # Get files in directory
    list_of_files = get_files(input_photo_directory, False)
    print('{0} file(s) have been found in input directory'.format(len(list_of_files)))

    # Get metadata of each file in list_of_images
    print('Fetching metadata from all images....\n')
    with exiftool.ExifTool(win_shell=is_win_shell) as et:
        list_of_metadata = [{'IMAGE_NAME': image, 'METADATA': et.get_metadata(image)} for image in list_of_files]

    # Create dataframe from list_of_metadata with image name in column and metadata in other column
    df_images = pd.DataFrame(list_of_metadata)

    if mode == 'manual':
        df_images = update_metadata_manual(df_images, start_time, interval)

    if mode == 'offset':
        df_images = update_metadata_offset(df_images, offset)

    if mode == 'inherit':
        df_images = update_metadata_inherit(df_images)

    if mode == 'reverse':
        df_images = update_metadata_reverse(df_images)

    # For each image, write the DateTimeOriginal into EXIF
    print('Writing metadata to EXIF of qualified images...\n')
    if mode is not 'reverse':
        with exiftool.ExifTool(win_shell=is_win_shell) as et:
            for row in df_images.iterrows():
                et.execute(
                    bytes('-DateTimeOriginal={0}'.format(row[1]['ORIGINAL_DATETIME'].strftime("%Y:%m:%d %H:%M:%S")),
                          'utf-8'),
                    bytes("{0}".format(row[1]['IMAGE_NAME']), 'utf-8'))

                et.execute(
                    bytes('-CreateDate={0}'.format(row[1]['CREATE_DATE  '].strftime("%Y:%m:%d")),
                          'utf-8'),
                    bytes("{0}".format(row[1]['IMAGE_NAME']), 'utf-8'))

    else:
        with exiftool.ExifTool(win_shell=is_win_shell) as et:
            for row in df_images.iterrows():
                et.execute(
                    bytes('-GPSTimeStamp={0}'.format(row[1]['GPS_DATETIME'].strftime("%H:%M:%S")),
                          'utf-8'),
                    bytes("{0}".format(row[1]['IMAGE_NAME']), 'utf-8'))
                et.execute(
                    bytes('-GPSDateStamp={0}'.format(row[1]['GPS_DATETIME'].strftime("%Y:%m:%d")),
                          'utf-8'),
                    bytes("{0}".format(row[1]['IMAGE_NAME']), 'utf-8'))

    clean_up_new_files(output_photo_directory, [image for image in df_images['IMAGE_NAME'].values])

    input('\nMetadata successfully added to images.\n\nPress any key to quit')
    quit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Image TimeStamper')

    now = datetime.datetime.now()

    parser.add_argument('-m', '--mode',
                        action='store',
                        default='missing',
                        dest='mode',
                        help='Image TimeStamper Mode. Available modes are "manual", "offset", "inherit" and "reverse"')

    parser.add_argument('--start_time',
                        action='store',
                        default=now.strftime("%Y-%m-%d, %H:%M:%S"),
                        dest='start_time',
                        help='Image TimeStamper StartTime. When mode is "manual" this argument is required.')

    parser.add_argument('--interval',
                        action='store',
                        default=0,
                        dest='interval',
                        help='Image TimeStamper interval value. When mode is "manual" this argument is required.')

    parser.add_argument('--offset',
                        action='store',
                        default=0,
                        dest='offset',
                        help='Image TimeStamper offset value. When mode is "offset" this argument is required.')

    parser.add_argument('-e', '--exiftool-exec-path',
                        action='store',
                        default='No path specified',
                        dest='executable_path',
                        help='Optional: path to Exiftool executable.')

    parser.add_argument('input_path',
                        action='store',
                        help='Path to input video or directory of images.')

    parser.add_argument('output_directory',
                        action="store",
                        help='Path to output folder.')

    parser.add_argument('--version',
                        action='version',
                        version='%(prog)s 1.0')

    args = parser.parse_args()

    image_time_stamper(args)