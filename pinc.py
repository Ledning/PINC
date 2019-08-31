#!/usr/bin/env python3

import argparse
import os
import sys
import subprocess
import threading
import urllib
from enum import Enum
from pathlib import Path
from subprocess import PIPE

import requests
from bs4 import BeautifulSoup
from packaging import version


class PkgVer(Enum):
    error = -1
    newer = 0
    uptodate = 1
    outofdate = 2


home = str(Path.home())
config_file_location = home + "/.config/pinc/pinc.conf"
run_list = []

configuration = {
    'repository': "https://aur.archlinux.org/packages/",
    'local_path': home + "/.Packages",
    'make_flags': "-sir",
    'threads': 10,
    'ignore_list': []
}


def main():
    if not args_validator():
        parse.print_help()
        exit()
    config_parser()

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
    if len(run_list) > 0:
        for pkg in run_list:
            make_pkg(pkg)

    if args.clean_flag:
        p = subprocess.Popen(["rm", "-rf", configuration['local_path'] + "/"], stdin=PIPE, stdout=PIPE)
        p.wait(2)
        os.mkdir(configuration['local_path'])


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


def config_parser():
    global configuration
    if not os.path.isfile(config_file_location):
        error("Config was not found. Using default settings.")
        return

    with open(config_file_location) as f:
        for line in f:
            line = line.strip()
            line = line.rstrip("\n")

            if line.startswith("#") or len(line) < 2:
                continue

            key, value = line.split("=")
            if key == "REPOSITORY":
                configuration['repository'] = value
            elif key == "LOCALPATH":
                if value.startswith("/"):
                    configuration['local_path'] = value
                else:
                    configuration['local_path'] = home + "/" + value
            elif key == "MAKESETTINGS":
                configuration['make_flags'] = value
            elif key == "THREADS":
                try:
                    configuration['threads'] = int(value)
                except:
                    if args.verbose_flag:
                        print("Thread value invalid. Using default (10).")
            elif key == "IGNORELIST":
                configuration['ignore_list'] = value.split(" ")


def args_validator():
    if len(sys.argv) < 2:
        return False

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
    link = "https://aur.archlinux.org/" + pkg + ".git"

    if pkg == "":
        error("No package specified.", force=True, kill=True)
    try:
        os.mkdir(configuration['local_path'])
    except OSError:
        pass

    try:
        subprocess.run(["git", "-C", configuration['local_path'], "clone", link], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except:
        error("Can not download or find the directory | " + pkg, force=True, kill=True)

    if args.run_flag:
        run_list.append(pkg)


def search_pkg(query):
    link = configuration['repository'] + "?K=" + urllib.parse.quote(query)
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
        error("Could not search for package from aur.", force=True, kill=True)


def update_pkg():
    subprocess_response = subprocess.run(["pacman", "-Qm"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    packages = str(subprocess_response.stdout.decode("utf-8")).split("\n")
    package_list = []
    for pkg in packages:
        if pkg != "":
            package_list.append(pkg.split(" "))
    while len(package_list) > 0:
        if threading.active_count() - 1 < configuration['threads']:
            pkg = package_list.pop()
            threading.Thread(target=is_pkg_upstream, args=(pkg[0], pkg[1], args.download_flag)).start()
    while args.download_flag and threading.active_count() != 1:
        pass
    return True


def is_pkg_upstream(pkg, ver, download=False):
    link = configuration['repository'] + pkg
    try:
        response = requests.get(link)
        parsed_html = BeautifulSoup(response.text, "html.parser")
        newest_pkg = str(parsed_html.find_all("h2")[1]).replace("<h2>Package Details: ", "").replace("</h2>", "").split(" ")
        if version_compare(ver, newest_pkg[1]) == PkgVer.outofdate:
            print("{} {} --> {}".format(pkg, ver, newest_pkg[1]))
            if download:
                download_pkg(pkg)
    except Exception as e:
        error(e)
        error("Could not fetch package from aur. ::: " + pkg, force=True, kill=True)


def make_pkg(pkg):
    path = configuration['local_path'] + "/" + pkg
    os.chdir(path)
    try:
        p = subprocess.Popen(["makepkg", configuration['make_flags']])
        p.communicate()
        # TODO: Run this gpg --search-keys A2C794A986419D8A
    except:
        error("\033[1;31mPINC :::     \033[0mFailed to build pkg")


def version_compare(local, upstream):
    if version.parse(local) == version.parse(upstream):
        return PkgVer.uptodate
    elif version.parse(local) < version.parse(upstream):
        return PkgVer.outofdate
    elif version.parse(local) > version.parse(upstream):
        return PkgVer.newer
    else:
        return PkgVer.error


def error(message, force=False, kill=False):
    # err_color_start = "\033[1;31m", err_color_end = "\033[0m"
    if force or args.verbose_flag:
        print(message)
    if kill:
        exit()


parse, args = parser()
if __name__ == "__main__":
    main()

