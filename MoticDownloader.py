#/usr/bin/env python3
current_version = 'v2.0'

from threading import Thread
import os
from time import sleep
from sys import exit
from urllib import request
from urllib.parse import urlparse
import http.cookiejar as cookielib
from PIL import Image, ImageDraw, ImageChops, ImageTk
from io import BytesIO
from math import ceil
import warnings
import webbrowser
from configparser import ConfigParser

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
    from tkinter import Tk, Frame, Label, Entry, Text, Canvas, Button, Checkbutton, Scrollbar, OptionMenu, Scale, Listbox, BooleanVar, StringVar, messagebox, filedialog
    from tkinter.ttk import Progressbar
    from tkinter import ttk
except ImportError:
    print('Module "tkinter" is missing. Trying to download...')
    os.system('python3 -m pip install tkinter')
    from tkinter import Tk, Frame, Label, Entry, Text, Canvas, Button, Checkbutton, Scrollbar, OptionMenu, Scale, Listbox, BooleanVar, StringVar, messagebox, filedialog
    from tkinter.ttk import Progressbar
    from tkinter import ttk

def ConfigSave():
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

def ConfigClearcred():
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

def ConfigLoad():
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
    except:
        ConfigDefault()

def ConfigDefault():
    global username, password, checkupdate, downloadpath, defaultzoom, defaultrotation, defaulttrim, loginsuffix
    username = ''
    password = ''
    checkupdate = True
    downloadpath = ''
    defaultzoom = 4
    defaultrotation = 270
    defaulttrim = 0
    loginsuffix = '/MoticSSO/login'
    ConfigSave()

class MoticSlide:
    global br
    def __init__(self, target_url):
        self.url = target_url
        self.zoom = defaultzoom
        self.rotation = defaultrotation
        self.timg = 0
        self.tile_size = 0
        self.id = ''
        self.name = ''

        #Image size: [x,y]
        # Whole image size at that zoom level, expressed as tile number
        self.imgsize_tile = [0,0]
        # Whole image size at that zoom level, expressed as pixel
        self.imgsize_pix = [0,0]
        # Canvas size
        self.canvas_size = [0,0]

        # trim_mode: 0=None 1=Auto 2=Manual
        self.trim_mode = defaulttrim

        # Trim range: [x_min, x_max, y_min, y_max]
        # Trim range, expressed as tile number
        self.trimrange_tile = [-1,-1,-1,-1]
        # Trim range, expressed as pixel on thumbnail
        self.trimrange_timg = [-1,-1,-1,-1]
        # Trim range, expressed as pixel on canvas
        self.trimrange_canvas = [-1,-1,-1,-1]

    def FetchInfo(self):
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
                # Download thumbnail
                timg_url = str(domain) + '/MoticGallery/Tiles/thumbnails/' + str(self.id) + '_f_256.jpg?storage=1'
                data = br.open(timg_url).read()
                stream = BytesIO(data)
                self.timg = Image.open(stream)
                return True
            except:
                pass
        return False

    def FetchSize(self):
        expected_item = 1024 / pow(2, self.zoom)
        step = int(expected_item / 8)
        if step < 8:
            step = 1
        # Find maximum x tile in full image
        while True:
            self.imgsize_tile[0] += step
            if self.CheckTile(0,self.imgsize_tile[0]) == False:
                if step >= 8:
                    self.imgsize_tile[0] -= step
                    step = int(step / 2)
                elif step != 1:
                    self.imgsize_tile[0] -= step
                    step = 1
                else:
                    break
        # Find maximum y tile in full image
        while True:
            self.imgsize_tile[1] += step
            if self.CheckTile(self.imgsize_tile[1],0) == False:
                if step >= 8:
                    self.imgsize_tile[1] -= step
                    step = int(step / 4)
                elif step != 1:
                    self.imgsize_tile[1] -= step
                    step = 1
                else:
                    break
        # Info of full image
        # Last image of each coordinate may not be square in shape
        stream = self.DownloadTile(0,0)
        self.tile_size = Image.open(stream).size
        stream.close()
        stream = self.DownloadTile(0, self.imgsize_tile[0]-1)
        self.imgsize_pix[0] = self.tile_size[0]*(self.imgsize_tile[0]-1) + Image.open(stream).size[0]
        stream.close()
        stream = self.DownloadTile(self.imgsize_tile[1]-1, 0)
        self.imgsize_pix[1] = self.tile_size[1]*(self.imgsize_tile[1]-1) + Image.open(stream).size[1]
        stream.close()

    def CheckTile(self, y, x):
        b=int(y/25)
        a=int(x/25)
        link = str(domain) + '/MoticGallery/Tiles/' + str(self.id) + '/f_' + str(self.zoom) + '/' + str(b) + '-' + str(a) + '/' + str(y) + '_' + str(x) + '.jpg?storage=1'
        for retries in range(3):
            try:
                br.open(link)
                return True
            except:
                sleep(1)
        return False

    def DownloadTile(self, y, x):
        b=int(y/25)
        a=int(x/25)
        link = str(domain) + '/MoticGallery/Tiles/' + str(self.id) + '/f_' + str(self.zoom) + '/' + str(b) + '-' + str(a) + '/' + str(y) + '_' + str(x) + '.jpg?storage=1'
        for retries in range(3):
            try:
                data = br.open(link).read()
                stream = BytesIO(data)
                return stream
            except:
                pass
        return None

    def SetRange(self):
        if self.trim_mode == 1:
            # Auto trim mode
            bg = Image.new(self.timg.mode, self.timg.size, (255,255,255))
            diff = ImageChops.difference(self.timg, bg)
            bbox = diff.getbbox()
            self.trimrange_timg = [bbox[0], bbox[2], bbox[1], bbox[3]]
            self.trimrange_tile = [
                int(self.trimrange_timg[0] * self.imgsize_pix[0] / self.timg.size[0] / self.tile_size[0]),
                ceil(self.trimrange_timg[1] * self.imgsize_pix[0] / self.timg.size[0] / self.tile_size[0]),
                int(self.trimrange_timg[2] * self.imgsize_pix[1] / self.timg.size[1] / self.tile_size[1]),
                ceil(self.trimrange_timg[3] * self.imgsize_pix[1] / self.timg.size[1] / self.tile_size[1])
            ]
            self.canvas_size = [
                (self.trimrange_tile[1] - self.trimrange_tile[0]) * self.tile_size[0],
                (self.trimrange_tile[3] - self.trimrange_tile[2]) * self.tile_size[1]
            ]
            self.trimrange_canvas = [-1,-1,-1,-1]
        elif self.trim_mode == 2:
            # Manual trim mode
            self.trimrange_tile = [
                int(self.trimrange_timg[0] * self.imgsize_pix[0] / self.timg.size[0] / self.tile_size[0]),
                ceil(self.trimrange_timg[1] * self.imgsize_pix[0] / self.timg.size[0] / self.tile_size[0]),
                int(self.trimrange_timg[2] * self.imgsize_pix[1] / self.timg.size[1] / self.tile_size[1]),
                ceil(self.trimrange_timg[3] * self.imgsize_pix[1] / self.timg.size[1] / self.tile_size[1])
            ]
            self.canvas_size = [
                (self.trimrange_tile[1] - self.trimrange_tile[0]) * self.tile_size[0],
                (self.trimrange_tile[3] - self.trimrange_tile[2]) * self.tile_size[1]
            ]
            self.trimrange_canvas = [
                int(self.trimrange_timg[0] * self.imgsize_pix[0] / self.timg.size[0]) - self.trimrange_tile[0] * self.tile_size[0],
                ceil(self.trimrange_timg[1] * self.imgsize_pix[0] / self.timg.size[0]) - self.trimrange_tile[0] * self.tile_size[0],
                int(self.trimrange_timg[2] * self.imgsize_pix[1] / self.timg.size[1]) - self.trimrange_tile[2] * self.tile_size[1],
                ceil(self.trimrange_timg[3] * self.imgsize_pix[1] / self.timg.size[1]) - self.trimrange_tile[2] * self.tile_size[1]
            ]
        else:
            # No trimming
            self.trimrange_timg = [0, self.timg.size[0], 0, self.timg.size[1]]
            self.trimrange_tile = [
                0,
                ceil(self.timg.size[0] * self.imgsize_pix[0] / self.timg.size[0] / self.tile_size[0]),
                0,
                ceil(self.timg.size[0] * self.imgsize_pix[1] / self.timg.size[1] / self.tile_size[1])
            ]
            self.canvas_size = [
                self.trimrange_tile[1] * self.tile_size[0],
                self.trimrange_tile[3] * self.tile_size[1]
            ]
            self.trimrange_canvas = [-1,-1,-1,-1]

    def Download(self):
        self.canvas = Image.new('RGB', self.canvas_size, (255,255,255))
        tile_amount = (self.trimrange_tile[3] - self.trimrange_tile[2]) * (self.trimrange_tile[1] - self.trimrange_tile[0])
        n = 0
        for y in range(self.trimrange_tile[2], self.trimrange_tile[3]):
            for x in range(self.trimrange_tile[0], self.trimrange_tile[1]):
                n += 1
                gui.loading_bar['value'] += 100 / tile_amount
                gui.loading_lbl1.config(text='Action: Downloading tiles (' + str(n) + '/' + str(tile_amount) + ')')
                stream = self.DownloadTile(y, x)
                if stream == None:
                    continue
                else:
                    canvas_x = self.tile_size[0] * (x-self.trimrange_tile[0])
                    canvas_y = self.tile_size[1] * (y-self.trimrange_tile[2])
                    self.canvas.paste(Image.open(stream), (canvas_x,canvas_y))
                    stream.close()

    def Trim(self):
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

    def Rotate(self):
        if self.rotation != 0:
            self.canvas = self.canvas.rotate(self.rotation, expand=True)

    def Save(self):
        if downloadpath != '':
            try:
                self.canvas.save(str(downloadpath) + '/' + str(self.name) + '[' + str(self.zoom) + '].png')
                self.canvas.close()
                return
            except:
                pass
        self.canvas.save(str(self.name) + '[' + str(self.zoom) + '].png')
        self.canvas.close()

class AppGUI:
    def __init__(self, master):
        self.master = master
        master.title('MoticDownloader')
        master.geometry("400x600")
        master.resizable(False, False)
        self.StartScreen()

    def StartScreen(self):
        master = self.master
        try:
            self.frame_main.destroy()
        except:
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
        self.settings_btn = Button(self.frame_bottom, text='Settings', command=self.SettingsScreen)
        self.next_btn = Button(self.frame_bottom, text='Next >', command=self.ActionStartSubmit)

        self.settings_btn.pack(side='left', anchor='sw')
        self.next_btn.pack(side='right', anchor='se')

        Thread(target=self.ActionCheckupdate).start()

    def SettingsScreen(self):
        master = self.master
        try:
            self.frame_main.destroy()
        except:
            pass

        # Create Frames
        self.frame_main = Frame(master, width=400, height=600)
        self.frame_main.pack(expand='y', fill='both')

        self.frame_settings = Frame(self.frame_main, width=400, height=550, borderwidth=5)
        self.frame_bottom = Frame(self.frame_main, width=400, height=50, borderwidth=5, highlightbackground='gray', highlightthickness=1)

        self.frame_settings.pack(anchor='n')
        self.frame_bottom.pack(expand='y', fill='x', anchor='s')

        # Settings frame
        self.github_btn = Button(self.frame_settings, text='https://github.com/laggykiller/MoticDownloader', command=self.ActionGithub)
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
        self.downloadpath_btn = Button(self.frame_settings, text='Choose', command=self.ActionCD)
        self.defaultzoom_lbl0 = Label(self.frame_settings, text='Default zoom level')
        self.defaultzoom_lbl1 = Label(self.frame_settings, text='(Lower is clearer)')
        self.defaultzoom_scale = Scale(self.frame_settings, from_=0, to=13, orient='horizontal', length=100)
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
        self.defaultzoom_scale.set(int(defaultzoom))
        self.defaultzoom_scale.grid(column=1, row=4, rowspan=2, sticky='w')
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
        self.default_btn = Button(self.frame_bottom, text='Default', command=self.ActionDefaultconf)
        self.ok_btn = Button(self.frame_bottom, text='OK', command=self.ActionSaveconf)
        self.cancel_btn = Button(self.frame_bottom, text='Cancel', command=self.StartScreen)

        self.default_btn.pack(side='left', anchor='sw')
        self.ok_btn.pack(side='right', anchor='se')
        self.cancel_btn.pack(side='right', anchor='se')

    def FetchinfoScreen(self):
        master = self.master
        try:
            self.frame_main.destroy()
        except:
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

        Thread(target=self.ActionFetchinfo).start()

    def PreviewScreen(self):
        master = self.master
        try:
            self.frame_main.destroy()
        except:
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

        self.frame_list = Frame(self.frame_top, width=80, height=540, borderwidth=5)
        self.frame_prop = Frame(self.frame_top, width=320, height=540, borderwidth=5)

        self.frame_list.pack(side='left', fill='y', anchor='w')
        self.frame_prop.pack(side='left', expand='y', fill='y', anchor='w')

        # List frame
        self.listbox = Listbox(self.frame_list, width=12, height=20)
        self.listbox.bind('<<ListboxSelect>>', self.ActionGetslideconf)
        self.listbox.pack(side='left', expand='y', fill='both')

        self.listbox_scroll = Scrollbar(self.frame_list)
        self.listbox_scroll.pack(side='right', fill='both')

        self.listbox.insert(0, '(All slides)')

        for slide in self.target_objs:
            self.listbox.insert('end', slide.name)

        self.listbox.select_set(0)
        self.listbox.config(yscrollcommand=self.listbox_scroll.set)
        self.listbox_scroll.config(command=self.listbox.yview)

        # Property frame
        self.timg_lbl = Label(self.frame_prop, text='Drag on thumbnail for manual trim                 ')
        self.timg_canvas = Canvas(self.frame_prop, width=256, height=256, highlightthickness=1, highlightbackground='grey')
        self.name_lbl = Label(self.frame_prop, text='Name: ')
        self.zoom_lbl0 = Label(self.frame_prop, text='Zoom level')
        self.zoom_lbl1 = Label(self.frame_prop, text='(Lower is clearer)')
        self.zoom_scale = Scale(self.frame_prop, from_=0, to=13, orient='horizontal')
        self.rotation_lbl = Label(self.frame_prop, text='Rotation (CCW)')
        self.rotation_var = StringVar(master, '*')
        self.rotation_menu = OptionMenu(self.frame_prop, self.rotation_var, '0', '90', '180', '270')
        self.trim_lbl = Label(self.frame_prop, text='Trim mode')
        self.trim_var = StringVar(master, '*')
        self.trim_menu = OptionMenu(self.frame_prop, self.trim_var, 'Auto', 'Manual', 'None')
        self.pos_lbl0 = Label(self.frame_prop, text='Trim range')
        self.pos_lbl1 = Label(self.frame_prop, text='(Auto)')
        self.set_btn = Button(self.frame_prop, text='Set', command=self.ActionSetslideconf)

        self.timg_lbl.grid(column=0, row=0, sticky='w', columnspan=3)
        self.timg_canvas.grid(column=0, row=1, sticky='w', columnspan=2)
        self.name_lbl.grid(column=0, row=2, sticky='w', columnspan=3)
        self.zoom_lbl0.grid(column=0, row=3, sticky='w')
        self.zoom_lbl1.grid(column=0, row=4, sticky='w')
        self.zoom_scale.grid(column=1, row=3, sticky='e', rowspan=2)
        self.rotation_lbl.grid(column=0, row=5, sticky='w')
        self.rotation_menu.config(width=5)
        self.rotation_menu.grid(column=1, row=5, sticky='e')
        self.trim_lbl.grid(column=0, row=6, sticky='w')
        self.trim_menu.config(width=5)
        self.trim_menu.grid(column=1, row=6, sticky='e')
        self.pos_lbl0.grid(column=0, row=7, sticky='w')
        self.pos_lbl1.grid(column=1, row=7, sticky='e')
        self.set_btn.grid(column=0, row=8, sticky='w')

        # Bottom frame
        self.back_btn = Button(self.frame_bottom, text='< Back', command=self.StartScreen)
        self.next_btn = Button(self.frame_bottom, text='Next >', command=self.DownloadScreen)

        self.back_btn.pack(side='left', anchor='sw')
        self.next_btn.pack(side='right', anchor='se')

        self.ActionGetslideconf()

    def DownloadScreen(self):
        master = self.master
        try:
            self.frame_main.destroy()
        except:
            pass

        # Create Frames
        self.frame_main = Frame(master, width=300, height=400)
        self.frame_main.pack(expand='y', fill='both')

        self.frame_lbl = Frame(self.frame_main, width=400, height=250, borderwidth=5)
        self.frame_bar = Frame(self.frame_main, width=400, height=300, borderwidth=5)
        self.frame_bottom = Frame(self.frame_main, width=400, height=50, borderwidth=5, highlightbackground='gray', highlightthickness=1)

        self.frame_lbl.pack(expand='y', fill='both', anchor='n')
        self.frame_bar.pack(expand='y', fill='both', anchor='n')
        self.frame_bottom.pack(fill='x', anchor='s')

        # Loading frame
        self.loading_lbl0 = Label(self.frame_lbl, text='Slide name')
        self.loading_lbl1 = Label(self.frame_lbl, text='Action')
        self.loading_bar = Progressbar(self.frame_bar, length=400)

        self.loading_lbl1.pack(side='bottom', anchor='sw')
        self.loading_lbl0.pack(side='bottom', anchor='sw')
        self.loading_bar.pack(side='top', anchor='nw')

        # Bottom frame
        self.back_btn = Button(self.frame_bottom, text='< Back', state='disabled')
        self.next_btn = Button(self.frame_bottom, text='Next >', state='disabled')

        self.back_btn.pack(side='left', anchor='sw')
        self.next_btn.pack(side='right', anchor='se')

        Thread(target=self.ActionDownload).start()

    def FinishScreen(self):
        master = self.master
        try:
            self.frame_main.destroy()
        except:
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
        self.startagain_btn = Button(self.frame_bottom, text='Start again', command=self.StartScreen)
        self.finish_btn = Button(self.frame_bottom, text='Finish', command=exit)

        self.startagain_btn.pack(side='left', anchor='sw')
        self.finish_btn.pack(side='right', anchor='se')

    def ActionCheckupdate(self):
        global latest_version
        if checkupdate == True:
            self.update_lbl.config(text='Checking for update...')
            latest_version = request.urlopen('https://github.com/laggykiller/MoticDownloader/raw/main/VERSION').read().decode('utf-8').replace('\n','')
            if current_version != latest_version:
                self.update_lbl.configure(text='Latest: ' + str(latest_version), fg='red')
            else:
                self.update_lbl.configure(text='Up to date', fg='green')

    def ActionCD(self):
        self.downloadpath_ent.delete(0, 'end')
        self.downloadpath_ent.insert(0, filedialog.askdirectory())

    def ActionGithub(self):
        webbrowser.open_new('https://github.com/laggykiller/MoticDownloader')

    def ActionSaveconf(self):
        global username, password, checkupdate, downloadpath, defaultzoom, defaultrotation, defaulttrim, loginsuffix
        downloadpath = self.downloadpath_ent.get()
        if not os.access(downloadpath, os.W_OK) and downloadpath != '':
            messagebox.showwarning(title='MoticDownloader', message='Cannot write in download path specified. Choose another one.')
            return
        checkupdate = self.checkupdate_var.get()
        defaultzoom = self.defaultzoom_scale.get()
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
        ConfigSave()
        self.StartScreen()

    def ActionDefaultconf(self):
        ConfigDefault()
        self.SettingsScreen()

    def ActionStartSubmit(self):
        global br, domain, username, password
        self.urls_txt.configure(state='disabled')
        self.username_ent.configure(state='disabled')
        self.password_ent.configure(state='disabled')
        self.rememberme_chk.configure(state='disabled')
        target_urls = self.urls_txt.get('1.0', 'end').replace(' ', '').split('\n')
        while('' in target_urls):
            target_urls.remove('')
        # Create slides objects
        self.target_objs = []
        for target_url in target_urls:
            self.target_objs.append(MoticSlide(target_url))
        username = self.username_ent.get()
        password = self.password_ent.get()
        try:
            domain = 'http://' + urlparse(target_urls[0]).netloc
        except:
            messagebox.showwarning(title='MoticDownloader', message='Please enter URL of slides')
            self.urls_txt.configure(state='normal')
            self.username_ent.configure(state='normal')
            self.password_ent.configure(state='normal')
            self.rememberme_chk.configure(state='normal')
            return
        # Login
        try:
            br.open(str(domain) + str(loginsuffix))
        except:
            messagebox.showwarning(title='MoticDownloader', message='Failed to visit ' + str(domain) + str(loginsuffix) + '\nMake sure you have internet connection and URL is correct')
            self.urls_txt.configure(state='normal')
            self.username_ent.configure(state='normal')
            self.password_ent.configure(state='normal')
            self.rememberme_chk.configure(state='normal')
            return
        if 'Sign in successful' in BeautifulSoup(br.response().read(), features='lxml').get_text():
            self.FetchinfoScreen()
            return
        br.select_form(nr=0)
        br.form['username'] = username
        br.form['password'] = password
        br.submit()
        if self.rememberme_var.get() == True:
            ConfigSave()
        else:
            username = ''
            password = ''
            ConfigClearcred()
        if 'Sign in successful' in BeautifulSoup(br.response().read(), features='lxml').get_text():
            self.FetchinfoScreen()
            return
        else:
            messagebox.showwarning(title='MoticDownloader', message='Login failed. Check URL, login name and password')
            self.urls_txt.configure(state='normal')
            self.username_ent.configure(state='normal')
            self.password_ent.configure(state='normal')
            self.rememberme_chk.configure(state='normal')
            return

    def ActionFetchinfo(self):
        # Fetch info about slides
        # Dictionary key is slide name, value is slide object
        self.loading_lbl.config(text='Getting slides info (0' + '/' + str(len(self.target_objs)) + ')')
        self.target_objs_dict = {}
        n = 0
        invalids = []
        for target_obj in self.target_objs:
            n += 1
            if target_obj.FetchInfo():
                self.target_objs_dict[target_obj.name] = target_obj
            else:
                invalids.append(target_obj)
            self.loading_lbl.config(text='Getting slides info (' + str(n) + '/' + str(len(self.target_objs)) + ')')
            self.loading_bar['value'] += 100 / len(self.target_objs)
        for item in invalids:
            self.target_objs.remove(item)
        self.PreviewScreen()

    def ActionGetslideconf(self, *args):
        global rect_id
        global topy, topx, botx, boty
        selection = self.listbox.get(self.listbox.curselection()[0])
        try:
            self.timg_canvas.delete('all')
        except:
            pass
        if selection == '(All slides)':
            self.trim_menu.destroy()
            self.trim_menu = OptionMenu(self.frame_prop, self.trim_var, 'Auto', 'None')
            self.trim_menu.config(width=5)
            self.trim_menu.grid(column=1, row=6, sticky='e')
            self.timg_canvas.config(width=256, height=256)
            self.timg_canvas.itemconfig(self.timg_canvas.create_text(90,120,anchor='nw'), text='(All slides)')
            self.name_lbl.config(text='Name: (All slides)')
            zooms = []
            rotations = []
            trims = []
            for slide in self.target_objs_dict.values():
                zooms.append(slide.zoom)
                rotations.append(slide.rotation)
                trims.append(slide.trim_mode)
            if len(set(zooms)) == 1:
                self.zoom_scale.set(zooms[0])
            if len(set(rotations)) == 1:
                self.rotation_var.set(rotations[0])
            else:
                self.rotation_var.set('*')
            if len(set(trims)) == 1:
                if trims[0] == 0:
                    self.trim_var.set('None')
                    self.pos_lbl1.config(text='(None)')
                elif trims[0] == 1:
                    self.trim_var.set('Auto')
                    self.pos_lbl1.config(text='(Auto)')
                else:
                    self.trim_var.set('*')
                    self.pos_lbl1.config(text='*')
            else:
                self.trim_var.set('*')
                self.pos_lbl1.config(text='*')
            self.timg_canvas.config(cursor='')
        else:
            self.trim_menu.destroy()
            self.trim_menu = OptionMenu(self.frame_prop, self.trim_var, 'Auto', 'Manual', 'None')
            self.trim_menu.config(width=5)
            self.trim_menu.grid(column=1, row=6, sticky='e')
            self.timg = self.target_objs_dict[selection].timg
            self.timg_draw = ImageTk.PhotoImage(self.timg)
            self.timg_canvas.config(width=self.timg.size[0],height=self.timg.size[1])
            self.timg_canvas.create_image(0,0, anchor='nw', image=self.timg_draw)
            self.timg_canvas.image = self.timg_draw
            self.name_lbl.config(text='Name: ' + str(self.target_objs_dict[selection].name))
            self.zoom_scale.set(int(self.target_objs_dict[selection].zoom))
            self.rotation_var.set(int(self.target_objs_dict[selection].rotation))
            if self.target_objs_dict[selection].trim_mode == 0:
                self.trim_var.set('None')
                self.pos_lbl1.config(text='(None)')
            elif self.target_objs_dict[selection].trim_mode == 1:
                self.trim_var.set('Auto')
                self.pos_lbl1.config(text='(Auto)')
            elif self.target_objs_dict[selection].trim_mode == 2:
                self.trim_var.set('Manual')
                r = self.target_objs_dict[selection].trimrange_timg
                self.pos_lbl1.config(text='(' + str(min(r[0],r[1])) + ',' + str(min(r[2],r[3])) + ') to (' + str(max(r[0],r[1])) + ',' + str(max(r[2],r[3])) + ')')
            else:
                self.trim_var.set('*')
                self.pos_lbl1.config(text='*')
            rect_id = self.timg_canvas.create_rectangle(topx, topy, topx, topy, dash=(2,2), fill='', outline='white')
            self.timg_canvas.bind('<Button-1>', self.get_mouse_posn)
            self.timg_canvas.bind('<B1-Motion>', self.update_sel_rect)
            self.timg_canvas.config(cursor='tcross')

    def ActionSetslideconf(self, *args):
        selection = self.listbox.get(self.listbox.curselection()[0])
        if self.trim_var.get() == 'None':
            trim = 0
        elif self.trim_var.get() == 'Auto':
            trim = 1
        elif self.trim_var.get() == 'Manual':
            trim = 2
        if selection == '(All slides)':
            for slide in self.target_objs_dict.values():
                slide.zoom = int(self.zoom_scale.get())
                slide.rotation = int(self.rotation_var.get())
                if trim != 2:
                    slide.trim_mode = int(trim)
        else:
            self.target_objs_dict[selection].zoom = int(self.zoom_scale.get())
            self.target_objs_dict[selection].rotation = int(self.rotation_var.get())
            self.target_objs_dict[selection].trim_mode = int(trim)
            self.target_objs_dict[selection].trimrange_timg = [min(botx,topx), max(botx,topx), min(boty,topy), max(boty,topy)]
        self.ActionGetslideconf()

    def ActionDownload(self, *args):
        n = 0
        for slide in self.target_objs_dict.values():
            n += 1
            self.loading_bar.config(mode='indeterminate')
            self.loading_bar.start(50)
            self.loading_lbl0.config(text='Slide name: ' + str(slide.name) + ' (' + str(n) + '/' + str(len(self.target_objs_dict)) + ')')
            self.loading_lbl1.config(text='Action: Fetch size of slide')
            slide.FetchSize()
            self.loading_lbl1.config(text='Action: Set download range')
            slide.SetRange()
            self.loading_lbl1.config(text='Action: Downloading tiles')
            self.loading_bar.stop()
            self.loading_bar.config(mode='determinate')
            slide.Download()
            self.loading_bar['value'] = 0
            self.loading_bar.config(mode='indeterminate')
            self.loading_bar.start(50)
            self.loading_lbl1.config(text='Action: Trimming')
            slide.Trim()
            self.loading_lbl1.config(text='Action: Rotating')
            slide.Rotate()
            self.loading_lbl1.config(text='Action: Saving')
            slide.Save()
        self.FinishScreen()

    def get_mouse_posn(self, event):
        global topy, topx
        topx, topy = event.x, event.y

    def update_sel_rect(self, event):
        global rect_id
        global topy, topx, botx, boty
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
        if self.listbox.get(self.listbox.curselection()[0]) != '(All slides)':
            self.trim_var.set('Manual')
            self.pos_lbl1.config(text='(' + str(min(botx,topx)) + ',' + str(min(boty,topy)) + ') to (' + str(max(botx,topx)) + ',' + str(max(boty,topy)) + ')')

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
ConfigLoad()

latest_version = None
topx, topy, botx, boty = 0, 0, 0, 0
rect_id = None

# Initialize browser
cj = cookielib.CookieJar()
br = mechanize.Browser()
br.set_cookiejar(cj)

# Start GUI
root = Tk()
gui = AppGUI(root)
root.mainloop()
exit()
