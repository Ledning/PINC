#!/usr/bin/env python3

import argparse
import subprocess
from subprocess import check_output
import requests
from bs4 import BeautifulSoup
import os
import urllib
import threading
from enum import Enum

packagepath = "/home/usrname/package"
makesettings = "-sir"
threads = 10
runlist = []


class PkgVer(Enum):
    newer = 0
    uptodate = 1
    outofdate = 2


# def ver_comp(local, upstream):
#     if local == upstream:
#         return PkgVer.uptodate
#     localpt = local.lower().replace("+", ".").replace("-", ".").replace(";", ".").split(".")
#     upstreampt = upstream.lower().replace("+", ".").replace("-", ".").replace(";", ".").split(".")
#
#     while True:
#         if len(localpt) == 0 and len(upstreampt) == 0:
#             return PkgVer.uptodate
#         elif len(localpt) == 0:
#             return PkgVer.outofdate
#         elif len(upstreampt) == 0:
#             return PkgVer.newer
#         localpop = localpt.pop()
#         upstreampop = upstreampt.pop()
#
#         if localpop == upstreampop:
#             continue
#         if localpop < upstreampop:
#             return PkgVer.outofdate
#         if localpop > upstreampop:
#             return PkgVer.newer


def parser():
    p = argparse.ArgumentParser(description="PINC Is Not Cower!")
    p.add_argument("-d", dest='download_flag', action='store_true', help='download package')
    p.add_argument("-s", dest='search_flag', action='store_true', help='Search for package in the aur repository')
    p.add_argument("-u", dest='update_flag', action='store_true', help='Check for updates')
    p.add_argument("-r", dest='run_flag', action='store_true', help='Make packages')
    p.add_argument('-v', dest='verbose_flag',action='store_true', help='Verbose output')
    p.add_argument('pkg', nargs='*', help='Package')
    return p, p.parse_args()


parse, args = parser()


def main():
    if args.download_flag:
        if not args.update_flag:
            for pkg in args.pkg:
                download_pkg(pkg)
    if args.search_flag:
        if args.download_flag or args.update_flag or args.run_flag:
            parse.print_help()
            exit()
        query = ''.join(str(x) + " " for x in args.pkg)
        search_pkg(query)
    if args.update_flag:
        update_pkg()
    if args.run_flag:
        if args.update_flag and not args.download_flag:
            parse.print_help()
            exit()
        if not args.download_flag:
            for pkg in args.pkg:
                make_pkg(pkg)
    if len(runlist) > 0:
        for pkg in runlist:
            make_pkg(pkg)
    #  parse.print_help()


def download_pkg(pkg):
    if pkg == "":
        print("No package specified.")
        exit()
    try:
        os.mkdir(packagepath)
    except:
        pass

    link = "https://aur.archlinux.org/" + pkg + ".git"

    try:
        subprocess.run(["git", "-C", packagepath, "clone", link], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except:
        print("Can not download or find the directory | " + pkg)
        exit()

    if args.run_flag:
        runlist.append(pkg)


def search_pkg(query):
    link = "https://aur.archlinux.org/packages/?K=" + urllib.parse.quote(query)
    try:
        response = requests.get(link)
        parsed_html = BeautifulSoup(response.text, "html.parser")
        parsed_query = parsed_html.find_all("tr")
        for x in parsed_query[1:]:
            y = x.find('td', attrs={'class':'wrap'})
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
    link = "https://aur.archlinux.org/packages/" + pkg
    try:
        response = requests.get(link)
        parsed_html = BeautifulSoup(response.text, "html.parser")
        newestpkg = str(parsed_html.find_all("h2")[1]).replace("<h2>Package Details: ", "").replace("</h2>", "").split(" ")
        if ver < newestpkg[1]:
            print("{} {} --> {}".format(pkg, ver, newestpkg[1]))
            if download:
                download_pkg(pkg)
        # elif ver_comp(ver, newestpkg[1]) == PkgVer.newer and args.verbose_flag:
        #     print("\033[1;31mPINC :::     \033[0mLocal version is newer! " + ver + " | " + newestpkg[1])

    except Exception as e:
        print(e)
        print("Could not fetch package from aur. ::: " + link)
        exit()


def make_pkg(pkg):
    path = packagepath + "/" + pkg
    os.chdir(path)
    try:
        p = subprocess.Popen(["makepkg", makesettings])
        # p.communicate()
        p.communicate()
        # TODO: Run this gpg --search-keys A2C794A986419D8A
        # for line in p.stdout.readlines():
        #     print("A line")
        #     if "public key" in line:
        #         print("Oh my god we did it")

    except:
        if args.verbose_flag:
            print("\033[1;31mPINC :::     \033[0mFailed to build pkg")


if __name__ == "__main__":
    main()
