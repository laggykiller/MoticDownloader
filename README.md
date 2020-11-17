# MoticDownloader
A python script for downloading images from Motic Gallery.

## How does it work?
Motic Gallery send images in square tiles. This program downloads and stitches the tiles together.

## How to use?
0. Install python: <https://www.python.org/downloads/>
1. Download from 'Releases'.
2. **Fill in the domain of MoticGallery and your login credentials in settings.txt**
3. Launch MoticDownloader.
  a. Windows: Use 'launch.bat'
  b. MacOS / Linux: Use 'launch.sh'
4. Enter URL of image(s). If you want to download more than one image, separate URLs with semicolon (;).
5. Enter zoom level (Range: 0-13). **Using low zoom level gives higher resolution, but takes more space.**
6. Select trim mode.
  a. Rough trim: Aavoid downloading tiles that is blank, hence reduce download time.
  b. Fine trim: Trimming away white space after downloading tiles, hence save space.
  c. Custom trim: Specify the range of tiles to download.
  d. Full image: Download all tiles.
7. Program will automagically download image(s).

(Tip: Default values will be used if nothing is entered.)

## FAQ
### Is this program safe?
Yes it is. You may check the source code.

However, the developer is not responsible for any bans resulted from using this program. Use at your own risk.

_(Side note: Be considerate, try to avoid downloading too many images at once, as well as avoiding to download at low zoom level)_

### Program crashed when downloading high resolution image
You probably ran out of RAM. Try to download with option '\[1] Rough trim only', as fine trim requires more RAM.

If it still fails, try to download with higher zoom level.

### I found a bug!
Submit a bug report to 'Issues'. Make sure you include the error message.

## Can you add XXX/YYY features?
Submit a request to 'Issues'. Also, feel free to submit pull requests.

## Libraries used
 - mechanize
 - beautifulsoup4
 - tqdm
