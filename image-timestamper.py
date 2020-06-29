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
from pathlib import Path
import datetime
import shutil

import pandas as pd
from exiftool_custom import exiftool


def get_files(path):
    """
    Return a list of files, or directories.
    """
    list_of_files = []

    for p, r, files in os.walk(path):
        for file in files:
            list_of_files.append(os.path.join(p, file))

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
        data = dict_metadata[key]
        values.append(data)
    return values


def update_metadata_manual(df_images, start_time, interval):
    """
    Update Images OriginalDateTime or CreateDate from state_time and interval
    """
    sort_key = 'ORIGINAL_DATETIME'

    try:
        keys = ['EXIF:DateTimeOriginal']
        df_images['ORIGINAL_DATETIME'] = df_images.apply(
            lambda x: parse_metadata(x, keys), axis=1, result_type='expand')
    except:
        print('Can not sort the files by DateTimeOriginal. Now sorting by file name')
        sort_key = 'IMAGE_NAME'

    df_images.sort_values(sort_key, axis=0, ascending=True, inplace=True)

    if start_time:
        start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d:%H:%M:%S")
    else:
        for idx, row in df_images.iterrows():
            try:
                start_time = datetime.datetime.strptime(row['METADATA']['EXIF:DateTimeOriginal'], "%Y:%m:%d %H:%M:%S") \
                             - datetime.timedelta(0, idx * interval)
                print('Start time is not set, so now setting by {}th file({})\'s DateTimeOriginal'.format(
                    idx, row['IMAGE_NAME']))
                break
            except:
                continue

    if not start_time:
        print("""Start time can not be set by DateTimeOriginal of files. Now setting by current time.""")
        start_time = now

    df_images['ORIGINAL_DATETIME'] = df_images.apply(
            lambda x: start_time + datetime.timedelta(0, int(x.name) * interval), axis=1, result_type='expand')

    return df_images


def update_metadata_offset(df_images, offset):
    """
    Update Images OriginalDateTime or CreateDate add offset from existing value
    """

    try:
        df_images['ORIGINAL_DATETIME'] = df_images.apply(
            lambda x: datetime.datetime.strptime(x['METADATA']['EXIF:DateTimeOriginal'], "%Y:%m:%d %H:%M:%S") \
                + datetime.timedelta(0, offset),
            axis=1,
            result_type='expand')
    except:
        input("""OriginalDateTime of some files are not set.\n\nPress any key to quit...""")
        quit()

    return df_images


def update_metadata_inherit(df_images):
    """
    Update Images OriginalDateTime or CreateDate from GPS DateTime
    """

    try:
        df_images['ORIGINAL_DATETIME'] = df_images.apply(
            lambda x: datetime.datetime.strptime(x['METADATA']['Composite:GPSDateTime'], "%Y:%m:%d %H:%M:%SZ"), axis=1, result_type='expand')
    except:
        input("""GPSDateTime of some files are not set.\n\nPress any key to quit...""")
        quit()

    return df_images


def update_metadata_reverse(df_images):
    """
    Update Images GPS DateTime from OriginalDateTime or CreateDate
    """
    df_images['GPS_DATETIME'] = df_images.apply(
        lambda x: datetime.datetime.strptime(x['METADATA']['EXIF:DateTimeOriginal'], "%Y:%m:%d %H:%M:%S"), axis=1, result_type='expand')

    return df_images


def copy_files(input_path, output_path):
    print('Moving files to destination: {}'.format(output_path))
    if os.path.isdir(os.path.abspath(output_path)):
        shutil.rmtree(output_path)

    try:
        shutil.copytree(input_path, output_path)
        # Directories are the same
    except shutil.Error as e:
        print('Directory not copied. Error: %s' % e)
        # Any error saying that the directory doesn't exist
    except OSError as e:
        print('Directory not copied. Error: %s' % e)


def image_time_stamper(args):
    path = Path(__file__)
    input_photo_directory = os.path.abspath(args.input_path)
    output_photo_directory = os.path.abspath(args.output_directory)
    mode = args.mode.lower()

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

    # Validate input mode
    if mode not in ['manual', 'offset', 'inherit', 'reverse']:
        input("""Mode should be one of "manual", "offset", "inherit", "reverse".\n\nPress any key to quit...""")
        quit()

    copy_files(input_photo_directory, output_photo_directory)

    # Get files in directory
    list_of_files = get_files(output_photo_directory)
    print('{0} file(s) have been found in input directory'.format(len(list_of_files)))

    # Get metadata of each file in list_of_images
    print('Fetching metadata from all images....\n')
    with exiftool.ExifTool(win_shell=is_win_shell) as et:
        list_of_metadata = [{'IMAGE_NAME': image, 'METADATA': et.get_metadata(image)} for image in list_of_files]

    # Create dataframe from list_of_metadata with image name in column and metadata in other column
    df_images = pd.DataFrame(list_of_metadata)

    if mode == 'manual':
        start_time = args.start_time
        interval = int(args.interval)
        df_images = update_metadata_manual(df_images, start_time, interval)

    elif mode == 'offset':
        offset = int(args.offset)
        df_images = update_metadata_offset(df_images, offset)

    elif mode == 'inherit':
        df_images = update_metadata_inherit(df_images)

    else:
        df_images = update_metadata_reverse(df_images)

    # For each image, write the DateTimeOriginal into EXIF
    print('Writing metadata to EXIF of qualified images...\n')
    if mode != 'reverse':
        with exiftool.ExifTool(win_shell=is_win_shell) as et:
            for row in df_images.iterrows():
                et.execute(
                    bytes('-DateTimeOriginal={0}'.format(row[1]['ORIGINAL_DATETIME'].strftime("%Y:%m:%d %H:%M:%S")),
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
                        default=None,
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

    input_args = parser.parse_args()

    image_time_stamper(input_args)
