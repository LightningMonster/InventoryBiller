import PyInstaller.__main__
import os

PyInstaller.__main__.run([
    'src/main.py',
    '--name=BillingSystem',
    '--windowed',
    '--onedir',
    '--add-data=src/fixed_bill_generator.py;src',
    '--add-data=src/config.py;src',
    '--hidden-import=babel.numbers',
    '--clean',
    '--icon=assets/icon.ico',
    '--distpath=build'
])