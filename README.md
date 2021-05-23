# MoticDownloader
A python script for downloading microscopic slides from Motic Gallery.

![alt text](https://github.com/laggykiller/MoticDownloader/blob/main/Demo.png?raw=true)

## Download
Pre-compiled versions are available for Windows, MacOS and Linux.
<https://github.com/laggykiller/MoticDownloader/releases/>

## Features
 - User-friendly tkinter GUI
 - CLI available for mass downloading microscopic slides
 - Download multiple microscopic slides from Motic Gallery at one go
 - Reduce bandwidth usage by not downloading white tiles
 - Auto trimming white edges
 - Rotate image
 - Free to choose zoom level (resolution of image)

## How does it work?
Motic Gallery send microscopic slides in square tiles. This program downloads and stitches the tiles together.

## CLI
MoticDownloader start in GUI mode by default. Supply any arguments to start in CLI mode.

The syntax of CLI is as below:

```
usage: MoticDownloader.py [-h] [-q] [-n] [-l LOGINPAGE] [-u USERNAME] [-p PASSWORD] [-z ZOOM]
                          [-r {0,90,180,270}] [-m {n,none,a,auto,m,manual}] [-t x1 x2 y1 y2]
                          [target_urls ...]

Download slides from MoticGallery. Supply any arguments to start in CLI mode instead of GUI mode.

positional arguments:
  target_urls           URL of slide to download

optional arguments:
  -h, --help            show this help message and exit
  -q, --quiet           Do not show any message
  -n, --dryrun          Show slide metadata only
  -l LOGINPAGE, --loginpage LOGINPAGE
                        Specify login page URL for login
  -u USERNAME, --username USERNAME
                        Set username for login
  -p PASSWORD, --password PASSWORD
                        Set password for login
  -z ZOOM, --zoom ZOOM  Set zoom level (0-13)
  -r {0,90,180,270}, --rotation {0,90,180,270}
                        Set counterclockwise rotation (0 | 90 | 180 | 270)
  -m {n,none,a,auto,m,manual}, --trim_mode {n,none,a,auto,m,manual}
                        Set trim mode ([n]one | [a]uto | [m]anual)
  -t x1 x2 y1 y2, --trim x1 x2 y1 y2
                        Set trim range on full image (x1, x2, y1, y2)
```

Note that if you do not give an argument, values from config.ini or default values would be used.

Example 1:

```
MoticDownloader.py -u simon -p password -z 3 -r 90 -m a http://www.example.com/MoticGallery/Slides/F2CA1BB6-06DA-4715-7E57-22DA52E6CCC2
```

This downloads slide at zoom level 3, rotation 90 degrees counterclockwise and auto trim.

Example 2:

```
MoticDownloader.py -z 5 -t 20 60 30 50 http://www.example.com/MoticGallery/Slides/F2CA1BB6-06DA-4715-7E57-22DA52E6CCC2 http://www.example.com/MoticGallery/Slides/D21BB4FC-DF08-2D5D-E846-7163AF34D082
```

This downloads 2 slides at zoom level 5 and manual trim from (20, 30) to (60, 50). Username, password and zoom level from config.ini would be used if available.

## FAQ
### Program crashed when downloading high resolution image
You probably ran out of RAM. Try to download without trimming, as trimming requires more RAM.

If it still fails, try to download with higher zoom level (lower resolution).

### Is this program safe?
Yes it is. You may check the source code.

If you do not trust the pre-compiled binaries, you may download and run the py file directly or compile it yourself.

Note that the windows program maybe marked suspicious by Windows SmartScreen, as the program is not code signed with certificate.

Some antivirus may detect it as a virus, as this program needs to collect your username and password and send it to Motic Gallery server.

Note that the windows msi installer is built with Advanced Installer, a non-opensource program. If you do not trust it, use exe or py file instead.

### I found a bug!
Submit a bug report to 'Issues'. Make sure you include the error message.

### Can you add XXX/YYY features?
Submit a request to 'Issues'. Also, feel free to submit pull requests.

### How to compile?
Install python and pip, then install libraries used by MoticDownloader with `pip install mechanize beautifulsoup4 lxml Pillow tqdm`

Finally, depending on OS, run one of the following command to compile:

Windows:
```
pip3 install pyinstaller
pyinstaller -n MoticDownloader-Windows --clean --onefile --icon=icon/app.ico --windowed --add-data icon/*;icon MoticDownloader.py
```

MacOS:
```
python3 -m pip install py2app
python3 setup-mac.py py2app
```
(Note: For MacOS, using pyinstaller to compile with --windowed option cause the app to crash on launch)

Linux:
```
pip3 install pyinstaller
pyinstaller -n MoticDownloader-Linux --clean --onefile --windowed --add-data icon/*:icon MoticDownloader.py
```

### Compiling on MacOS gives an app with buggy GUI
You might had installed python3 via homebrew.

Uninstall python3 and reinstall python3 using pkg supplied by python.org

### Compiling on linux failed with `pyinstaller 'NoneType' object has no attribute 'groups'`
Use the patch provided here: https://github.com/pyinstaller/pyinstaller/issues/5540#issuecomment-776995969

## Libraries used
Libraries below are required if you want to run the py file directly or compile it yourself. Install them with pip.
 - mechanize
 - beautifulsoup4
 - lxml
 - Pillow
 - tqdm

## Icon source
App icon is from [Remix Icon](https://remixicon.com/)
