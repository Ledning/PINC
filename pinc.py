#!/usr/bin/env python3

import argparse
import subprocess
import requests
from bs4 import BeautifulSoup
import os
import urllib

packagepath = "/tmp/package"
makesettings = "-sir"


def parser():
    p = argparse.ArgumentParser(description="PINC Is Not Cower!")
    p.add_argument("-d", dest='download_flag', action='store_true', help='download package')
    p.add_argument("-s", dest='search_flag', action='store_true', help='Search for package in the aur repository')
    p.add_argument("-u", dest='update_flag', action='store_true', help='Check for updates')
    p.add_argument("-r", dest='run_flag', action='store_true', help='Make packages')
    p.add_argument('pkg', nargs='*', help='Package')
    return p, p.parse_args()


def main():
    parse, args = parser()
    if args.download_flag:
        for pkg in args.pkg:
            download_pkg(args, pkg)
    elif args.search_flag:
        query = ''.join(str(x) + " " for x in args.pkg)
        search_pkg(query)
    elif args.update_flag:
        update_pkg(args)
    elif args.run_flag:
        for pkg in args.pkg:
            make_pkg(pkg)
#    else:
#        parse.print_help()


def download_pkg(args, pkg):
    if pkg is "":
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
        make_pkg(pkg)


def search_pkg(query):
    link = "https://aur.archlinux.org/packages/?K=" + urllib.parse.quote(query)
    try:
        response = requests.get(link)
        parsed_html = BeautifulSoup(response.text, "html.parser")
        parsed_query = parsed_html.find_all("tr")
        for x in parsed_query[1:]:
            y = x.find('td', attrs={'class':'wrap'})
            print(x.a.contents[0] + ": " + str(y.text))
        if len(parsed_query) is 0:
            print("No packages found")
    except:
        print("Could not search for package from aur.")
        exit()


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
        print("Could not fetch package from aur.")
        exit()


def make_pkg(pkg):
    path = packagepath + "/" + pkg
    os.chdir(path)
    p = subprocess.Popen(["makepkg", makesettings])
    p.communicate()



if __name__ == "__main__":
    main()
