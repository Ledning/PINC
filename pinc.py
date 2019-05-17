#!/usr/bin/env python3

import argparse
import subprocess
import requests
from bs4 import BeautifulSoup
import os

packagepath = "/tmp/package"


def parser():
    p = argparse.ArgumentParser(description="PINC Is Not Cower!")
    p.add_argument("-d", dest='download_flag', action='store_true', help='download package')
    p.add_argument("-s", dest='search_flag', action='store_true', help='Search for package in the aur repository')
    p.add_argument("-u", dest='update_flag', action='store_true', help='Check for updates')
    p.add_argument("-r", dest='run_flag', action='store_true', help='Make packages')
    return p, p.parse_args()


def main():
    parse, args = parser()
    download_pkg(args, "google-chrome")
    if args.download_flag:
        download_pkg(args, pkg)
    elif args.search_flag:
        search_pkg()
    elif args.update_flag:
        update_pkg(args)
    elif args.run_flag:
        make_pkg()
#    else:
#        parse.print_help()


def download_pkg(args, pkg):
    try:
        os.mkdir(packagepath)
    except:
        print("beep boop")
        pass

    link = "https://aur.archlinux.org/" + pkg + ".git"
    print(link)
    try:
        subprocess_response = subprocess.run(["git", "-C", packagepath, "clone", link], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if args.run_flag:
            make_pkg()
    except:
        print("Can not download or find the directory | " + pkg)
        exit()


def search_pkg():
    return


def update_pkg(args):
    subprocess_response = subprocess.run(["pacman", "-Qm"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    package = str(subprocess_response.stdout.decode("utf-8")).split("\n")
    packagelist = []
    for pkg in package:
        if pkg is not "":
            packagelist.append(pkg.split(" "))
    for x in packagelist:
        if check_package_for_update(x[0], x[1]):
            if args.download_flag:
                download_pkg(x[0])
            else:
                print(x[0])


def check_package_for_update(pkg, ver):
    link = "https://aur.archlinux.org/packages/" + pkg
    try:
        response = requests.get(link)
        parsed_html = BeautifulSoup(response.text, "html.parser")
        newestpkg = str(parsed_html.find_all("h2")[1]).replace("<h2>Package Details: ", "").replace("</h2>", "").split(" ")
        return newestpkg[1] is ver
    except:
        print("shit it's på danish")
        exit()

def make_pkg():
    return


if __name__ == "__main__":
    main()
