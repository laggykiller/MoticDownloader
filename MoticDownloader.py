#!/bin/python3
from threading import Thread
from os import path
from time import sleep
from sys import exit
import mechanize
from urllib import request
from bs4 import BeautifulSoup
import http.cookiejar as cookielib
from PIL import Image, ImageDraw, ImageChops
from tqdm import tqdm
from io import BytesIO
from math import ceil
import warnings

# Default settings
thread_amount = 2

def GetInfo(target_slide):
    global br
    # Get slide information
    br.open(target_slide)
    raw = br.response().read()
    soup = str(BeautifulSoup(raw, features='lxml'))
    for line in soup.split('\n'):
        if 'viewer.openSlide' in line:
            slide_info_raw = line
            break
    slide_info_raw = slide_info_raw.split(',')
    tiles_id = slide_info_raw[0].split("'")[1].lower()
    slide_name = slide_info_raw[2].split("'")[1]
    return tiles_id, slide_name

def GetSize(tiles_id, zoom_lvl):
    # Get image info
    # Start with large steps, then step of 1
    y_min = 0
    x_min = 0
    expected_item = int(1200 / pow(2, zoom_lvl))
    step = int(expected_item / 10)
    # Get range of y
    lower = 0
    while step > 10:
        upper, lower, step = search(tiles_id, zoom_lvl, 'y', expected_item, lower, step)
    y = lower#!/bin/python3
from threading import Thread
from os import path,system
from time import sleep
from sys import exit
from urllib import request
import http.cookiejar as cookielib
from PIL import Image, ImageDraw, ImageChops
from io import BytesIO
from math import ceil
import warnings
try:
    import mechanize
except ImportError:
    print('Module "mechanize" is missing. Trying to download...')
    os.system('python -m pip install mechanize')
    import mechanize
try:
    from bs4 import BeautifulSoup
except ImportError:
    print('Module "beautifulsoup4" is missing. Trying to download...')
    os.system('python -m pip install beautifulsoup4')
    from bs4 import BeautifulSoup
try:
    from tqdm import tqdm
except ImportError:
    print('Module "tqdm" is missing. Trying to download...')
    os.system('python -m pip install tqdm')
    from tqdm import tqdm

# Default settings
thread_amount = 2

def GetInfo(target_slide):
    global br
    # Get slide information
    br.open(target_slide)
    raw = br.response().read()
    soup = str(BeautifulSoup(raw, features='lxml'))
    for line in soup.split('\n'):
        if 'viewer.openSlide' in line:
            slide_info_raw = line
            break
    slide_info_raw = slide_info_raw.split(',')
    tiles_id = slide_info_raw[0].split("'")[1].lower()
    slide_name = slide_info_raw[2].split("'")[1]
    return tiles_id, slide_name

def GetSize(tiles_id, zoom_lvl):
    # Get image info
    # Start with large steps, then step of 1
    y_min = 0
    x_min = 0
    expected_item = int(1200 / pow(2, zoom_lvl))
    step = int(expected_item / 10)
    # Get range of y
    lower = 0
    while step > 10:
        upper, lower, step = search(tiles_id, zoom_lvl, 'y', expected_item, lower, step)
    y = lower
    while True:
        status = CheckTile(tiles_id,zoom_lvl,y,0)
        if status == 0:
            y_max = y
            break
        y += 1
    # Get range of x
    lower = 0
    while step > 10:
        upper, lower, step = search(tiles_id, zoom_lvl, 'x', expected_item, lower, step)
    x = lower
    while True:
        status = CheckTile(tiles_id,zoom_lvl,0,x)
        if status == 0:
            x_max = x
            break
        x += 1
    # Info of full image
    # Last image of each coordinate may not be square in shape
    stream = DownloadTile(tiles_id, zoom_lvl, 0,0)
    tile_size = Image.open(stream).size
    stream.close()
    stream = DownloadTile(tiles_id, zoom_lvl, 0, x_max-1)
    image_size_x = tile_size[0]*(x_max-x_min-1) + Image.open(stream).size[0]
    stream.close()
    stream = DownloadTile(tiles_id, zoom_lvl, y_max-1, 0)
    image_size_y = tile_size[1]*(y_max-y_min-1) + Image.open(stream).size[1]
    stream.close()
    image_size = (image_size_x, image_size_y)
    tiles_dimension = (x_max-x_min, y_max-y_min)
    tiles_amount = tiles_dimension[0] * tiles_dimension[1]
    return image_size, tile_size, y_min, y_max, x_min, x_max

def GetRoughTrimRange(tiles_id, zoom_lvl):
    if zoom_lvl > 5:
        # Download thumbnail for estimation
        link = str(domain) + '/MoticGallery/Tiles/thumbnails/' + str(tiles_id) + '_f_256.jpg?storage=1'
        for retries in range(3):
            try:
                data = br.open(link).read()
                stream = BytesIO(data)
            except:
                pass
        t_canvas = Image.open(stream)
        t_image_size = t_canvas.size
    else:
        # Download picture with zoom level 8 for estimation
        t_image_size, t_tile_size, t_y_min, t_y_max, t_x_min, t_x_max = GetSize(tiles_id, 8)
        t_canvas = Image.new('RGB', t_image_size, (255,255,255))
        for y in range(t_y_min,t_y_max):
            for x in range(t_x_min,t_x_max):
                stream = DownloadTile(tiles_id, 8, y, x)
                if stream == 0:
                    continue
                else:
                    pixel_x = tile_size[0] * (x-t_x_min)
                    pixel_y = tile_size[1] * (y-t_y_min)
                    grid = Image.open(stream)
                    t_canvas.paste(grid, (pixel_x,pixel_y))
                    stream.close()
        # Remove dark bands on the side
        for i in range(0,t_canvas.size[0]):
            for j in range(1,t_canvas.size[1]):
                color = t_canvas.getpixel((i,j))
                if (color == (0,0,0)):
                    t_canvas.putpixel((i,j),(255,255,255))
    # Estimate white margins location
    bg = Image.new(t_canvas.mode, t_canvas.size, (255,255,255))
    diff = ImageChops.difference(t_canvas, bg)
    diff = ImageChops.add(diff, diff)
    bbox = diff.getbbox()
    ratio = image_size[0] / t_image_size[0]
    y_min = int(bbox[1] * ratio / tile_size[1])
    y_max = ceil(bbox[3] * ratio / tile_size[1])
    x_min = int((t_image_size[0] - bbox[2]) * ratio / tile_size[0])
    x_max = ceil((t_image_size[0] - bbox[0]) * ratio / tile_size[0])
    t_canvas.close()
    #Info of trimmed image
    trimmed_image_size = (tile_size[0]*(x_max-x_min), tile_size[1]*(y_max-y_min))
    tiles_dimension = (x_max-x_min, y_max-y_min)
    tiles_amount = tiles_dimension[0] * tiles_dimension[1]
    return trimmed_image_size, y_min, y_max, x_min, x_max

def search(tiles_id, zoom_lvl, mode, upper, lower, step):
    current = 0
    while True:
        if mode == 'x':
            status = CheckTile(tiles_id,zoom_lvl,0,current)
        else:
            status = CheckTile(tiles_id,zoom_lvl,current,0)
        if status == 0:
            upper = current
            lower = current - step
            step = int((upper - lower) / 10)
            return upper, lower, step
        current += step

def CheckTile(tiles_id, zoom_lvl, y, x):
    global br
    b=int(y/25)
    a=int(x/25)
    link = str(domain) + '/MoticGallery/Tiles/' + str(tiles_id) + '/f_' + str(zoom_lvl) + '/' + str(b) + '-' + str(a) + '/' + str(y) + '_' + str(x) + '.jpg?storage=1'
    for retries in range(3):
        try:
            br.open(link)
            return 1
        except:
            sleep(1)
    return 0

def DownloaderThread(tiles_id, zoom_lvl, y_min_slice, y_max_slice, x_min_slice, x_max_slice):
    global canvas
    # Download tiles
    for y in range(y_min_slice,y_max_slice):
        for x in range(x_min_slice,x_max_slice):
            stream = DownloadTile(tiles_id, zoom_lvl, y, x)
            if stream == 0:
                progress.write('[' + str(num) + '] Grid ' + str(y) + ',' + str(x) + ' download failed')
                continue
            else:
                pixel_x = tile_size[0] * (x-x_min)
                pixel_y = tile_size[1] * (y-y_min)
                canvas.paste(Image.open(stream), (pixel_x,pixel_y))
                stream.close()
            progress.update(1)

def DownloadTile(tiles_id, zoom_lvl, y, x):
    global br
    b=int(y/25)
    a=int(x/25)
    link = str(domain) + '/MoticGallery/Tiles/' + str(tiles_id) + '/f_' + str(zoom_lvl) + '/' + str(b) + '-' + str(a) + '/' + str(y) + '_' + str(x) + '.jpg?storage=1'
    for retries in range(3):
        try:
            data = br.open(link).read()
            stream = BytesIO(data)
            return stream
        except:
            pass
    return 0

def FineTrimming(input):
    # Trim white edge
    bg = Image.new(input.mode, input.size, (255,255,255))
    diff = ImageChops.difference(input, bg)
    diff = ImageChops.add(diff, diff)
    bbox = diff.getbbox()
    if bbox:
        return input.crop(bbox)

warnings.simplefilter("ignore")

# Load credentials
try:
    config = open('settings.txt','r')
    for line in config:
        exec(line)
except OSError:
    print('settings.txt missing. Regenerating')
    config = open('settings.txt','w')
    config.write("# Keep the single quote" + '\n')
    config.write("domain = 'http://www.example.com'" + '\n')
    config.write("username = 'yourusername'" + '\n')
    config.write("password = 'yourpassword'" + '\n')
    config.close()
    print('Please fill in the domain of Motic Gallery and your credentials in settings.txt')
    input('Press Enter to continue...')
    exit()

print('MoticGallery slides downloader')
print('==============================')
print()
print('Enter URL of slide(s)')
print('If enter more than one slide, separate with semicolon (;)')
print()

target_slides = input('Input: ')

# Set zoom level
print()
print('Enter zoom level (0-13, lower is clearer)')
print('DEFAULT: 4')
print()
while True:
    selection = input('Input: ')
    try:
        if selection == '':
            selection = 4
        zoom_lvl = int(selection)
        if 0 <= zoom_lvl <= 13:
            break
    except:
        pass
    print('Invalid input')

# Download specific grids only
print()
print('Select trim mode')
print('[0] DEFAULT: Rough trim + Fine trim')
print('[1] Rough trim only')
print('[2] Custom trim')
print('[3] Full image')
print()
while True:
    selection = input('Input: ')
    if selection == '':
        selection = 0
    try:
        trim_mode = int(selection)
        if 0 <= trim_mode <= 3:
            break
    except:
        pass
    print('Invalid input')
    continue

if trim_mode == 2:
    print()
    print('Custom trim mode')
    print('Enter trimming range in format: y_min, y_max, x_min, x_max')
    print('Example: 2,5,4,7')
    print()
    while True:
        selection = input('Input: ')
        try:
            input_list = selection.replace(' ', '').split(',')
            custom_y_min, custom_y_max, custom_x_min, custom_x_max = list(map(int, input_list))
            break
        except:
            print('Invalid input')
            continue

# Initialize browser
print()
print('Initializing')
cj = cookielib.CookieJar()
br = mechanize.Browser()
br.set_cookiejar(cj)
try:
    br.open(str(domain) + '/MoticSSO/login')
except:
    print('Failed to visit ' + domain)
    print('Make sure you have internet connection and the domain set in settings.txt is correct.')
    input('Press Enter to continue...')
    exit()

# Login
print('Logging in')
br.select_form(nr=0)
br.form['username'] = username
br.form['password'] = password
br.submit()
if 'Sign in successful' in BeautifulSoup(br.response().read(), features='lxml').get_text():
    print('Login successful')
else:
    print('Login failed. Check domain, login name and password in settings.txt')
    input('Press Enter to continue...')
    exit()

num = 0
for target_slide in target_slides.replace(' ', '').split(';'):
    num += 1
    print('[' + str(num) + '] Started')
    tiles_id, slide_name = GetInfo(target_slide)
    print('[' + str(num) + '] slide name = ' + str(slide_name))
    print('[' + str(num) + '] tiles_id = ' + str(tiles_id))
    if 0 <= trim_mode <= 1 and zoom_lvl < 8:
        print('[' + str(num) + '] Getting image size')
        image_size, tile_size, y_min, y_max, x_min, x_max = GetSize(tiles_id, zoom_lvl)
        print('[' + str(num) + '] image_size = ' + str(image_size))
        print('[' + str(num) + '] Calculating rough trimming range')
        trimmed_image_size, y_min, y_max, x_min, x_max = GetRoughTrimRange(tiles_id, zoom_lvl)
        print('[' + str(num) + '] trimmed_image_size = ' + str(trimmed_image_size))
    elif trim_mode == 2:
        print('[' + str(num) + '] Using user defined trimming range')
        data = DownloadTile(tiles_id, zoom_lvl, 0, 0)
        y_min = custom_y_min
        y_max = custom_y_max
        x_min = custom_x_min
        x_max = custom_x_max
        tile_size = Image.open(data).size
        trimmed_image_size = (tile_size[0]*(x_max-x_min), tile_size[1]*(y_max-y_min))
        print('[' + str(num) + '] trimmed_image_size = ' + str(trimmed_image_size))
    else:
        print('[' + str(num) + '] Getting image size')
        image_size, tile_size, y_min, y_max, x_min, x_max = GetSize(tiles_id, zoom_lvl)
        print('[' + str(num) + '] image_size = ' + str(image_size))
        trimmed_image_size = image_size
    y_range = y_max - y_min
    x_range = x_max - x_min
    canvas = Image.new('RGB', trimmed_image_size, (255,255,255))
    progress = tqdm(desc = '[' + str(num) + '] Downloading', total = x_range * y_range)
    threads = []
    if y_range < x_range and x_range >= thread_amount:
        # Slice with x axis
        step = x_range//thread_amount
        for n in range(thread_amount):
            x_min_slice = x_min + step * n
            x_max_slice = x_min + step * (n + 1)
            if n == thread_amount - 1:
                x_max_slice = x_max
            t = Thread(target=DownloaderThread, args=(tiles_id, zoom_lvl, y_min, y_max, x_min_slice, x_max_slice))
            threads.append(t)
    elif y_range > x_range and y_range >= thread_amount:
        # Slice with y axis
        step = y_range//thread_amount
        for n in range(thread_amount):
            y_min_slice = y_min + step * n
            y_max_slice = y_min + step * (n + 1)
            if n == thread_amount - 1:
                y_max_slice = y_max
            t = Thread(target=DownloaderThread, args=(tiles_id, zoom_lvl, y_min_slice, y_max_slice, x_min, x_max))
            threads.append(t)
    else:
        # Use one thread only
        t = Thread(target=DownloaderThread, args=(tiles_id, zoom_lvl, y_min, y_max, x_min, x_max))
        threads.append(t)
    for t in threads:
        sleep(1)
        t.start()
    for t in threads:
        t.join()
    progress.close()
    # Post processing
    if trim_mode == 0:
        print('[' + str(num) + '] Fine trimming')
        canvas = FineTrimming(canvas)
    # Rotate by 90 degrees clockwise
    print('[' + str(num) + '] Rotating by 90 degrees clockwise')
    canvas = canvas.rotate(270, expand=True)
    print('[' + str(num) + '] Saving')
    canvas.save(str(slide_name) + '[' + str(zoom_lvl) + '].png')
    canvas.close()
    print('[' + str(num) + '] Done')

print('All done')

    while True:
        status = CheckTile(tiles_id,zoom_lvl,y,0)
        if status == 0:
            y_max = y
            break
        y += 1
    # Get range of x
    lower = 0
    while step > 10:
        upper, lower, step = search(tiles_id, zoom_lvl, 'x', expected_item, lower, step)
    x = lower
    while True:
        status = CheckTile(tiles_id,zoom_lvl,0,x)
        if status == 0:
            x_max = x
            break
        x += 1
    # Info of full image
    # Last image of each coordinate may not be square in shape
    stream = DownloadTile(tiles_id, zoom_lvl, 0,0)
    tile_size = Image.open(stream).size
    stream.close()
    stream = DownloadTile(tiles_id, zoom_lvl, 0, x_max-1)
    image_size_x = tile_size[0]*(x_max-x_min-1) + Image.open(stream).size[0]
    stream.close()
    stream = DownloadTile(tiles_id, zoom_lvl, y_max-1, 0)
    image_size_y = tile_size[1]*(y_max-y_min-1) + Image.open(stream).size[1]
    stream.close()
    image_size = (image_size_x, image_size_y)
    tiles_dimension = (x_max-x_min, y_max-y_min)
    tiles_amount = tiles_dimension[0] * tiles_dimension[1]
    return image_size, tile_size, y_min, y_max, x_min, x_max

def GetRoughTrimRange(tiles_id, zoom_lvl):
    if zoom_lvl > 5:
        # Download thumbnail for estimation
        link = str(domain) + '/MoticGallery/Tiles/thumbnails/' + str(tiles_id) + '_f_256.jpg?storage=1'
        for retries in range(3):
            try:
                data = br.open(link).read()
                stream = BytesIO(data)
            except:
                pass
        t_canvas = Image.open(stream)
        t_image_size = t_canvas.size
    else:
        # Download picture with zoom level 8 for estimation
        t_image_size, t_tile_size, t_y_min, t_y_max, t_x_min, t_x_max = GetSize(tiles_id, 8)
        t_canvas = Image.new('RGB', t_image_size, (255,255,255))
        for y in range(t_y_min,t_y_max):
            for x in range(t_x_min,t_x_max):
                stream = DownloadTile(tiles_id, 8, y, x)
                if stream == 0:
                    continue
                else:
                    pixel_x = tile_size[0] * (x-t_x_min)
                    pixel_y = tile_size[1] * (y-t_y_min)
                    grid = Image.open(stream)
                    t_canvas.paste(grid, (pixel_x,pixel_y))
                    stream.close()
        # Remove dark bands on the side
        for i in range(0,t_canvas.size[0]):
            for j in range(1,t_canvas.size[1]):
                color = t_canvas.getpixel((i,j))
                if (color == (0,0,0)):
                    t_canvas.putpixel((i,j),(255,255,255))
    # Estimate white margins location
    bg = Image.new(t_canvas.mode, t_canvas.size, (255,255,255))
    diff = ImageChops.difference(t_canvas, bg)
    diff = ImageChops.add(diff, diff)
    bbox = diff.getbbox()
    ratio = image_size[0] / t_image_size[0]
    y_min = int(bbox[1] * ratio / tile_size[1])
    y_max = ceil(bbox[3] * ratio / tile_size[1])
    x_min = int((t_image_size[0] - bbox[2]) * ratio / tile_size[0])
    x_max = ceil((t_image_size[0] - bbox[0]) * ratio / tile_size[0])
    t_canvas.close()
    #Info of trimmed image
    trimmed_image_size = (tile_size[0]*(x_max-x_min), tile_size[1]*(y_max-y_min))
    tiles_dimension = (x_max-x_min, y_max-y_min)
    tiles_amount = tiles_dimension[0] * tiles_dimension[1]
    return trimmed_image_size, y_min, y_max, x_min, x_max

def search(tiles_id, zoom_lvl, mode, upper, lower, step):
    current = 0
    while True:
        if mode == 'x':
            status = CheckTile(tiles_id,zoom_lvl,0,current)
        else:
            status = CheckTile(tiles_id,zoom_lvl,current,0)
        if status == 0:
            upper = current
            lower = current - step
            step = int((upper - lower) / 10)
            return upper, lower, step
        current += step

def CheckTile(tiles_id, zoom_lvl, y, x):
    global br
    b=int(y/25)
    a=int(x/25)
    link = str(domain) + '/MoticGallery/Tiles/' + str(tiles_id) + '/f_' + str(zoom_lvl) + '/' + str(b) + '-' + str(a) + '/' + str(y) + '_' + str(x) + '.jpg?storage=1'
    for retries in range(3):
        try:
            br.open(link)
            return 1
        except:
            sleep(1)
    return 0

def DownloaderThread(tiles_id, zoom_lvl, y_min_slice, y_max_slice, x_min_slice, x_max_slice):
    global canvas
    # Download tiles
    for y in range(y_min_slice,y_max_slice):
        for x in range(x_min_slice,x_max_slice):
            stream = DownloadTile(tiles_id, zoom_lvl, y, x)
            if stream == 0:
                progress.write('[' + str(num) + '] Grid ' + str(y) + ',' + str(x) + ' download failed')
                continue
            else:
                pixel_x = tile_size[0] * (x-x_min)
                pixel_y = tile_size[1] * (y-y_min)
                canvas.paste(Image.open(stream), (pixel_x,pixel_y))
                stream.close()
            progress.update(1)

def DownloadTile(tiles_id, zoom_lvl, y, x):
    global br
    b=int(y/25)
    a=int(x/25)
    link = str(domain) + '/MoticGallery/Tiles/' + str(tiles_id) + '/f_' + str(zoom_lvl) + '/' + str(b) + '-' + str(a) + '/' + str(y) + '_' + str(x) + '.jpg?storage=1'
    for retries in range(3):
        try:
            data = br.open(link).read()
            stream = BytesIO(data)
            return stream
        except:
            pass
    return 0

def FineTrimming(input):
    # Trim white edge
    bg = Image.new(input.mode, input.size, (255,255,255))
    diff = ImageChops.difference(input, bg)
    diff = ImageChops.add(diff, diff)
    bbox = diff.getbbox()
    if bbox:
        return input.crop(bbox)

warnings.simplefilter("ignore")

# Load credentials
try:
    config = open('settings.txt','r')
    for line in config:
        exec(line)
except OSError:
    print('settings.txt missing. Regenerating')
    config = open('settings.txt','w')
    config.write("# Keep the single quote" + '\n')
    config.write("domain = 'http://www.example.com'" + '\n')
    config.write("username = 'yourusername'" + '\n')
    config.write("password = 'yourpassword'" + '\n')
    config.close()
    print('Please fill in the domain of Motic Gallery and your credentials in settings.txt')
    input('Press Enter to continue...')
    exit()

print('MoticGallery slides downloader')
print('==============================')
print()
print('Enter URL of slide(s)')
print('If enter more than one slide, separate with semicolon (;)')
print()

target_slides = input('Input: ')

# Set zoom level
print()
print('Enter zoom level (0-13, lower is clearer)')
print('DEFAULT: 4')
print()
while True:
    selection = input('Input: ')
    try:
        if selection == '':
            selection = 4
        zoom_lvl = int(selection)
        if 0 <= zoom_lvl <= 13:
            break
    except:
        pass
    print('Invalid input')

# Download specific grids only
print()
print('Select trim mode')
print('[0] DEFAULT: Rough trim + Fine trim')
print('[1] Rough trim only')
print('[2] Custom trim')
print('[3] Full image')
print()
while True:
    selection = input('Input: ')
    if selection == '':
        selection = 0
    try:
        trim_mode = int(selection)
        if 0 <= trim_mode <= 3:
            break
    except:
        pass
    print('Invalid input')
    continue

if trim_mode == 2:
    print()
    print('Custom trim mode')
    print('Enter trimming range in format: y_min, y_max, x_min, x_max')
    print('Example: 2,5,4,7')
    print()
    while True:
        selection = input('Input: ')
        try:
            input_list = selection.replace(' ', '').split(',')
            custom_y_min, custom_y_max, custom_x_min, custom_x_max = list(map(int, input_list))
            break
        except:
            print('Invalid input')
            continue

# Initialize browser
print()
print('Initializing')
cj = cookielib.CookieJar()
br = mechanize.Browser()
br.set_cookiejar(cj)
br.open(str(domain) + '/MoticSSO/login')

# Login
print('Logging in')
br.select_form(nr=0)
br.form['username'] = username
br.form['password'] = password
br.submit()
if 'Sign in successful' in BeautifulSoup(br.response().read(), features='lxml').get_text():
    print('Login successful')
else:
    print('Login failed. Check domain, login name and password in settings.txt')
    input('Press Enter to continue...')
    exit()

num = 0
for target_slide in target_slides.replace(' ', '').split(';'):
    num += 1
    print('[' + str(num) + '] Started')
    tiles_id, slide_name = GetInfo(target_slide)
    print('[' + str(num) + '] slide name = ' + str(slide_name))
    print('[' + str(num) + '] tiles_id = ' + str(tiles_id))
    if 0 <= trim_mode <= 1 and zoom_lvl < 8:
        print('[' + str(num) + '] Getting image size')
        image_size, tile_size, y_min, y_max, x_min, x_max = GetSize(tiles_id, zoom_lvl)
        print('[' + str(num) + '] image_size = ' + str(image_size))
        print('[' + str(num) + '] Calculating rough trimming range')
        trimmed_image_size, y_min, y_max, x_min, x_max = GetRoughTrimRange(tiles_id, zoom_lvl)
        print('[' + str(num) + '] trimmed_image_size = ' + str(trimmed_image_size))
    elif trim_mode == 2:
        print('[' + str(num) + '] Using user defined trimming range')
        data = DownloadTile(tiles_id, zoom_lvl, 0, 0)
        y_min = custom_y_min
        y_max = custom_y_max
        x_min = custom_x_min
        x_max = custom_x_max
        tile_size = Image.open(data).size
        trimmed_image_size = (tile_size[0]*(x_max-x_min), tile_size[1]*(y_max-y_min))
        print('[' + str(num) + '] trimmed_image_size = ' + str(trimmed_image_size))
    else:
        print('[' + str(num) + '] Getting image size')
        image_size, tile_size, y_min, y_max, x_min, x_max = GetSize(tiles_id, zoom_lvl)
        print('[' + str(num) + '] image_size = ' + str(image_size))
        trimmed_image_size = image_size
    y_range = y_max - y_min
    x_range = x_max - x_min
    canvas = Image.new('RGB', trimmed_image_size, (255,255,255))
    progress = tqdm(desc = '[' + str(num) + '] Downloading', total = x_range * y_range)
    threads = []
    if y_range < x_range and x_range >= thread_amount:
        # Slice with x axis
        step = x_range//thread_amount
        for n in range(thread_amount):
            x_min_slice = x_min + step * n
            x_max_slice = x_min + step * (n + 1)
            if n == thread_amount - 1:
                x_max_slice = x_max
            t = Thread(target=DownloaderThread, args=(tiles_id, zoom_lvl, y_min, y_max, x_min_slice, x_max_slice))
            threads.append(t)
    elif y_range > x_range and y_range >= thread_amount:
        # Slice with y axis
        step = y_range//thread_amount
        for n in range(thread_amount):
            y_min_slice = y_min + step * n
            y_max_slice = y_min + step * (n + 1)
            if n == thread_amount - 1:
                y_max_slice = y_max
            t = Thread(target=DownloaderThread, args=(tiles_id, zoom_lvl, y_min_slice, y_max_slice, x_min, x_max))
            threads.append(t)
    else:
        # Use one thread only
        t = Thread(target=DownloaderThread, args=(tiles_id, zoom_lvl, y_min, y_max, x_min, x_max))
        threads.append(t)
    for t in threads:
        sleep(1)
        t.start()
    for t in threads:
        t.join()
    progress.close()
    # Post processing
    if trim_mode == 0:
        print('[' + str(num) + '] Fine trimming')
        canvas = FineTrimming(canvas)
    # Rotate by 90 degrees clockwise
    print('[' + str(num) + '] Rotating by 90 degrees clockwise')
    canvas = canvas.rotate(270, expand=True)
    print('[' + str(num) + '] Saving')
    canvas.save(str(slide_name) + '[' + str(zoom_lvl) + '].png')
    canvas.close()
    print('[' + str(num) + '] Done')

print('All done')
