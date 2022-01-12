#!/usr/bin/env python
# -*- coding: utf-8 -*-
################################################################################
##
## Project: NextGIS Borsch build system
## Author: Dmitry Baryshnikov <dmitry.baryshnikov@nextgis.com>
##
## Copyright (c) 2017-2022 NextGIS <info@nextgis.com>
## License: GPL v.2
##
## Purpose: Post processing script
################################################################################

import fileinput
import os
import sys
import shutil
import subprocess

cmake_src_path = os.path.join(sys.argv[1], 'CMakeLists.txt')

if not os.path.exists(cmake_src_path):
    exit('Parse path not exists')

utilfile = os.path.join(os.getcwd(), os.pardir, 'cmake', 'util.cmake')

# Get values
_major = "0"
_minor = "0"
_rev = "0"

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    OKGRAY = '\033[0;37m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    DGRAY='\033[1;30m'
    LRED='\033[1;31m'
    LGREEN='\033[1;32m'
    LYELLOW='\033[1;33m'
    LBLUE='\033[1;34m'
    LMAGENTA='\033[1;35m'
    LCYAN='\033[1;36m'
    WHITE='\033[1;37m'

def extract_value(text):
    val_text = text.replace("set(QTKEYCHAIN_VERSION", "")
    val_text = val_text.replace(")", "")
    val_text = val_text.strip()
    val_text = val_text.split(".")
    return val_text[0], val_text[1], val_text[2]

def color_print(text, bold, color):
    if sys.platform == 'win32':
        print (text)
    else:
        out_text = ''
        if bold:
            out_text += bcolors.BOLD
        if color == 'GREEN':
            out_text += bcolors.OKGREEN
        elif color == 'LGREEN':
            out_text += bcolors.LGREEN
        elif color == 'LYELLOW':
            out_text += bcolors.LYELLOW
        elif color == 'LMAGENTA':
            out_text += bcolors.LMAGENTA
        elif color == 'LCYAN':
            out_text += bcolors.LCYAN
        elif color == 'LRED':
            out_text += bcolors.LRED
        elif color == 'LBLUE':
            out_text += bcolors.LBLUE
        elif color == 'DGRAY':
            out_text += bcolors.DGRAY
        elif color == 'OKGRAY':
            out_text += bcolors.OKGRAY
        else:
            out_text += bcolors.OKGRAY
        out_text += text + bcolors.ENDC
        print (out_text)

with open(cmake_src_path) as f:
    for line in f:
        if "set(QTKEYCHAIN_VERSION" in line:
            _major, _minor, _rev = extract_value(line)
            break

for line in fileinput.input(utilfile, inplace = 1):
    if "set(MAJOR_VERSION " in line:
        print ("    set(MAJOR_VERSION " + _major + ")")
    elif "set(MINOR_VERSION " in line:
        print ("    set(MINOR_VERSION " + _minor + ")")
    elif "set(REV_VERSION " in line:
        print ("    set(REV_VERSION " + _rev + ")")
    else:
        print (line),

# overwrite files
ovr_path = os.path.join(os.getcwd(), 'overwrite')
if os.path.exists(ovr_path):
    dst_path = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
    for dirname, dirnames, filenames in os.walk(ovr_path):
        for filename in filenames:
            src_file = os.path.join(ovr_path, dirname, filename)
            dst_file = src_file.replace(ovr_path, dst_path)
            if not filename.startswith("."):
                color_print("Overwrite " + dst_file, False, 'LRED')
                shutil.copyfile(src_file, dst_file)

# patch files
patches_path = os.path.join(os.getcwd(), 'patches')
if os.path.exists(patches_path):
    for dirname, dirnames, filenames in os.walk(patches_path):
        for patch in filenames:
            color_print("Patch " + patch, False, 'LRED')
            subprocess.call(['git', 'apply', os.path.join(patches_path, patch)], cwd = "../")
