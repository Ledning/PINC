#!/usr/bin/env python3

import argparse
import subprocess
import requests
from bs4 import BeautifulSoup
import os
import urllib
import threading
from enum import Enum
from pathlib import Path
import numbers
from subprocess import Popen,PIPE

default_config_location = str(Path.home()) + "/.config/pinc/pinc.conf"
home = str(Path.home())
repository = "https://aur.archlinux.org/packages/"
localpath = str(Path.home()) + "/.Packages"
makesettings = "-sir"
threads = 10
ignorelist = []
runlist = []


def configparser():
    global repository, localpath, makesettings, threads, ignorelist
    if not os.path.isfile(default_config_location):
        if args.verbose_flag:
            print("Config was not found. Using default settings.")
        return

    with open(default_config_location) as f:
        for line in f:
            if line.startswith("#") or len(line) < 2:
                continue
            key, value = line.split("=")
            if key == "REPOSITORY":
                repository = value.rstrip("\n")
            elif key == "LOCALPATH":
                if value.startswith("/"):
                    localpath = value.rstrip("\n")
                else:
                    localpath = str(Path.home()) + "/" + value.rstrip("\n")
            elif key == "MAKESETTINGS":
                makesettings = value.rstrip("\n")
            elif key == "THREADS":
                try:
                    threads = int(value.rstrip("\n"))
                except:
                    if args.verbose_flag:
                        print("Thread value invalid. Using default (10).")
            elif key == "IGNORELIST":
                ignorelist = value.rstrip("\n").split(" ")


class PkgVer(Enum):
    newer = 0
    uptodate = 1
    outofdate = 2


def parser():
    p = argparse.ArgumentParser(description="PINC Is Not Cower!")
    p.add_argument("-d", dest='download_flag', action='store_true', help='download package')
    p.add_argument("-s", dest='search_flag', action='store_true', help='Search for package in the aur repository')
    p.add_argument("-u", dest='update_flag', action='store_true', help='Check for updates')
    p.add_argument("-r", dest='run_flag', action='store_true', help='Make packages')
    p.add_argument('-v', dest='verbose_flag', action='store_true', help='Verbose output')
    p.add_argument('-c', dest='clean_flag', action='store_true', help='Clean package folder')
    p.add_argument('pkg', nargs='*', help='Package')
    return p, p.parse_args()


parse, args = parser()


def main():
    if not args_validator():
        parse.print_help()
        exit()
    configparser()

    if args.download_flag:
        if not args.update_flag:
            for pkg in args.pkg:
                download_pkg(pkg)
    if args.search_flag:
        query = ''.join(str(x) + " " for x in args.pkg)
        search_pkg(query)
    if args.update_flag:
        update_pkg()
    if args.run_flag:
        if not args.download_flag:
            for pkg in args.pkg:
                make_pkg(pkg)
    if len(runlist) > 0:
        for pkg in runlist:
            make_pkg(pkg)

    if args.clean_flag:
        p = subprocess.Popen(["rm", "-rf", localpath + "/"], stdin=PIPE, stdout=PIPE)
        p.wait(2)
        os.mkdir(localpath)


def args_validator():
    if args.search_flag and (args.download_flag or args.update_flag or args.run_flag):
        return False
    if args.download_flag and not (args.pkg or args.update_flag):
        return False
    if args.run_flag and not (args.download_flag or args.pkg):
        return False
    if args.clean_flag and args.download_flag and not args.run_flag:
        print("Okay... But why?")
    return True


def download_pkg(pkg):
    if pkg == "":
        print("No package specified.")
        exit()
    try:
        os.mkdir(localpath)
    except:
        pass

    link = "https://aur.archlinux.org/" + pkg + ".git"

    try:
        subprocess.run(["git", "-C", localpath, "clone", link], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except:
        print("Can not download or find the directory | " + pkg)
        exit()

    if args.run_flag:
        runlist.append(pkg)


def search_pkg(query):
    link = repository + "?K=" + urllib.parse.quote(query)
    try:
        response = requests.get(link)
        parsed_html = BeautifulSoup(response.text, "html.parser")
        parsed_query = parsed_html.find_all("tr")
        for x in parsed_query[1:]:
            y = x.find('td', attrs={'class': 'wrap'})
            print(x.a.contents[0] + ": " + str(y.text))
        if len(parsed_query) == 0:
            print("No packages found")
    except:
        print("Could not search for package from aur.")
        exit()


def update_pkg():
    subprocess_response = subprocess.run(["pacman", "-Qm"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    package = str(subprocess_response.stdout.decode("utf-8")).split("\n")
    packagelist = []
    for pkg in package:
        if pkg != "":
            packagelist.append(pkg.split(" "))
    while len(packagelist) > 0:
        if threading.active_count()-1 < threads:
            pkg = packagelist.pop()
            threading.Thread(target=is_pkg_uptodate, args=(pkg[0], pkg[1], args.download_flag)).start()
    while args.download_flag and threading.active_count() != 1:
        pass
    return True


def is_pkg_uptodate(pkg, ver, download=False):
    link = repository + pkg
    try:
        response = requests.get(link)
        parsed_html = BeautifulSoup(response.text, "html.parser")
        newestpkg = str(parsed_html.find_all("h2")[1]).replace("<h2>Package Details: ", "").replace("</h2>", "").split(" ")
        if ver < newestpkg[1]:
            print("{} {} --> {}".format(pkg, ver, newestpkg[1]))
            if download:
                download_pkg(pkg)
    except Exception as e:
        if args.verbose_flag:
            print(e)
        print("Could not fetch package from aur. ::: " + pkg)
        exit()


def make_pkg(pkg):
    path = localpath + "/" + pkg
    os.chdir(path)
    try:
        p = subprocess.Popen(["makepkg", makesettings])
        p.communicate()
        # TODO: Run this gpg --search-keys A2C794A986419D8A
    except:
        if args.verbose_flag:
            print("\033[1;31mPINC :::     \033[0mFailed to build pkg")


if __name__ == "__main__":
    main()
