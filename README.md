# MoticDownloader
A python script for downloading images from Motic Gallery.

## Download
Pre-compiled versions are available for Windows, MacOS and Linux.
<https://github.com/laggykiller/MoticDownloader/releases/>

## How does it work?
Motic Gallery send images in square tiles. This program downloads and stitches the tiles together.

## FAQ
### Program crashed when downloading high resolution image
You probably ran out of RAM. Try to download with option '\[1] Rough trim only', as fine trim requires more RAM.

If it still fails, try to download with higher zoom level.

### Is this program safe?
Yes it is. You may check the source code.

The application maybe marked suspicious by Windows SmartScreen, as it is not signed.

If you do not trust the pre-compiled binaries, you may download and run the py file directly or compile it yourself.

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
