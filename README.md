# Image Timestamper

## In one sentence

Command line Python script that 1) takes a series of images, 2) reads existing timestamp data (if any), 3) writes new DateTimeOriginal metadata based on offset values defined by user.

## Why we built this

When shooting images, it is often advantageous to use a 3rd-party GPS logger (e.g. phones because they're often more accurate at recording positioning than camera GPS chips).

Problem is, in order to join images with GPS tracks, the times in each log must match up (or be within 1 second of each other). [We use Image Geotagger to do this](https://github.com/trek-view/image-geotagger).

Oftentimes, cameras use a user defined time (e.g. time set at startup) to timestamp a `DateTimeOriginal` metadata value to the image. This is problematic when clocks move or moving between countries with different timezones where time is not updated. On phones this is less of a problem because they use remote time clock (NTP servers) to keep an accurate time.

We've also noticed some camera stitching software completely rewrites the `DateTimeOriginal` of images during stitching, replacing it with the datetime the image was stitched (which is often many days later).

Finally, other software can sometimes completely strip metadata from files (e.g ffmpeg when converting videos to frames).

Image Timestamper gives users a significant amount of flexibility to edit the timestamps of multiple images (usually timestamps) in one go.

Note: if you need to adjust GPS timestamps see [GPS Track Timestamper](https://github.com/trek-view/gps-track-timestamper).

## How it works

1. You create a series of timelapse photos or video file
2. You define how timestamps should be assigned
3. The script reads all of the photos in the directory or video file
4. The script writes new timestamps into photos as `DateTimeOriginal` values or into video as `*CreateDate`'s.

## Requirements

### OS Requirements

Works on Windows, Linux and MacOS.

### Software Requirements

* Python version 3.6+
* [Pandas](https://pandas.pydata.org/docs/): python -m pip install pandas

### Image requirements

Requirements are different by the mode.

* mode
    - manual doesn't require any thing
    - offset the `DateTimeOriginal` must required
    - inherit the `GPSDateTime` must required
    - reverse the `DateTimeOriginal` must required

## Quick start guide

```
python image-timestamper.py -m [MODE] --start_time [START_TIME] --interval [INTERVAL] --offset [OFFSET] [INPUT DIRECTORY OR VIDEO FILE] [OUTPUT DIRECTORY]
```

* mode

	- manual: must specify start `originaldatetime` (photo) or first photo `originaldatetime` and time offset for subsequent photos (timelapse). For timelapse images will be ordered and processed in ascending time order if  `originaldatetime` values exist in all images, if no `originaldatetime` values exist the script will order and process using ascending filename order.
	- offset: must specify time in seconds that should be applied to existing `DateTimeOriginal` (photo / timelapse) values
	- inherit: inherits `originaldatetime` (photo / timelapse)  from `gpsdatetime`.
	- reverse: inherits `gpsdatetime` from `originaldatetime` (photo / timelapse).
  
* --start_time
    - Require when mode is manual. e.g (2020-01-09:11:00:47:+0300)
    
* --interval
    - Interval times by set value.

* --offset
    - Offset from current set value.
    
* --exiftool-exec-path, -e
    - Optional: path to Exiftool executable in Windows.
	
## Output

The photo file(s) outputted will contain all original metadata, but with updated timestamps from script for `DateTimeOriginal` values.

## Support 

We offer community support for all our software on our Campfire forum. [Ask a question or make a suggestion here](https://campfire.trekview.org/c/support/8).

## License

Image Timestamper is licensed under a [GNU AGPLv3 License](https://github.com/trek-view/image-video-timestamper/blob/master/LICENSE.txt).