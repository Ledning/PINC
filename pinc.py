#!/usr/bin/env python3

import argparse
import os
import sys
import subprocess
import json
import errno as ecode
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
config_file_location = home + "/.config/pinc/config"
run_list = []

configuration = {
    'repository': "https://aur.archlinux.org/",
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
            if len(args.pkg) > 0:
                for pkg in args.pkg:
                    make_pkg(pkg)
            else:
                run_all_packages()
    if len(run_list) > 0:
        for pkg in run_list:
            make_pkg(pkg)

    if args.clean_flag:
        p = subprocess.Popen(["rm", "-rf", configuration['local_path'] + "/"], stdin=PIPE, stdout=PIPE)
        p.wait(2)
        os.mkdir(configuration['local_path'])


def parser():
    p = argparse.ArgumentParser(description="PINC Is Not Cower!")
    p.add_argument("-a", dest='ask_flag', action='store_true', help='Selected operations')
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

            if line.strip().startswith("#") or len(line) < 2:
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
    if args.verbose_flag and len(sys.argv) < 3:
        return False
    if args.update_flag and args.pkg:
        return False
    if args.search_flag and (args.download_flag or args.update_flag or args.run_flag):
        return False
    if args.download_flag and not (args.pkg or args.update_flag):
        return False
    if args.run_flag and args.update_flag and not args.download_flag:
        return False
    if args.clean_flag and args.download_flag and not args.run_flag:
        error("Okay... But why?", force=True)
    return True


def download_pkg(pkg):
    link = configuration['repository'] + pkg + ".git"

    if pkg == "":
        error("No package specified.", force=True, kill=True)
    try:
        os.mkdir(configuration['local_path'])
    except OSError as e:
        if e.errno != ecode.EEXIST:
            if e.errno == ecode.EACCES:
                error("You do not have permission to write to your local path " + configuration['local_path'],
                      force=True, kill=True)
            elif e.errno == ecode.ENOSPC:
                error("You don't have enough space :(", force=True, kill=True)
            else:
                error("Unknown error creating directory")
    try:
        subprocess.run(["git", "-C", configuration['local_path'], "clone", link], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except:
        error("Can not download or find the directory | " + pkg, force=True, kill=True)

    if args.run_flag:
        run_list.append(pkg)


def search_pkg(query):
    link = configuration['repository'] + "packages/?K=" + urllib.parse.quote(query)
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
    subprocess_string = str(subprocess_response.stdout.decode("utf-8")).split("\n")

    local_packages = []
    link = configuration['repository'] + "rpc/?v=5&type=info"
    for local_package in subprocess_string:
        if local_package != "":
            local_packages.append(local_package.split(" "))
            link = link + "&arg[]=" + local_package.split(" ")[0]

    response = requests.get(link)
    if response.status_code < 200 or response.status_code > 299:
        error("Could not talk to AUR", force=True, kill=True)

    json_response = json.loads(response.text)
    outofdate = []
    for local_package in local_packages:
        for upstream_package in json_response['results']:
            if upstream_package["Name"] == local_package[0]:
                if version_compare(local_package[1], upstream_package["Version"]) == PkgVer.outofdate:
                    print("{} {} --> {}".format(upstream_package["Name"], local_package[1], upstream_package["Version"]))
                    if args.download_flag and not args.ask_flag:
                        download_pkg(local_package[0])
                    elif args.ask_flag:
                        outofdate.append(local_package[0])
    if len(outofdate) > 0:
        selective_download(outofdate)


def selective_download(packages):
    selection = select(packages)

    for index in selection:
        download_pkg(packages[int(index, 10) - 1])


def run_all_packages():
    packages = os.listdir(configuration['local_path'])
    if args.ask_flag:
        packages = select(packages)
    for package in packages:
        make_pkg(package)


def make_pkg(pkg):
    path = configuration['local_path'] + "/" + pkg
    os.chdir(path)
    try:
        p = subprocess.Popen(["makepkg", configuration['make_flags']])
        p.communicate()
        # TODO: Run this gpg --search-keys A2C794A986419D8A
    except:
        error("\033[1;31mPINC :::     \033[0mFailed to build pkg")


def select(packages):
    ret_val = []
    i = 0
    for package in packages:
        i = i + 1
        print(str(i) + ") " + package)

    print("Select the packages you want.")
    selection = input().split(" ")

    for index in selection:
        ret_val.append(packages[int(index, 10) - 1])
    return ret_val


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
