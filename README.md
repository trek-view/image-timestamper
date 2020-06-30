# Image Timestamper

## In one sentence

Command line Python script that 1) takes a photo, series of images (timelapse) or video, 2) reads existing time data (if any), and 3) writes new time data based on offset values defined by user.

## Why we built this

When shooting images, it is often advantageous to use a 3rd-party GPS logger (e.g. phones because they're often more accurate at recording positioning than camera GPS chips).

Problem is, in order to join images with GPS tracks, the times in each log must match up (or be within 1 second of each other). ([We use Image Geotagger to do this](https://github.com/trek-view/image-geotagger)).

Oftentimes, cameras use the default camera time (time set by user on camera) to assign a timestamp a `DateTimeOriginal` metadata value to the image.

This is problematic when clocks move or moving between countries with different timezones where time is not updated. On phones this is less of a problem because they use remote time clock (NTP servers) to keep an accurate time.

We've also noticed some camera stitching software completely rewrites the `DateTimeOriginal` of images during stitching, replacing it with the datetime the image was stitched (which is often many days later).

Finally, other software can sometimes completely strip metadata from files (e.g ffmpeg when converting videos to frames).

Image Timestamper gives users a significant amount of flexibility to edit the timestamps of multiple images (usually timestamps) in one go using the command line.

The script works with .mp4 video files too. In the case of video files all `*CreateDate`'s (e.g. MediaCreateDate, TrackCreateDate, etc,) are modified instead (as oppose to `DateTimeOriginal` for image files)

_Note: if you need to adjust GPS log timestamps see [GPS Track Timestamper](https://github.com/trek-view/gps-track-timestamper)._

## How it works

1. You specify a photo file, series of timelapse photo files, or video file
2. You define how timestamps should be assigned
3. The script reads all of the photos in the directory or video file
4. The script writes new timestamps into photos as `DateTimeOriginal` values or into video as `*CreateDate`'s.

## Requirements

### OS Requirements

Works on Windows, Linux and MacOS.

### Software Requirements

* Python version 3.6+
* [Pandas](https://pandas.pydata.org/docs/): python -m pip install pandas
* [Exiftool](https://exiftool.org/)

### Image / video metadata requirements

Requirements are different by the mode.

* manual: 
* offset:
* inherit: 
* reverse: 

## Usage

```
python image-timestamper.py -m [MODE] [INPUT DIRECTORY OR VIDEO FILE] [OUTPUT DIRECTORY]
```

* mode (`-m`)
	- `manual`: doesn't require any existing data (**video / timelapse / photo**). For single photo and video you must specify start `DateTimeOriginal` using `--start_time` in `YYYY-MM-DD:HH:MM:SS` format. For timestamp must supply `--start_time` and the time offset for subsequent photos using `--interval` in seconds. Timelapse images in the directory specified will be ordered and processed in ascending time order (1-9) if  `DateTimeOriginal` values exist in all images, if no `DateTimeOriginal` values exist the script will order and process using ascending filename order (A-Z).
	- `offset`: requires `DateTimeOriginal` (**timelapse / photo**) OR `CreateDate` (**video**) value. Must specify time `--offset` in seconds that should be applied to existing `DateTimeOriginal` (timelapse / photo) or `*CreateDate` values
    - `inherit`: requires `GPSDateTime` value (**video / timelapse / photo**). Inherits `DateTimeOriginal` (photo / timelapse) or `*CreateDate` values (video) from `GPSDateTime`. For video files, the first reported `GPSDateTime` is used.
	- `reverse`: requires `DateTimeOriginal` (**timelapse / photo**). Inherits `GPSDateTime` from `DateTimeOriginal`. Note, this does not work with video where multiple `GPSDateTime` are required. WARNING: `GPSDateTime` is a much more accurate value for time, as this is reported from GPS atomic clocks. It is very unlikely you want to use this mode, unless your intention is to spoof the image time.
  
**Note for Windows users**

It is recommended you place `exiftool.exe` in the script directory. To do this, [download exiftool](https://exiftool.org/), extract the `.zip` file, and place `exiftool(-k).exe` in script directory.

If you want to run an existing exiftool install from outside the directory you can also add the path to the exiftool executable on the machine using either `--exiftool-exec-path` or `-e`.
	
## Output

The photo file(s) outputted in specified directory will contain all original metadata, but with updated timestamps from script for `DateTimeOriginal` or `*CreateDate` values.

## Quick start 

**Note for Windows user**

Add double quotes (`"`) around any directory path shown in the examples. For example `OUTPUT_1` becomes `"OUTPUT_1"`.

### Take a directory of images (`INPUT`) and add 10 seconds onto each files reported `DateTimeOriginal` value then output (to directory `OUTPUT_1`)

```
python image-timestamper.py -m manual --start_time 2020-01-01:00:00:01 --interval 10 "INPUT" "OUTPUT_1"
```

### Take a single photo (`INPUT/MULTISHOT_0611_000000.jpg`) and add 5 minutes onto `DateTimeOriginal` value then output (to directory `OUTPUT_2`)

```
python image-timestamper.py -m offset --offset 300 "INPUT/MULTISHOT_0611_000000.jpg" "OUTPUT_2"
```

### Take a video file (`INPUT/VIDEO_7152.mp4`) and inherit all `*CreateDate` values from the first reported `GPSDateTime` in the telemetry track then output (to directory `OUTPUT_3`)

```
python image-timestamper.py -m inherit "INPUT/VIDEO_7152.mp4" "OUTPUT_3"
```

### Take a directory of images (`INPUT`) and make each images `GPSDateTime` match the value reported for its `DateTimeOriginal` then output (to directory `OUTPUT_4`)

```
python image-timestamper.py -m inherit "INPUT" "OUTPUT_4"
```

## Support 

We offer community support for all our software on our Campfire forum. [Ask a question or make a suggestion here](https://campfire.trekview.org/c/support/8).

## License

Image Timestamper is licensed under a [GNU AGPLv3 License](https://github.com/trek-view/image-video-timestamper/blob/master/LICENSE.txt).