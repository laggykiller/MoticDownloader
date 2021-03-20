from setuptools import setup

APP = ['./MoticDownloader.py']
DATA_FILES = [
    ('icon', ['icon'])
]
OPTIONS = {
    'packages':['PIL',],
    'iconfile': 'icon/app.icns'
}

setup(
    app=APP,
    name='MoticDownloader-MacOS',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
