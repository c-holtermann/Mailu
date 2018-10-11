#!/usr/bin/python

import jinja2
from jinja2 import environment
import os
import time
import shutil
import re
import socket
import glob
import subprocess
import sys

# Custom filter method
def regex_replace(s, find, replace):
    """A non-optimal implementation of a regex filter"""
    return re.sub(find, replace, s)

environment.DEFAULT_FILTERS['regex_replace'] = regex_replace

def runBashCommand(bashCommand):
    print(">>" + bashCommand)
    returncode = subprocess.call(bashCommand.split())
    if returncode:
    	print(">> returncode: " + str(returncode))
    return returncode

def runBashCommands(bashCommands):
    for bashCommand in bashCommands:
        runBashCommand(bashCommand)

convert = lambda src, dst: open(dst, "w").write(jinja2.Template(open(src).read()).render(**os.environ))

# Actual startup script
os.environ["FRONT_ADDRESS"] = socket.gethostbyname(os.environ.get("FRONT_ADDRESS", "front"))
os.environ["HOST_ANTISPAM"] = os.environ.get("HOST_ANTISPAM", "antispam:11332")
os.environ["HOST_LMTP"] = os.environ.get("HOST_LMTP", "imap:2525")

os.environ["SYMPADATADIR"] = "/data/sympa"

convert("/conf/rsyslog/rsyslog.conf", "/etc/rsyslog.conf")

#postfix
for postfix_file in glob.glob("/conf/postfix/*.cf"):
    convert(postfix_file, os.path.join("/etc/postfix", os.path.basename(postfix_file)))

for postfix_file in glob.glob("/tmp/overrides/*.cf"):
    convert(postfix_file, os.path.join("/overrides", os.path.basename(postfix_file)))

for postfix_file in glob.glob("/tmp/overrides/*.map"):
    convert(postfix_file, os.path.join("/overrides", os.path.basename(postfix_file)))

runBashCommands(["usr/lib/postfix/post-install meta_directory=/etc/postfix create-missing",
	"/usr/lib/postfix/master &"])

# sympa
convert("/conf/sympa/sympa.conf", "/conf/sympa/sympa.conf.out")
with open("/etc/sympa/sympa.conf", "a") as fo:
    with open("/conf/sympa/sympa.conf.out", "r") as fi: 
        fo.write(fi.read())

sysconfdir = "/home/sympa/etc/"
listdomain = os.environ.get('DOMAIN')
expldir = os.environ["SYMPADATADIR"] + "/list_data/"
sympadatadir = os.environ["SYMPADATADIR"]

shutil.copyfile("/conf/sympa/list_aliases.tt2", sysconfdir + "/list_aliases.tt2") # $SYSCONFDIR

runBashCommands([ "mkdir " + os.environ["SYMPADATADIR"],
        "mkdir " + os.environ["SYMPADATADIR"] + "/spool",
        "mkdir " + os.environ["SYMPADATADIR"] + "/list_data",
        "mkdir " + os.environ["SYMPADATADIR"] + "/arc",
        "touch " + os.environ["SYMPADATADIR"] + "/sympa.db",
        "chown sympa:sympa " + os.environ["SYMPADATADIR"],
        "chown sympa:sympa " + os.environ["SYMPADATADIR"] + "/spool",
        "chown sympa:sympa " + os.environ["SYMPADATADIR"] + "/list_data",
        "chown sympa:sympa " + os.environ["SYMPADATADIR"] + "/arc",
        "chown sympa:sympa " + os.environ["SYMPADATADIR"] + "/sympa.db",
        "chmod a+w " + os.environ["SYMPADATADIR"],
        "touch " + sysconfdir +  "transport.sympa",
	"touch " + sysconfdir + "virtual.sympa",
	"touch " + os.environ["SYMPADATADIR"] + "/sympa_transport",
	"chmod 640 " + os.environ["SYMPADATADIR"] + "/sympa_transport",
	"chown sympa:sympa " + os.environ["SYMPADATADIR"] + "/sympa_transport",
	"postmap hash:" + sysconfdir + "transport.sympa",
	"postmap hash:" + sysconfdir + "virtual.sympa",
	"/home/sympa/bin/sympa_newaliases.pl",
	"mkdir -m 755 " + os.environ["SYMPADATADIR"] + "/" + listdomain,
	"touch " + os.environ["SYMPADATADIR"] + "/" + listdomain + "/robot.conf",
	"chown -R sympa:sympa " + os.environ["SYMPADATADIR"] + "/" + listdomain,
	"mkdir -m 750 " + expldir + listdomain,
 	"chown sympa:sympa " + expldir + listdomain
])

convert("/conf/sympa/transport.sympa", "/conf/sympa/transport.sympa.out")
with open(sysconfdir + "transport.sympa", "a") as fo:
    with open("/conf/sympa/transport.sympa.out", "r") as fi: 
        fo.write(fi.read())

convert("/conf/sympa/virtual.sympa", "/conf/sympa/virtual.sympa.out")
with open(sysconfdir + "virtual.sympa", "a") as fo:
    with open("/conf/sympa/virtual.sympa.out", "r") as fi: 
        fo.write(fi.read())

runBashCommands(["postmap hash:" + sysconfdir + "transport.sympa",
	"postmap hash:" + sysconfdir + "virtual.sympa"])
shutil.copyfile(os.path.join(sysconfdir, "virtual.sympa"), os.path.join(sympadatadir, "virtual.sympa"))
shutil.copyfile(os.path.join(sysconfdir, "virtual.sympa.db"), os.path.join(sympadatadir, "virtual.sympa.db"))

#apache2
convert("/conf/apache2/httpd_append.conf", "/conf/apache2/httpd_append.conf.out")
convert("/conf/apache2/sympa.conf", "/etc/apache2/conf.d/sympa.conf")
convert("/conf/apache2/proxy.conf", "/etc/apache2/conf.d/proxy.conf")

with open("/etc/apache2/httpd.conf", "a") as fo:
    with open("/conf/apache2/httpd_append.conf.out", "r") as fi: 
        fo.write(fi.read())

runBashCommands(["postmap hash:" + sysconfdir + "transport.sympa",
	"postmap hash:" + sysconfdir + "virtual.sympa",
	"/home/sympa/bin/sympa.pl --health_check"])

# transport rules for global postfix
with open("/overrides/sympa_transport.map", "w") as fo:
    fo.write("#this file will get overwritten each time sympa container is being rebuilt - don't edit !")
    fo.write("#file has been translated from " + os.environ["SYMPADATADIR"] + "/sympa_transport")
    with open(os.environ["SYMPADATADIR"] + "/sympa_transport", "r") as fi:
        lines = fi.readlines()
        for line in lines:
            if line.find("transport map") != -1:
                maildomain = line.split()[1]
                (mail, domain) = maildomain.split("@")
                # output headline
                fo.write(line)
            elif not (line[0] in ['#',' ']):
                (source, destination) = line.split()
                (sourcemail, sourcedomain) = source.split("@")
                if sourcedomain == domain:
                    outline = source + " " + "smtp:" + os.environ["COMPOSE_PROJECT_NAME"] + "_mailinglist_1"
                    # write transport line
                    fo.write(outline + "\n")

# flush buffer when giving over log to init system and rsyslog
sys.stdout.flush()

os.execl("/sbin/init", "/sbin/init")
