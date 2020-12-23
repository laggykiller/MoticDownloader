# MoticDownloader
A python script for downloading images from Motic Gallery.

![alt text](https://github.com/laggykiller/MoticDownloader/blob/main/Demo.png?raw=true)

## Download
Pre-compiled versions are available for Windows, MacOS and Linux.
<https://github.com/laggykiller/MoticDownloader/releases/>

## Features
 - User-friendly tkinter GUI
 - Download multiple images from Motic Gallery at one go
 - Reduce bandwidth usage by not downloading white tiles
 - Auto trimming white edges
 - Rotate images
 - Free to choose zoom level (resolution of image)

## How does it work?
Motic Gallery send images in square tiles. This program downloads and stitches the tiles together.

## FAQ
### Program crashed when downloading high resolution image
You probably ran out of RAM. Try to download without trimming, as trimming requires more RAM.

If it still fails, try to download with higher zoom level (lower resolution).

### Is this program safe?
Yes it is. You may check the source code.

If you do not trust the pre-compiled binaries, you may download and run the py file directly or compile it yourself.

Note that the windows program maybe marked suspicious by Windows SmartScreen, as the program is not code signed with certificate.

Some antivirus may detect it as a virus, as this program needs to collect your username and password and send it to Motic Gallery server.

### I found a bug!
Submit a bug report to 'Issues'. Make sure you include the error message.

### Can you add XXX/YYY features?
Submit a request to 'Issues'. Also, feel free to submit pull requests.

## Libraries used
Libraries below are required if you want to run the py file directly or compile it yourself. Install them with pip.
 - mechanize
 - beautifulsoup4
 - lxml
 - Pillow
