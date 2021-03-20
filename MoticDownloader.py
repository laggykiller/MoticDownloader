#!/usr/bin/env python3
current_version = 'v3.0'

from threading import Thread
import os
from time import sleep
import sys
from urllib import request
from urllib.parse import urlparse
import http.cookiejar as cookielib
from io import BytesIO
from math import ceil
import warnings
import webbrowser
from configparser import ConfigParser, NoSectionError
import json
import argparse

try:
    from PIL import Image, ImageDraw, ImageChops, ImageTk
except ImportError:
    print('Module "PIL" is missing. Trying to download...')
    os.system('python3 -m pip install Pillow')
    from PIL import Image, ImageDraw, ImageChops, ImageTk
try:
    import mechanize
except ImportError:
    print('Module "mechanize" is missing. Trying to download...')
    os.system('python3 -m pip install mechanize')
    import mechanize
try:
    from bs4 import BeautifulSoup
except ImportError:
    print('Module "beautifulsoup4" is missing. Trying to download...')
    os.system('python3 -m pip install beautifulsoup4')
    os.system('python3 -m pip install lxml')
    from bs4 import BeautifulSoup
try:
    from tkinter import Tk, Frame, Label, Entry, Text, Canvas, Button, Checkbutton, Scrollbar, OptionMenu, BooleanVar, StringVar, IntVar, messagebox, filedialog, PhotoImage
    from tkinter.ttk import Progressbar
    from tkinter import ttk, TclError
except ImportError:
    print('Module "tkinter" is missing. Trying to download...')
    os.system('python3 -m pip install tkinter')
    from tkinter import Tk, Frame, Label, Entry, Text, Canvas, Button, Checkbutton, Scrollbar, OptionMenu, BooleanVar, StringVar, IntVar, messagebox, filedialog, PhotoImage
    from tkinter.ttk import Progressbar
    from tkinter import ttk, TclError
try:
    from tqdm import tqdm
except ImportError:
    print('Module "tqdm" is missing. Trying to download...')
    os.system('python3 -m pip install tqdm')
    from tqdm import tqdm

def config_save():
    config = ConfigParser()
    config.add_section('credentials')
    config.set('credentials', 'username', str(username))
    config.set('credentials', 'password', str(password))
    config.add_section('other')
    config.set('other', 'checkupdate', str(checkupdate))
    config.set('other', 'downloadpath', str(downloadpath))
    config.set('other', 'defaultzoom', str(defaultzoom))
    config.set('other', 'defaultrotation', str(defaultrotation))
    config.set('other', 'defaulttrim', str(defaulttrim))
    config.set('other', 'loginsuffix', str(loginsuffix))
    with open('config.ini', 'w') as f:
        config.write(f)

def config_clearcred():
    config = ConfigParser()
    config.add_section('credentials')
    config.set('credentials', 'username', '')
    config.set('credentials', 'password', '')
    config.add_section('other')
    config.set('other', 'checkupdate', str(checkupdate))
    config.set('other', 'downloadpath', str(downloadpath))
    config.set('other', 'defaultzoom', str(defaultzoom))
    config.set('other', 'defaultrotation', str(defaultrotation))
    config.set('other', 'defaulttrim', str(defaulttrim))
    config.set('other', 'loginsuffix', str(loginsuffix))
    with open('config.ini', 'w') as f:
        config.write(f)

def config_load():
    global username, password, checkupdate, downloadpath, defaultzoom, defaultrotation, defaulttrim, loginsuffix
    config = ConfigParser()
    try:
        config.read('config.ini')
        username = config.get('credentials', 'username')
        password = config.get('credentials', 'password')
        checkupdate = config.getboolean('other', 'checkupdate')
        downloadpath = config.get('other', 'downloadpath')
        defaultzoom = config.getint('other', 'defaultzoom')
        defaultrotation = config.getint('other', 'defaultrotation')
        defaulttrim = config.getint('other', 'defaulttrim')
        loginsuffix = config.get('other', 'loginsuffix')
    except NoSectionError:
        config_default()

def config_default():
    global username, password, checkupdate, downloadpath, defaultzoom, defaultrotation, defaulttrim, loginsuffix
    username = ''
    password = ''
    checkupdate = True
    downloadpath = ''
    defaultzoom = 4
    defaultrotation = 270
    defaulttrim = 1
    loginsuffix = '/MoticSSO/login'
    config_save()

class MoticSlide:
    global br
    def __init__(self, target_url):
        self.url = target_url
        self.zoom = defaultzoom
        self.rotation = defaultrotation
        self.trim_mode = defaulttrim

    def fetch_info(self):
        for retries in range(3):
            try:
                # Get slid name and ID
                br.open(self.url)
                raw = br.response().read()
                soup = str(BeautifulSoup(raw, features='lxml'))
                for line in soup.split('\n'):
                    if 'viewer.openSlide' in line:
                        slide_info_raw = line
                        break
                slide_info_raw = slide_info_raw.split(',')
                self.id = slide_info_raw[0].split("'")[1].lower()
                self.name = slide_info_raw[2].split("'")[1]
                # Get metadata
                metadata_url = str(domain) + '/MoticGallery/Slides/' + str(self.id) + '/Metadata'
                self.metadata = json.loads(br.open(metadata_url).read())
                self.tile_size = [self.metadata['images'][0]['tileWidth'], self.metadata['images'][0]['tileHeight']]
                self.img_size = [self.metadata['images'][0]['width'], self.metadata['images'][0]['height']]
                self.tile_amount_list = []
                for mode in self.metadata['images'][0]['layer']:
                    self.tile_amount_list.append([int(mode['Cols']), int(mode['Rows'])])
                # Download thumbnail
                timg_url = str(domain) + '/MoticGallery/Tiles/thumbnails/' + str(self.id) + '_f_256.jpg?storage=1'
                data = br.open(timg_url).read()
                stream = BytesIO(data)
                self.timg = Image.open(stream)
                return True
            except (mechanize.HTTPError, mechanize.URLError):
                pass
        return False

    def download_tile(self, y, x):
        b=int(y/25)
        a=int(x/25)
        link = str(domain) + '/MoticGallery/Tiles/' + str(self.id) + '/f_' + str(self.zoom) + '/' + str(b) + '-' + str(a) + '/' + str(y) + '_' + str(x) + '.jpg?storage=1'
        for retries in range(3):
            try:
                data = br.open(link).read()
                stream = BytesIO(data)
                return stream
            except (mechanize.HTTPError, mechanize.URLError):
                pass
        return None

    def calculate_range(self):
        # Trim range: [x_min, x_max, y_min, y_max]
        # trimrange = Trim range, expressed as pixel on full size image
        # trimrange_tile = Trim range, expressed as tile number
        # trimrange_timg = Trim range, expressed as pixel on thumbnail
        # trimrange_canvas = Trim range, expressed as pixel on canvas

        self.tile_amount = self.tile_amount_list[self.zoom]
        self.img_zoomed_size = [int(i / pow(2, self.zoom)) for i in self.img_size]
        self.timg2img_ratio = self.img_zoomed_size[0] / self.timg.size[0]
        if self.trim_mode == 1:
            # Auto trim mode
            bg = Image.new(self.timg.mode, self.timg.size, (255,255,255))
            diff = ImageChops.difference(self.timg, bg)
            bbox = diff.getbbox()
            self.trimrange_timg = [bbox[0], bbox[2], bbox[1], bbox[3]]
            self.trimrange = [int(i * self.timg2img_ratio) for i in self.trimrange_timg]
            self.trimrange_tile = [
                int(self.trimrange[0] / self.tile_size[0]),
                ceil(self.trimrange[1] / self.tile_size[0]),
                int(self.trimrange[2] / self.tile_size[1]),
                ceil(self.trimrange[3] / self.tile_size[1])
            ]
            self.canvas_size = [
                (self.trimrange_tile[1] - self.trimrange_tile[0]) * self.tile_size[0],
                (self.trimrange_tile[3] - self.trimrange_tile[2]) * self.tile_size[1]
            ]
            self.trimrange_canvas = [0,0,0,0]
        elif self.trim_mode == 2:
            # Manual trim mode
            # trimrange and trimrange_timg already set
            self.trimrange_tile = [
                int(self.trimrange[0] / self.tile_size[0]),
                ceil(self.trimrange[1] / self.tile_size[0]),
                int(self.trimrange[2] / self.tile_size[1]),
                ceil(self.trimrange[3] / self.tile_size[1])
            ]
            self.canvas_size = [
                (self.trimrange_tile[1] - self.trimrange_tile[0]) * self.tile_size[0],
                (self.trimrange_tile[3] - self.trimrange_tile[2]) * self.tile_size[1]
            ]
            self.trimrange_canvas = [
                self.trimrange[0] - self.trimrange_tile[0] * self.tile_size[0],
                self.trimrange[1] - self.trimrange_tile[0] * self.tile_size[0],
                self.trimrange[2] - self.trimrange_tile[2] * self.tile_size[1],
                self.trimrange[3] - self.trimrange_tile[2] * self.tile_size[1]
            ]
        else:
            # No trimming
            self.trimrange_timg = [0, self.timg.size[0], 0, self.timg.size[1]]
            self.trimrange = [0, self.img_zoomed_size[0], 0, self.img_zoomed_size[1]]
            self.trimrange_tile = [0, self.tile_amount[0], 0, self.tile_amount[1]]
            self.canvas_size = self.img_zoomed_size
            self.trimrange_canvas = [0,0,0,0]

    def validate_range(self):
        r = self.trimrange
        r = [max(r[0], r[1]), max(r[2], r[3]), min(r[0], r[1]), min(r[2], r[3])]
        s = self.trimrange_timg
        s = [max(s[0], s[1]), max(s[2], s[3]), min(s[0], s[1]), min(s[2], s[3])]
        if r[0] > self.img_zoomed_size[0] or r[1] > self.img_zoomed_size[1] or r[0]-r[2] == 0 or r[1]-r[3] == 0:
            return False
        else:
            return True

    def download(self):
        self.canvas = Image.new('RGB', self.canvas_size, (255,255,255))
        tiles = (self.trimrange_tile[3] - self.trimrange_tile[2]) * (self.trimrange_tile[1] - self.trimrange_tile[0])
        if workmode == 'cli':
            progress = tqdm(desc='[ACTION] Downloading', total=tiles)
        n = 0
        for y in range(self.trimrange_tile[2], self.trimrange_tile[3]):
            for x in range(self.trimrange_tile[0], self.trimrange_tile[1]):
                n += 1
                stream = self.download_tile(y, x)
                if stream == None:
                    continue
                else:
                    canvas_x = self.tile_size[0] * (x-self.trimrange_tile[0])
                    canvas_y = self.tile_size[1] * (y-self.trimrange_tile[2])
                    self.canvas.paste(Image.open(stream), (canvas_x,canvas_y))
                    stream.close()
                if workmode == 'gui':
                    gui.loading_bar['value'] += 100 / tiles
                    gui.loading_lbl6.config(text='Action: Downloading tiles (' + str(n) + '/' + str(tiles) + ')')
                else:
                    progress.update(1)
        if workmode == 'cli':
            progress.close()

    def trim(self):
        if self.trim_mode == 1:
            # Trim white edge
            bg = Image.new(self.canvas.mode, self.canvas.size, (255,255,255))
            diff = ImageChops.difference(self.canvas, bg)
            diff = ImageChops.add(diff, diff)
            bbox = diff.getbbox()
            if bbox:
                self.canvas = self.canvas.crop(bbox)
        elif self.trim_mode == 2:
            self.canvas.crop((self.trimrange_canvas[0],self.trimrange_canvas[2],self.trimrange_canvas[1],self.trimrange_canvas[3]))

    def rotate(self):
        if self.rotation != 0:
            self.canvas = self.canvas.rotate(self.rotation, expand=True)

    def save(self):
        if downloadpath != '':
            try:
                self.canvas.save(str(downloadpath) + '/' + str(self.name) + '[' + str(self.zoom) + '].png')
                self.canvas.close()
                return
            except FileNotFoundError:
                messagebox.showwarning(title='MoticDownloader', message='Cannot write in download path specified. Choose another one.')
                return
        try:
            self.canvas.save(str(self.name) + '[' + str(self.zoom) + '].png')
            self.canvas.close()
        except FileNotFoundError:
            messagebox.showwarning(title='MoticDownloader', message='Cannot write in download path specified. Choose another one.')

class AppGUI:
    def __init__(self, master):
        self.master = master
        master.title('MoticDownloader')
        master.geometry("400x600")
        master.resizable(False, False)
        self.screen_start()

    def screen_start(self):
        master = self.master
        try:
            self.frame_main.destroy()
        except AttributeError:
            pass

        # Create frames
        self.frame_main = Frame(master, width=400, height=600)
        self.frame_main.pack(expand='y', fill='both')

        self.frame_title = Frame(self.frame_main, width=400, height=150, borderwidth=5, highlightbackground='gray', highlightthickness=1)
        self.frame_urls = Frame(self.frame_main, width=400, height=300, borderwidth=5)
        self.frame_login = Frame(self.frame_main, width=400, height=100, borderwidth=5)
        self.frame_bottom = Frame(self.frame_main, width=400, height=50, borderwidth=5, highlightbackground='gray', highlightthickness=1)

        self.frame_title.pack(fill='both', anchor='n')
        self.frame_urls.pack(fill='both')
        self.frame_login.pack(fill='both')
        self.frame_bottom.pack(expand='y', fill='x', anchor='s')

        # Title frame
        self.title_lbl = Label(self.frame_title, text="Motic Downloader ",font=('Calibri',20))
        self.version_lbl = Label(self.frame_title, text='Version: ' + str(current_version))
        self.update_lbl = Label(self.frame_title, text='Update check disabled')

        self.title_lbl.grid(row=0, column=0, sticky='n')
        self.version_lbl.grid(row=1, column=0, sticky='w')
        self.update_lbl.grid(row=2, column=0, sticky='w')

        # URLs frame
        self.urls_lbl0 = Label(self.frame_urls, text="Enter URL(s) of slides below")
        self.urls_lbl1 = Label(self.frame_urls, text="(Start a new line for another URL)")
        self.urls_scroll = Scrollbar(self.frame_urls)
        self.urls_txt = Text(self.frame_urls, height=15, yscrollcommand=self.urls_scroll.set)

        self.urls_lbl0.pack(side='top', anchor='nw')
        self.urls_lbl1.pack(side='top', anchor='nw')
        self.urls_scroll.pack(side='right',fill='y')
        self.urls_txt.pack(fill='both')
        self.urls_scroll.config(command=self.urls_txt.yview)
        self.urls_txt.focus_set()

        # Login frame
        self.username_lbl = Label(self.frame_login, text='Username')
        self.password_lbl = Label(self.frame_login, text='Password')
        self.username_ent = Entry(self.frame_login, width=30)
        self.password_ent = Entry(self.frame_login, width=30, show='*')
        if username != '' and password != '':
            rememberme = True
        else:
            rememberme = False
        self.rememberme_var = BooleanVar(master, rememberme)
        self.rememberme_chk = Checkbutton(self.frame_login, text="Remember me", variable=self.rememberme_var)

        self.username_lbl.grid(row=0, column=0, sticky='w')
        self.password_lbl.grid(row=1, column=0, sticky='w')
        self.username_ent.grid(row=0, column=1)
        self.password_ent.grid(row=1, column=1)
        self.username_ent.insert(0, username)
        self.password_ent.insert(0, password)
        self.rememberme_chk.grid(row=2, column=0, sticky='w', columnspan=2)

        # Bottom frame
        self.settings_btn = Button(self.frame_bottom, text='Settings', command=self.screen_settings)
        self.next_btn = Button(self.frame_bottom, text='Next >', command=self.action_startsubmit)

        self.settings_btn.pack(side='left', anchor='sw')
        self.next_btn.pack(side='right', anchor='se')

        Thread(target=self.action_checkupdate).start()

    def screen_settings(self):
        master = self.master
        try:
            self.frame_main.destroy()
        except AttributeError:
            pass

        # Create Frames
        self.frame_main = Frame(master, width=400, height=600)
        self.frame_main.pack(expand='y', fill='both')

        self.frame_settings = Frame(self.frame_main, width=400, height=550, borderwidth=5)
        self.frame_bottom = Frame(self.frame_main, width=400, height=50, borderwidth=5, highlightbackground='gray', highlightthickness=1)

        self.frame_settings.pack(anchor='n')
        self.frame_bottom.pack(expand='y', fill='x', anchor='s')

        # Settings frame
        self.github_btn = Button(self.frame_settings, text='https://github.com/laggykiller/MoticDownloader', command=self.action_github)
        self.checkupdate_var = BooleanVar(master, checkupdate)
        self.checkupdate_chk = Checkbutton(self.frame_settings, text='Check for update at startup', variable=self.checkupdate_var)
        if username != '' and password != '':
            rememberme = True
        else:
            rememberme = False
        self.rememberme_var = BooleanVar(master, rememberme)
        self.rememberme_chk = Checkbutton(self.frame_settings, text='Save login credentials', variable=self.rememberme_var)
        self.downloadpath_lbl = Label(self.frame_settings, text='Download path')
        self.downloadpath_ent = Entry(self.frame_settings, width=15)
        self.downloadpath_btn = Button(self.frame_settings, text='Choose', command=self.action_chgdir)
        self.defaultzoom_lbl0 = Label(self.frame_settings, text='Default zoom level')
        self.defaultzoom_lbl1 = Label(self.frame_settings, text='(Lower is clearer)')
        self.defaultzoom_var = StringVar(master, defaultzoom)
        self.defaultzoom_menu = OptionMenu(self.frame_settings, self.defaultzoom_var, *zoom_options)
        self.defaultrotation_lbl = Label(self.frame_settings, text='Default rotation (CCW)')
        self.defaultrotation_var = StringVar(master, defaultrotation)
        self.defaultrotation_menu = OptionMenu(self.frame_settings, self.defaultrotation_var, '0', '90', '180', '270')
        self.defaulttrim_lbl = Label(self.frame_settings, text='Default trim')
        if defaulttrim == 0:
            self.defaulttrim_var = StringVar(master, 'None')
        elif defaulttrim == 1:
            self.defaulttrim_var = StringVar(master, 'Auto')
        else:
            self.defaulttrim_var = StringVar(master, '*')
        self.defaulttrim_menu = OptionMenu(self.frame_settings, self.defaulttrim_var, 'Auto', 'None')
        self.loginsuffix_lbl = Label(self.frame_settings, text='Login page URL suffix')
        self.loginsuffix_ent = Entry(self.frame_settings, width=15)

        self.github_btn.grid(column=0, row=0, columnspan=3, sticky='w')
        self.checkupdate_chk.grid(column=0, row=1, sticky='w')
        self.rememberme_chk.grid(column=0, row=2, sticky='w')
        self.downloadpath_lbl.grid(column=0, row=3, sticky='w')
        self.downloadpath_ent.grid(column=1, row=3, sticky='w')
        self.downloadpath_ent.insert(0, downloadpath)
        self.downloadpath_btn.grid(column=2, row=3, stick='w')
        self.defaultzoom_lbl0.grid(column=0, row=4, sticky='w')
        self.defaultzoom_lbl1.grid(column=0, row=5, sticky='w')
        self.defaultzoom_menu.config(width=5)
        self.defaultzoom_menu.grid(column=1, row=4, rowspan=2, sticky='w')
        self.defaultrotation_lbl.grid(column=0, row=6, sticky='w')
        self.defaultrotation_menu.config(width=5)
        self.defaultrotation_menu.grid(column=1, row=6, sticky='w')
        self.defaulttrim_lbl.grid(column=0, row=7, sticky='w')
        self.defaulttrim_menu.config(width=5)
        self.defaulttrim_menu.grid(column=1, row=7, sticky='w')
        self.loginsuffix_lbl.grid(column=0, row=8, sticky='w')
        self.loginsuffix_ent.grid(column=1, row=8, sticky='w')
        self.loginsuffix_ent.insert(0, loginsuffix)

        # Bottom frame
        self.default_btn = Button(self.frame_bottom, text='Default', command=self.action_defaultconf)
        self.ok_btn = Button(self.frame_bottom, text='OK', command=self.action_saveconf)
        self.cancel_btn = Button(self.frame_bottom, text='Cancel', command=self.screen_start)

        self.default_btn.pack(side='left', anchor='sw')
        self.ok_btn.pack(side='right', anchor='se')
        self.cancel_btn.pack(side='right', anchor='se')

    def screen_fetchinfo(self):
        master = self.master
        try:
            self.frame_main.destroy()
        except AttributeError:
            pass

        # Create Frames
        self.frame_main = Frame(master, width=400, height=600)
        self.frame_main.pack(expand='y', fill='both')

        self.frame_lbl = Frame(self.frame_main, width=400, height=250, borderwidth=5)
        self.frame_bar = Frame(self.frame_main, width=400, height=300, borderwidth=5)
        self.frame_bottom = Frame(self.frame_main, width=400, height=50, borderwidth=5, highlightbackground='gray', highlightthickness=1)

        self.frame_lbl.pack(expand='y', fill='both', anchor='n')
        self.frame_bar.pack(expand='y', fill='both', anchor='n')
        self.frame_bottom.pack(fill='x', anchor='s')

        # Loading frame
        self.loading_lbl = Label(self.frame_lbl, text='Getting slides info')
        self.loading_bar = Progressbar(self.frame_bar, length=400)

        self.loading_lbl.pack(side='bottom', anchor='sw')
        self.loading_bar.pack(side='top', anchor='nw')

        # Bottom frame
        self.back_btn = Button(self.frame_bottom, text='< Back', state='disabled')
        self.next_btn = Button(self.frame_bottom, text='Next >', state='disabled')

        self.back_btn.pack(side='left', anchor='sw')
        self.next_btn.pack(side='right', anchor='se')

        Thread(target=self.action_fetchinfo).start()

    def screen_preview(self):
        master = self.master
        try:
            self.frame_main.destroy()
        except AttributeError:
            pass

        # Create Frames
        self.frame_main = Frame(master, width=400, height=600)
        self.frame_main.pack(expand='y', fill='both')

        self.tip_lbl = Label(self.frame_main, text='Configure slides')
        self.frame_top = Frame(self.frame_main, width=400, height=540)
        self.frame_bottom = Frame(self.frame_main, width=400, height=50, borderwidth=5, highlightbackground='gray', highlightthickness=1)

        self.tip_lbl.pack(side='top', anchor='nw')
        self.frame_top.pack(side='top', expand='y', fill='both')
        self.frame_bottom.pack(side='bottom', expand='y', fill='x', anchor='s')

        self.frame_top0 = Frame(self.frame_top, width=320, height=300, borderwidth=5)
        self.frame_top1 = Frame(self.frame_top, width=320, height=220, borderwidth=5)
        self.frame_top2 = Frame(self.frame_top, width=320, height=20, borderwidth=5)

        self.frame_top0.pack(side='top', expand='y', fill='y', anchor='w')
        self.frame_top1.pack(side='top', expand='y', fill='y', anchor='w')
        self.frame_top2.pack(side='bottom', expand='y', fill='y', anchor='w')

        # Top0 frame
        self.timg_canvas = Canvas(self.frame_top0, width=256, height=256, highlightthickness=1, highlightbackground='grey')
        self.timg_lbl = Label(self.frame_top0, text='Drag on thumbnail for manual trim')
        self.resfull_lbl = Label(self.frame_top0, text='Pixels (Full): ')
        self.restrim_lbl = Label(self.frame_top0, text='Pixels (Trim): ')

        self.timg_canvas.grid(column=0, row=0, sticky='w')
        self.timg_lbl.grid(column=0, row=1, sticky='w')
        self.resfull_lbl.grid(column=0, row=2, sticky='w')
        self.restrim_lbl.grid(column=0, row=3, sticky='w')

        # Top1 frame
        self.name_lbl = Label(self.frame_top1, text='Slide')
        self.name_var = StringVar(master, self.target_names[1])
        self.name_menu = OptionMenu(self.frame_top1, self.name_var, *self.target_names)
        self.zoom_lbl = Label(self.frame_top1, text='Zoom level (Lower = Clearer)')
        self.zoom_var = StringVar(master, '*')
        self.zoom_menu = OptionMenu(self.frame_top1, self.zoom_var, *zoom_options)
        self.rotation_lbl = Label(self.frame_top1, text='Rotation (CCW)')
        self.rotation_var = StringVar(master, '*')
        self.rotation_menu = OptionMenu(self.frame_top1, self.rotation_var, '0', '90', '180', '270')
        self.trim_lbl = Label(self.frame_top1, text='Trim mode')
        self.trim_var = StringVar(master, '*')
        self.trim_menu = OptionMenu(self.frame_top1, self.trim_var, 'Auto', 'Manual', 'None')

        self.name_lbl.grid(column=0, row=0, sticky='w')
        self.name_menu.grid(column=1, row=0, sticky='w')
        self.zoom_lbl.grid(column=0, row=1, sticky='w')
        self.zoom_menu.config(width=5)
        self.zoom_menu.grid(column=1, row=1, sticky='w')
        self.rotation_lbl.grid(column=0, row=2, sticky='w')
        self.rotation_menu.config(width=5)
        self.rotation_menu.grid(column=1, row=2, sticky='w')
        self.trim_lbl.grid(column=0, row=3, sticky='w')
        self.trim_menu.config(width=5)
        self.trim_menu.grid(column=1, row=3, sticky='w')

        self.name_var.trace_add('write', self.action_getslideconf)
        self.zoom_var.trace_add('write', self.action_setslideconf)
        self.rotation_var.trace_add('write', self.action_setslideconf)
        self.trim_var.trace_add('write', self.action_setslideconf)

        # Top2 frame
        self.pos_lbl0 = Label(self.frame_top2, text='Trim range (x1,y1)')
        self.pos_lbl1 = Label(self.frame_top2, text='Trim range (x2,y2)')
        self.vcmd = (master.register(self.validate_num))
        self.pos_var0 = IntVar(master)
        self.pos_ent0 = Entry(self.frame_top2, width=5, text=self.pos_var0, validate='all', validatecommand=(self.vcmd, '%P'))
        self.pos_var1 = IntVar(master)
        self.pos_ent1 = Entry(self.frame_top2, width=5, text=self.pos_var1, validate='all', validatecommand=(self.vcmd, '%P'))
        self.pos_var2 = IntVar(master)
        self.pos_ent2 = Entry(self.frame_top2, width=5, text=self.pos_var2, validate='all', validatecommand=(self.vcmd, '%P'))
        self.pos_var3 = IntVar(master)
        self.pos_ent3 = Entry(self.frame_top2, width=5, text=self.pos_var3, validate='all', validatecommand=(self.vcmd, '%P'))

        self.pos_lbl0.grid(column=0, row=5, sticky='w')
        self.pos_lbl1.grid(column=0, row=6, sticky='w')
        self.pos_ent0.grid(column=1, row=5, sticky='w')
        self.pos_ent1.grid(column=2, row=5, sticky='w')
        self.pos_ent2.grid(column=1, row=6, sticky='w')
        self.pos_ent3.grid(column=2, row=6, sticky='w')

        self.pos_var0.trace_add('write', self.action_setslideconf)
        self.pos_var1.trace_add('write', self.action_setslideconf)
        self.pos_var2.trace_add('write', self.action_setslideconf)
        self.pos_var3.trace_add('write', self.action_setslideconf)

        # Bottom frame
        self.back_btn = Button(self.frame_bottom, text='< Back', command=self.screen_start)
        self.next_btn = Button(self.frame_bottom, text='Next >', command=self.action_checkslideconf)

        self.back_btn.pack(side='left', anchor='sw')
        self.next_btn.pack(side='right', anchor='se')

        self.action_getslideconf()

    def screen_download(self):
        master = self.master
        try:
            self.frame_main.destroy()
        except AttributeError:
            pass

        # Create Frames
        self.frame_main = Frame(master, width=300, height=400)
        self.frame_main.pack(expand='y', fill='both')

        self.frame_top = Frame(self.frame_main, width=400, height=250, borderwidth=5)
        self.frame_bottom = Frame(self.frame_main, width=400, height=50, borderwidth=5, highlightbackground='gray', highlightthickness=1)

        self.frame_top.pack(expand='y', fill='both', anchor='n')
        self.frame_bottom.pack(fill='x', anchor='s')

        # Loading frame
        self.timg_canvas = Canvas(self.frame_top, width=256, height=256, highlightthickness=1, highlightbackground='grey')
        self.loading_lbl0 = Label(self.frame_top, text='Number: ')
        self.loading_lbl1 = Label(self.frame_top, text='Slide name: ')
        self.loading_lbl2 = Label(self.frame_top, text='Zoom level: ')
        self.loading_lbl3 = Label(self.frame_top, text='Rotation (CCW): ')
        self.loading_lbl4 = Label(self.frame_top, text='Trim mode: ')
        self.loading_lbl5 = Label(self.frame_top, text='Pixels: ')
        self.loading_lbl6 = Label(self.frame_top, text='Action: ')
        self.loading_bar = Progressbar(self.frame_top, length=400)

        self.timg_canvas.pack(side='top', anchor='sw')
        self.loading_lbl0.pack(side='top', anchor='sw')
        self.loading_lbl1.pack(side='top', anchor='sw')
        self.loading_lbl2.pack(side='top', anchor='sw')
        self.loading_lbl3.pack(side='top', anchor='sw')
        self.loading_lbl4.pack(side='top', anchor='sw')
        self.loading_lbl5.pack(side='top', anchor='sw')
        self.loading_lbl6.pack(side='top', anchor='sw')
        self.loading_bar.pack(side='top', anchor='nw')

        # Bottom frame
        self.back_btn = Button(self.frame_bottom, text='< Back', state='disabled')
        self.next_btn = Button(self.frame_bottom, text='Next >', state='disabled')

        self.back_btn.pack(side='left', anchor='sw')
        self.next_btn.pack(side='right', anchor='se')

        Thread(target=self.action_download).start()

    def screen_finish(self):
        master = self.master
        try:
            self.frame_main.destroy()
        except AttributeError:
            pass

        # Create Frames
        self.frame_main = Frame(master, width=300, height=400)
        self.frame_main.pack(expand='y', fill='both')

        self.frame_lbl0 = Frame(self.frame_main, width=400, height=250, borderwidth=5)
        self.frame_lbl1 = Frame(self.frame_main, width=400, height=300, borderwidth=5)
        self.frame_bottom = Frame(self.frame_main, width=400, height=50, borderwidth=5, highlightbackground='gray', highlightthickness=1)

        self.frame_lbl0.pack(expand='y', fill='both', anchor='n')
        self.frame_lbl1.pack(expand='y', fill='both', anchor='n')
        self.frame_bottom.pack(fill='x', anchor='s')

        # Loading frame
        self.loading_lbl0 = Label(self.frame_lbl0, text='All done')
        self.loading_lbl1 = Label(self.frame_lbl1, text='Click "Finish" to exit')

        self.loading_lbl0.pack(side='bottom', anchor='sw')
        self.loading_lbl1.pack(side='top', anchor='nw')

        # Bottom frame
        self.startagain_btn = Button(self.frame_bottom, text='Start again', command=self.screen_start)
        self.finish_btn = Button(self.frame_bottom, text='Finish', command=exit)

        self.startagain_btn.pack(side='left', anchor='sw')
        self.finish_btn.pack(side='right', anchor='se')

    def action_checkupdate(self):
        global latest_version
        if checkupdate == True:
            self.update_lbl.config(text='Checking for update...')
            latest_version = request.urlopen('https://github.com/laggykiller/MoticDownloader/raw/main/VERSION').read().decode('utf-8').replace('\n','')
            if current_version != latest_version:
                self.update_lbl.configure(text='Latest: ' + str(latest_version), fg='red')
            else:
                self.update_lbl.configure(text='Up to date', fg='green')

    def action_chgdir(self):
        self.downloadpath_ent.delete(0, 'end')
        self.downloadpath_ent.insert(0, filedialog.askdirectory())

    def action_github(self):
        webbrowser.open_new('https://github.com/laggykiller/MoticDownloader')

    def action_saveconf(self):
        global username, password, checkupdate, downloadpath, defaultzoom, defaultrotation, defaulttrim, loginsuffix
        downloadpath = self.downloadpath_ent.get()
        if not os.access(downloadpath, os.W_OK) and downloadpath != '':
            messagebox.showwarning(title='MoticDownloader', message='Cannot write in download path specified. Choose another one.')
            return
        checkupdate = self.checkupdate_var.get()
        defaultzoom = self.defaultzoom_var.get()
        defaultrotation = int(self.defaultrotation_var.get())
        if self.defaulttrim_var.get() == 'None':
            defaulttrim = 0
        elif self.defaulttrim_var.get() == 'Manual':
            defaulttrim = 2
        else:
            defaulttrim = 1
        loginsuffix = self.loginsuffix_ent.get()
        if self.rememberme_var.get() == False:
            username = ''
            password = ''
        config_save()
        self.screen_start()

    def action_defaultconf(self):
        config_default()
        self.screen_settings()

    def action_startsubmit(self):
        global br, domain, username, password
        self.urls_txt.configure(state='disabled')
        self.username_ent.configure(state='disabled')
        self.password_ent.configure(state='disabled')
        self.rememberme_chk.configure(state='disabled')
        self.target_urls = self.urls_txt.get('1.0', 'end').replace(' ', '').split('\n')
        while('' in self.target_urls):
            self.target_urls.remove('')
        username = self.username_ent.get()
        password = self.password_ent.get()
        try:
            domain = 'http://' + urlparse(self.target_urls[0]).netloc
        except (mechanize.HTTPError, mechanize.URLError):
            messagebox.showwarning(title='MoticDownloader', message='Please enter URL of slides')
            self.urls_txt.configure(state='normal')
            self.username_ent.configure(state='normal')
            self.password_ent.configure(state='normal')
            self.rememberme_chk.configure(state='normal')
            return
        # Login
        try:
            br.open(str(domain) + str(loginsuffix))
        except (mechanize.HTTPError, mechanize.URLError):
            messagebox.showwarning(title='MoticDownloader', message='Failed to visit ' + str(domain) + str(loginsuffix) + '\nMake sure you have internet connection and URL is correct')
            self.urls_txt.configure(state='normal')
            self.username_ent.configure(state='normal')
            self.password_ent.configure(state='normal')
            self.rememberme_chk.configure(state='normal')
            return
        if 'Sign in successful' in BeautifulSoup(br.response().read(), features='lxml').get_text():
            self.screen_fetchinfo()
            return
        br.select_form(nr=0)
        br.form['username'] = username
        br.form['password'] = password
        br.submit()
        if self.rememberme_var.get() == True:
            config_save()
        else:
            username = ''
            password = ''
            config_clearcred()
        if 'Sign in successful' in BeautifulSoup(br.response().read(), features='lxml').get_text():
            self.screen_fetchinfo()
            return
        else:
            messagebox.showwarning(title='MoticDownloader', message='Login failed. Check URL, login name and password')
            self.urls_txt.configure(state='normal')
            self.username_ent.configure(state='normal')
            self.password_ent.configure(state='normal')
            self.rememberme_chk.configure(state='normal')
            return

    def action_fetchinfo(self):
        # Fetch info about slides
        # Dictionary key is slide name, value is slide object
        self.loading_lbl.config(text='Getting slides info (0' + '/' + str(len(self.target_urls)) + ')')
        self.slides_dict = {}
        self.target_names = ['(All slides)']
        n = 0
        for target_url in self.target_urls:
            n += 1
            slide = MoticSlide(target_url)
            if slide.fetch_info():
                slide.calculate_range()
                self.slides_dict[slide.name] = slide
                self.target_names.append(slide.name)
            self.loading_lbl.config(text='Getting slides info (' + str(n) + '/' + str(len(self.target_urls)) + ')')
            self.loading_bar['value'] += 100 / len(self.target_urls)
        if self.slides_dict != {}:
            self.screen_preview()
        else:
            messagebox.showwarning(title='MoticDownloader', message='None of the URL(s) supplied is valid')
            self.screen_start()

    def action_getslideconf(self, *args):
        global rect_id
        global topy, topx, botx, boty
        global updating_slide
        updating_slide = True
        topy, topx, botx, boty = 0,0,0,0
        selection = self.name_var.get()
        self.timg_canvas.delete('all')
        if selection == '(All slides)':
            self.trim_menu.destroy()
            self.trim_menu = OptionMenu(self.frame_top1, self.trim_var, 'Auto', 'None')
            self.trim_menu.config(width=5)
            self.trim_menu.grid(column=1, row=3, sticky='w')
            self.timg_canvas.config(width=256, height=256)
            self.timg_canvas.itemconfig(self.timg_canvas.create_text(95,120,anchor='nw'), text='(All slides)')
            self.timg_canvas.unbind('<Button-1>')
            self.timg_canvas.unbind('<B1-Motion>')
            zooms = []
            rotations = []
            trims = []
            for slide in self.slides_dict.values():
                zooms.append(slide.zoom)
                rotations.append(slide.rotation)
                trims.append(slide.trim_mode)
            if len(set(zooms)) == 1:
                self.zoom_var.set(zooms[0])
            else:
                self.zoom_var.set('*')
            if len(set(rotations)) == 1:
                self.rotation_var.set(rotations[0])
            else:
                self.rotation_var.set('*')
            if len(set(trims)) == 1:
                if trims[0] == 0:
                    self.trim_var.set('None')
                elif trims[0] == 1:
                    self.trim_var.set('Auto')
                else:
                    self.trim_var.set('*')
            else:
                self.trim_var.set('*')
            self.pos_ent0.config(state='disabled')
            self.pos_ent1.config(state='disabled')
            self.pos_ent2.config(state='disabled')
            self.pos_ent3.config(state='disabled')
            self.timg_canvas.config(cursor='')
            self.resfull_lbl.config(text='Pixels (Full): *')
            self.restrim_lbl.config(text='Pixels (Trim): *')
        else:
            slide = self.slides_dict[selection]
            self.trim_menu.destroy()
            self.trim_menu = OptionMenu(self.frame_top1, self.trim_var, 'Auto', 'Manual', 'None')
            self.trim_menu.config(width=5)
            self.trim_menu.grid(column=1, row=3, sticky='w')
            self.timg = slide.timg
            self.timg_draw = ImageTk.PhotoImage(self.timg)
            self.timg_canvas.config(width=self.timg.size[0],height=self.timg.size[1])
            self.timg_canvas.create_image(0,0, anchor='nw', image=self.timg_draw)
            self.timg_canvas.image = self.timg_draw
            rect_id = self.timg_canvas.create_rectangle(topx, topy, topx, topy, dash=(2,2), fill='', outline='gray')
            self.zoom_var.set(int(slide.zoom))
            self.rotation_var.set(int(slide.rotation))
            if slide.trim_mode == 0:
                self.trim_var.set('None')
                self.pos_ent0.config(state='disabled')
                self.pos_ent1.config(state='disabled')
                self.pos_ent2.config(state='disabled')
                self.pos_ent3.config(state='disabled')
                self.timg_canvas.coords(rect_id, topx, topy, topx, topy)
            elif slide.trim_mode == 1:
                self.trim_var.set('Auto')
                self.pos_ent0.config(state='disabled')
                self.pos_ent1.config(state='disabled')
                self.pos_ent2.config(state='disabled')
                self.pos_ent3.config(state='disabled')
                s = slide.trimrange_timg
                self.timg_canvas.coords(rect_id, max(s[0], s[1]), max(s[2], s[3]), min(s[0], s[1]), min(s[2],s[3]))
            elif slide.trim_mode == 2:
                self.trim_var.set('Manual')
                self.pos_ent0.config(state='normal')
                self.pos_ent1.config(state='normal')
                self.pos_ent2.config(state='normal')
                self.pos_ent3.config(state='normal')
                r = slide.trimrange
                self.pos_var0.set(min(r[0],r[1]))
                self.pos_var1.set(min(r[2],r[3]))
                self.pos_var2.set(max(r[0],r[1]))
                self.pos_var3.set(max(r[2],r[3]))
                s = slide.trimrange_timg
                self.timg_canvas.coords(rect_id, max(s[0], s[1]), max(s[2], s[3]), min(s[0], s[1]), min(s[2],s[3]))
            else:
                self.trim_var.set('*')
            self.timg_canvas.bind('<Button-1>', self.get_mouse_posn)
            self.timg_canvas.bind('<B1-Motion>', self.update_sel_rect)
            self.timg_canvas.config(cursor='tcross')
            resfull = ( slide.img_zoomed_size[0], slide.img_zoomed_size[1])
            restrim = ( slide.trimrange[1] - slide.trimrange[0], slide.trimrange[3] - slide.trimrange[2] )
            self.resfull_lbl.config(text='Pixels (Full): ' + str(resfull[0]) + 'x' + str(resfull[1]))
            self.restrim_lbl.config(text='Pixels (Trim): ' + str(restrim[0]) + 'x' + str(restrim[1]))
        updating_slide = False

    def action_setslideconf(self, *args):
        if updating_slide == True:
            return
        selection = self.name_var.get()
        if self.trim_var.get() == 'None':
            trim = 0
        elif self.trim_var.get() == 'Auto':
            trim = 1
        elif self.trim_var.get() == 'Manual':
            trim = 2
        else:
            trim = None
        if selection == '(All slides)':
            for slide in self.slides_dict.values():
                try:
                    slide.zoom = int(self.zoom_var.get())
                except ValueError:
                    pass
                try:
                    slide.rotation = int(self.rotation_var.get())
                except ValueError:
                    pass
                if trim == 0:
                    slide.trim_mode = int(trim)
                elif trim == 1:
                    slide.trim_mode = int(trim)
                slide.calculate_range()
        else:
            slide = self.slides_dict[selection]
            slide.zoom = int(self.zoom_var.get())
            slide.rotation = int(self.rotation_var.get())
            if trim == 0:
                slide.trim_mode = int(trim)
                self.pos_ent0.config(state='disabled')
                self.pos_ent1.config(state='disabled')
                self.pos_ent2.config(state='disabled')
                self.pos_ent3.config(state='disabled')
                slide.calculate_range()
                self.timg_canvas.coords(rect_id, topx, topy, topx, topy)
            elif trim == 1:
                slide.trim_mode = int(trim)
                self.pos_ent0.config(state='disabled')
                self.pos_ent1.config(state='disabled')
                self.pos_ent2.config(state='disabled')
                self.pos_ent3.config(state='disabled')
                slide.calculate_range()
                s = slide.trimrange_timg
                self.timg_canvas.coords(rect_id, max(s[0], s[1]), max(s[2], s[3]), min(s[0], s[1]), min(s[2],s[3]))
            elif trim == 2:
                slide.trim_mode = int(trim)
                self.pos_ent0.config(state='normal')
                self.pos_ent1.config(state='normal')
                self.pos_ent2.config(state='normal')
                self.pos_ent3.config(state='normal')
                if holding == True:
                    x1 = min(topx, botx)
                    x2 = max(topx, botx)
                    y1 = min(topy, boty)
                    y2 = max(topy, boty)
                    slide.trimrange_timg = [x1, x2, y1, y2]
                    self.pos_var0.set(int(x1 * slide.timg2img_ratio))
                    self.pos_var1.set(int(y1 * slide.timg2img_ratio))
                    self.pos_var2.set(int(x2 * slide.timg2img_ratio))
                    self.pos_var3.set(int(y2 * slide.timg2img_ratio))
                    slide.trimrange = [self.pos_var0.get(), self.pos_var2.get(), self.pos_var1.get(), self.pos_var3.get()]
                else:
                    slide.trimrange = [self.pos_var0.get(), self.pos_var2.get(), self.pos_var1.get(), self.pos_var3.get()]
                    slide.trimrange_timg = [int(i / slide.timg2img_ratio) for i in slide.trimrange]
                    s = slide.trimrange_timg
                    self.timg_canvas.coords(rect_id, max(s[0], s[1]), max(s[2], s[3]), min(s[0], s[1]), min(s[2],s[3]))
                slide.calculate_range()
            res = slide.canvas_size
            resfull = ( slide.img_zoomed_size[0], slide.img_zoomed_size[1])
            restrim = ( slide.trimrange[1] - slide.trimrange[0], slide.trimrange[3] - slide.trimrange[2] )
            self.resfull_lbl.config(text='Pixels (Full): ' + str(resfull[0]) + 'x' + str(resfull[1]))
            self.restrim_lbl.config(text='Pixels (Trim): ' + str(restrim[0]) + 'x' + str(restrim[1]))

    def action_checkslideconf(self, *args):
        for slide in self.slides_dict.values():
            if slide.validate_range() == False:
                messagebox.showwarning(title='MoticDownloader', message='Invalid trim range')
                return
        self.screen_download()

    def action_download(self, *args):
        n = 0
        for slide in self.slides_dict.values():
            n += 1
            self.timg = slide.timg
            self.timg_draw = ImageTk.PhotoImage(self.timg)
            self.timg_canvas.config(width=self.timg.size[0],height=self.timg.size[1])
            self.timg_canvas.create_image(0,0, anchor='nw', image=self.timg_draw)
            self.timg_canvas.image = self.timg_draw
            s = slide.trimrange_timg
            self.timg_canvas.create_rectangle(s[0], s[2], s[1], s[3], dash=(2,2), fill='', outline='gray')
            self.loading_lbl0.config(text='Number: ' + str(n) + '/' + str(len(self.slides_dict)))
            self.loading_lbl1.config(text='Slide name: ' + str(slide.name))
            self.loading_lbl2.config(text='Zoom level: ' + str(slide.zoom))
            self.loading_lbl3.config(text='Rotation (CCW): ' + str(slide.rotation))
            if slide.trim_mode == 0:
                self.loading_lbl4.config(text='Trim mode: None')
            elif slide.trim_mode == 1:
                self.loading_lbl4.config(text='Trim mode: Auto')
            elif slide.trim_mode == 2:
                self.loading_lbl4.config(text='Trim mode: Manual')
            r = slide.trimrange
            self.loading_lbl5.config(text='Pixels: '+ '(' + str(min(r[0],r[1])) + ',' + str(min(r[2],r[3])) + ') to (' + str(max(r[0],r[1])) + ',' + str(max(r[2],r[3])) + ')')
            self.loading_lbl6.config(text='Action: Downloading tiles')
            self.loading_bar.stop()
            self.loading_bar.config(mode='determinate')
            slide.download()
            self.loading_bar['value'] = 0
            self.loading_bar.config(mode='indeterminate')
            self.loading_bar.start(50)
            self.loading_lbl6.config(text='Action: Trimming')
            slide.trim()
            self.loading_lbl6.config(text='Action: Rotating')
            slide.rotate()
            self.loading_lbl6.config(text='Action: Saving')
            slide.save()
        self.screen_finish()

    def get_mouse_posn(self, event):
        global topy, topx
        topx, topy = event.x, event.y

    def update_sel_rect(self, event):
        global rect_id
        global topy, topx, botx, boty
        global holding
        holding = True
        botx, boty = event.x, event.y
        self.timg_canvas.coords(rect_id, topx, topy, botx, boty)
        if botx > 88:
            botx = 88
        if botx < 0:
            botx = 0
        if boty > 256:
            boty = 256
        if boty < 0:
            boty = 0
        self.trim_var.set('Manual')
        self.action_setslideconf()
        holding = False

    def validate_num(self, input):
        if str.isdigit(input):
            return True
        else:
            return False

class AppCLI:
    def __init__(self):
        global br, domain, username, password
        # Domain
        self.target_urls = args.target_urls
        try:
            domain = 'http://' + urlparse(self.target_urls[0]).netloc
        except (mechanize.HTTPError, mechanize.URLError):
            self.message('Please enter URL of slides')
            sys.exit()
        # Username
        if args.username != None:
            username = args.username
        # Password
        if args.password != None:
            password = args.password
        # Zoom level
        if args.zoom != None:
            self.zoom = args.zoom
        else:
            self.zoom = defaultzoom
        # Rotation
        if args.rotation != None:
            self.rotation = args.rotation
        else:
            self.rotation = defaultrotation
        # Trim mode
        try:
            self.trim_mode = args.trim_mode.lower()
        except AttributeError:
            pass
        if args.trim_mode == 'm' or args.trim_mode == 'manual' or args.trim != None:
            self.trim_mode = 2
        elif args.trim_mode == 'a' or args.trim_mode == 'auto':
            self.trim_mode = 1
        elif args.trim_mode == 'n' or args.trim_mode == 'none':
            self.trim_mode = 0
        elif args.trim_mode == None:
            try:
                if 0 <= defaulttrim <= 2:
                    self.trim_mode = int(defaulttrim)
                else:
                    self.message('[ERROR] Invalid defaulttrim value in config.ini')
                    sys.exit()
            except TypeError:
                self.message('[ERROR] Invalid defaulttrim value in config.ini')
                sys.exit()
        else:
            self.message('[ERROR] Invalid trim mode (-m) value')
            sys.exit()
        # Trim range
        if self.trim_mode == 2:
            try:
                if type(args.trim) == list and len(args.trim) == 4:
                    self.trim = [min(args.trim[0], args.trim[1]), max(args.trim[0], args.trim[1]), min(args.trim[2], args.trim[3]), max(args.trim[2], args.trim[3])]
                else:
                    self.message('[ERROR] Invalid trim range (-t) value')
                    sys.exit()
            except TypeError:
                self.message('[ERROR] Invalid trim range (-t) value')
                sys.exit()
        # Login
        self.message('[INFO] Zoom = ' + str(self.zoom))
        self.message('[INFO] Rotation = ' + str(self.rotation))
        self.message('[INFO] Trim mode = ' + str(self.trim_mode))
        if self.trim_mode == 2:
            self.message('[INFO] Trim range = ' + str(self.trim))

        self.message('[ACTION] Login')
        try:
            if args.loginpage == None:
                br.open(str(domain) + str(loginsuffix))
            else:
                br.open(args.loginpage)
        except (mechanize.HTTPError, mechanize.URLError):
            self.message('[ERROR] Failed to visit ' + str(domain) + str(loginsuffix) + '. Make sure you have internet connection and URL is correct')
            sys.exit()
        if 'Sign in successful' not in BeautifulSoup(br.response().read(), features='lxml').get_text():
            br.select_form(nr=0)
            br.form['username'] = username
            br.form['password'] = password
            br.submit()
            if 'Sign in successful' not in BeautifulSoup(br.response().read(), features='lxml').get_text():
                self.message('[ERROR] Login failed. Check URL, login name and password')
                sys.exit()
        # Download
        n = 0
        self.slides_dict = {}
        for target_url in self.target_urls:
            n += 1
            self.message()
            self.message('[INFO] Currently on slide: ' + str(n) + '/' + str(len(self.target_urls)))
            self.message('[INFO] Slide URL = ' + str(target_url))
            slide = MoticSlide(target_url)
            if slide.fetch_info():
                slide.calculate_range()
                self.slides_dict[slide.name] = slide
                slide.zoom = self.zoom
                slide.rotation = self.rotation
                slide.trim_mode = self.trim_mode
                if self.trim_mode == 2:
                    slide.trimrange = self.trim
                    slide.trimrange_timg = [int(i / slide.timg2img_ratio) for i in slide.trimrange]
                slide.calculate_range()
                self.message('[ACTION] Getting slide info')
                self.message('[INFO] Name = ' + str(slide.name))
                self.message('[INFO] ID = ' + str(slide.id))
                self.message('[INFO] Full slide dimension = ' + str(slide.img_size))
                self.message('[INFO] Trimmed slide dimension = ' + str(slide.img_zoomed_size))
                if args.dryrun != None:
                    self.message('[ACTION] Downloading')
                    slide.download()
                    self.message('[ACTION] Trimming')
                    slide.trim()
                    self.message('[ACTION] Rotating')
                    slide.rotate()
                    self.message('[ACTION] Saving')
                    slide.save()
                else:
                    message('[INFO] Dry run (-d) set. Skipped downloading')
            else:
                message('[ERROR] Unable to download this slide')

    def message(self, msg=''):
        if args.quiet == False:
            print(msg)

parser = argparse.ArgumentParser(description='Download slides from MoticGallery. Supply any arguments to start in CLI mode instead of GUI mode.')
parser.add_argument('target_urls', nargs='*', help='URL of slide to download')
parser.add_argument('-q', '--quiet', action='store_true', help="Do not show any message")
parser.add_argument('-n', '--dryrun', action='store_true', help="Show slide metadata only")
parser.add_argument('-l', '--loginpage', action='store', type=str, help="Specify login page URL for login")
parser.add_argument('-u', '--username', action='store', type=str, help="Set username for login")
parser.add_argument('-p', '--password', action='store', type=str, help="Set password for login")
parser.add_argument('-z', '--zoom', action='store', type=int, help="Set zoom level (0-13)")
parser.add_argument('-r', '--rotation', action='store', type=int, choices=[0, 90, 180, 270], help="Set counterclockwise rotation (0 | 90 | 180 | 270)")
parser.add_argument('-m', '--trim_mode', action='store', type=str, choices=['n', 'none', 'a', 'auto', 'm', 'manual'], help="Set trim mode ([n]one | [a]uto | [m]anual)")
parser.add_argument('-t', '--trim', action='store', type=int, nargs=4, metavar=('x1', 'x2', 'y1', 'y2'), help="Set trim range on full image (x1, x2, y1, y2)")

args=parser.parse_args()

# Load settings
domain = None
username = ''
password = ''
checkupdate = None
downloadpath = ''
defaultzoom = None
defaultrotation = None
defaulttrim = None
loginsuffix = None
config_load()

latest_version = None
topx, topy, botx, boty = 0, 0, 0, 0
rect_id = None
zoom_options = [str(i) for i in range(0,14)]
updating_slide = False
holding = False
workmode = None

# Initialize browser
cj = cookielib.CookieJar()
br = mechanize.Browser()
br.set_cookiejar(cj)

if args.target_urls == []:
    try:
        workmode = 'gui'
        root = Tk()
        if getattr(sys, 'frozen', False) and sys.platform != 'darwin':
            icon_path = os.path.join(sys._MEIPASS, 'icon/app.png')
        else:
            icon_path = 'icon/app.png'
        try:
            root.tk.call('wm', 'iconphoto', root._w, PhotoImage(file=icon_path))
        except TclError:
            print('icon/app.png missing')
        gui = AppGUI(root)
        root.mainloop()
    except TclError:
        print('Failed to start GUI. Perhaps windows server (e.g. Xorg) is not working.')
        print('Supply any arguments to start in CLI mode instead of GUI mode.')
else:
    workmode = 'cli'
    cli = AppCLI()

sys.exit()
