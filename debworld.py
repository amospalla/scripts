#!/usr/bin/env python

try:
    import apt
    import apt_pkg
except ImportError:
    print "Please install python-apt before running this software"
    sys.exit(0)
import os
import platform
import sys
import argparse
import re
import socket

if platform.machine() == 'x86_64':
    architecture = 'amd64'
else:
    print "Architecture not supported by " + sys.argv[0]
    sys.exit(1)

defaultfile = "/etc/world/" + socket.gethostbyaddr(socket.gethostname())[0]

parser = argparse.ArgumentParser(description='Package setup like gentoo\'s world file', version='0.01')
parser.add_argument('-n', '--dry-run', action='store_true', default=False, dest='dryrun', help='dry run')
parser.add_argument('-f', '--file', action='store', default=defaultfile , dest='file', help='definitions file')
arguments= parser.parse_args()

apt_cache = apt.Cache()

apt_pkg.init_config()
apt_pkg.init_system()
apt_pkg_cache = apt_pkg.Cache()
depcache = apt_pkg.DepCache(apt_pkg_cache)

packages = []
packagesautomatic = {}
packages_referenced = {}

def read_definitions(path):
    if os.path.isfile(path):
        try:
            file = open(path, 'r')
            for line in file:
                match_include = re.match('^\s*include\s*(\S*)\s*$', line)
                match_comment = re.match('^\s*#\s*|^\s*$', line)

                # load includes
                if match_include:
                    currentpath = os.path.realpath(path) 
                    read_definitions(currentpath[0:currentpath.rfind('/')+1] + match_include.group(1))

                # exclude comments
                elif not match_comment:
                    mode,package = line.split()
                    if not package in packages:
                        packages_referenced[package] = False
                        packages.append(package)
                        if mode.lower() == 'a':
                            packagesautomatic[package] = True
                        elif mode.lower() == 'm':
                            packagesautomatic[package] = False
                        else:
                            print "Error in package definitions file, mode for package '" + package + "' is '" + mode + "'"
                            print "Allowed modes are a(utomatic) or m(manual)"
                            sys.exit(1)
        except IOError:
            print "error opening file"
        finally:
            file.close()
    else:
        print "Error loading file '" + path + "', not a file"

##########
## Code ##
##########

read_definitions(path=arguments.file)

for package in apt_cache:

    name = package.name
    arch = depcache.get_candidate_ver(apt_pkg_cache[name]).arch
    if not (arch == 'all' or arch == architecture):
        continue

    essential = package.essential
    priority = depcache.get_candidate_ver(apt_pkg_cache[name]).priority
    automatic =  depcache.is_auto_installed(apt_pkg_cache[name])
    installed = package.is_installed

    # Essential/important packages
    if essential or priority < 3:
        if name in packages:
            print "Warning: package " + name + " included in definitions file, not needed"
            packages_referenced[name] = True
        if not installed:
            print arch
            if arguments.dryrun:
                print "! Essential/important package " + name + " not installed (priority:" + str(priority) + ")"
            else:
                print "\nInstall essential package " + name
                package.mark_install()

        elif automatic:
            if arguments.dryrun:
                print "! Essential/important package " + name + " automatic (priority:" + str(priority) + ")"
            else:
                print "\nMark essential package " + name + " manual"
                package.mark_auto(auto=False)

    # If package is installed (essential/important discarded)
    elif installed:
        if name not in packages:
            if not automatic:
                if arguments.dryrun:
                    print "! Package " + name + " not referenced and manual"
                else:
                    print "\nMark not referenced package " + name + " manual"
                    package.mark_auto(auto=True)
        else:
            packages_referenced[name] = True
            if packagesautomatic[name] and not automatic:
                if arguments.dryrun:
                    print "! Package " + name + " referenced as automatic but is manual"
                else:
                    print "\nMark referenced package " + name + " automatic"
                    package.mark_auto(auto=True)
            elif not packagesautomatic[name] and automatic:
                if arguments.dryrun:
                    print "! Package " + name + " referenced as manual but is automatic"
                else:
                    print "\nMark referenced package " + name + " manual"
                    package.mark_auto(auto=False)
 
    # only not installed or not essential/important packages
    elif name in packages:
        packages_referenced[name] = True
        if arguments.dryrun:
            print "! Package " + name + " referenced but not installed"
        else:
            print "\nInstall referenced package " + name
            package.mark_install()
            if packagesautomatic[name]:
                package.mark_auto(auto=True)
            else:
                package.mark_install(from_user=False)

if not arguments.dryrun: apt_cache.commit()

for package in packages:
    if packages_referenced[package] == False:
        print "Warning: " + package + " not referenced"
