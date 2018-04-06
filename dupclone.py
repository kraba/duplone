#!/usr/bin/python

"""Duplone - automate duplicity & rclone

Version: 0.1-20180404

Description:

    Duplone is a script to automate duplicity & rclone backups who can help you
    to create/delete/verify backups trough cloud providers.

Author:

    Matteo Basso  < matteo.basso@gmail.com > < https://github.com/kraba >

License:

    Copyright (C) 2018 Matteo Basso

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import json
import sys
import os
import subprocess
import re
import gnupg
import logging
import logging.handlers
import datetime
import glob
import gzip


def logFile():
    """Initialize logger."""
    logname = 'duplone.log'
    logger = logging.getLogger("Duplone")
    """ DEBUG - INFO - ERROR """
    logger.setLevel(logging.INFO)
    """ Max logsize 5 mb """
    fh = logging.handlers.RotatingFileHandler(
                    logname, maxBytes=5242880, backupCount=10)
    formatter = logging.Formatter('%(asctime)s|%(levelname)s --> %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    """ Perform gzip on switched log - delete plain text"""
    switchedLog = glob.glob('%s*' % logname)
    for curs in range(1, 10):
        logToZip = logname+'.'+str(curs)
        if logToZip in switchedLog:
            with open(logToZip, 'rb') as switchedLog:
                with gzip.open(logToZip+'.gz', 'wb') as zipped_file:
                    zipped_file.writelines(switchedLog)
                    zipped_file.close()
                    os.unlink(logToZip)
    return logger


def jsonToDict(jsonfile):
    """Copy json key+value in a dict."""
    if os.path.isfile(jsonfile):
        with open(jsonfile) as data_file:
            data = json.load(data_file)
            logger.debug("JSON configuration file '%s' is present" % jsonfile)
            return data
    else:
        logger.error("JSON configuration file '%s' doesen't exists" % jsonfile)
        exit()


def binExists(executable):
    """Check if binary is present/installed on system."""
    process = subprocess.Popen(["which", executable], stdout=subprocess.PIPE)
    path = process.communicate()[0].rstrip()
    if path:
        logger.debug('Binary %s present' % path)
        return True, path


def setPass(passphrase, token):
    """Set the environment passphrase.Token = 1 set / Token = 0 unset."""
    if passphrase and token:
        logger.info("Passphrase setted in environment")
        os.environ['PASSPHRASE'] = str(passphrase)
    elif not passphrase and token:
        logger.error("Passphrase is empty in conf.json, exit!")
        exit()
    elif not passphrase and not token:
        logger.info("Passphrase unsetted in environment")
        os.environ['PASSPHRASE'] = str(passphrase)


def setCommand(command, origin, destination):
    """Launch some cheks and create the duplicity command."""
    confdict = data[origin][destination]

    """ Check if duplicity is installed on system """
    duplicityExists, duplicityPath = binExists('duplicity')
    if not duplicityExists:
        logger.error("The binary of duplicity is not installed! \
                    Install it before using this script")
        exit()

    """ Check if rclone is setted and it exists on system """
    using_rclone = confdict['using_rclone']
    rcloneExists, rclonePath = binExists('rclone')
    if using_rclone in ('Y', 'y', 'YES', 'yes', 'Yes') and rcloneExists:
        logger.debug("rclone flag is present")
        using_rclone = "rclone://"
    elif using_rclone in ('Y', 'y', 'YES', 'yes', 'Yes') and not rcloneExists:
        logger.error("The binary of rclone is not installed but required")
        logger.error("in conf.json (flagged as YES)! Check the JSON file!")
        exit()
    else:
        logger.debug("rclone is not present/required")
        using_rclone = ''

    """Search and check if encrypted key is present """
    gpg = gnupg.GPG()
    encryptkey = confdict['encryptkey']
    public_key = gpg.list_keys()
    if public_key:
        token = 0
        for key in range(0, len(public_key)):
            if encryptkey == public_key[key]['keyid'][8:]:
                logger.debug("Key %s found! GPG ready!" % encryptkey)
                token = 1
            if not token:
                logger.error("Key %s not found" % encryptkey)
                exit()
    else:
            logger.error("Keyring %s not found" % encryptkey)
            exit()

    """ Check if the excluded directory exists and add --exclude """
    exclude_dir = []
    for exclude_path in re.split("\s+", confdict["exclude_dir"]):
        if os.path.exists(exclude_path):
            logger.debug("Excluding directory : %s" % exclude_path)
            exclude_dir.extend(["--exclude", exclude_path])
        else:
            logger.info("Excluded directory '%s' doesn't exists" % exclude_path)

    """ Create correct string connection for the destination service
        If sftp/ftp/scp : require rclone not setted, sftp string connection
        If cloud storage : require rclone setted
    """
    dest_type = confdict['dest_type']
    dest_path = confdict['dest_path']
    if dest_type in ('hubic', 'HUBIC', 'Hubic'):
        pass
    elif dest_type in ('gdrive', 'gapps', 'gmail'):
        dest_path = ('/' + dest_path)
    elif dest_type in ('sftp', 'ftp', 'scp'):
        dest_path = ('/' + dest_path)
    else:
        logger.error("Destination service %s not supported" % dest_type)
    logger.info("Destination service: '%s'" % dest_type)

    classic_service = ['sftp', 'ftp', 'scp']
    only_sftp_string = confdict['only_sftp_string']
    if dest_type in classic_service and only_sftp_string and using_rclone:
        logger.error("Too many args in conf.json! Check it")
        logger.error("With %s 'using_rclone' must be empty" % dest_type)
        exit()
    if dest_type in classic_service and only_sftp_string:
        logger.debug("Duplicity'll run w/out rclone!%s connection" % dest_type)
        dest_type = (dest_type + '://' + only_sftp_string + ':')
    elif dest_type not in classic_service and using_rclone:
        logger.debug("Duplicity'll run with rclone!%s connection" % dest_type)
        dest_type = (dest_type + ':')

    """ Check if retention exists or set it to 5 full backup or 1 year"""
    retention_days = confdict['retention_days']
    retention_full = confdict['retention_full']
    if not retention_days:
        retention_days = '1Y'
        logger.debug("Retention not populated, setted to 1 year!")
    if not retention_full:
        retention_full = '5'
        logger.debug("Retention for full backup not populated, \
                    setted to 5 full backup")
    logger.debug("Retention days : %s" % retention_days)
    logger.debug("Retention full archive : %s" % retention_full)

    """ Set the env path """
    setPass(confdict['passphrase'], 1)

    """ Launch duplicity command """
    """Build the correct string to launch duplicity."""

    execThis = [duplicityPath, command]
    if command in ("incremental", "full"):
        execThis.extend(["--encrypt-key", str(encryptkey)])
        execThis.extend(exclude_dir)
        execThis.append(confdict['bck_path'])
    elif command == "collection-status":
        pass
    elif command == "remove-older-than":
        execThis.append(retention_days)
    elif command == "remove-all-but-n-full":
        execThis.extend([retention_full, "--force"])

    execThis.append("{}{}{}".format(using_rclone, dest_type, dest_path))
    process = subprocess.Popen(execThis, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    """  Output and error catch/print """
    (output_command, error_command) = process.communicate()
    logger.info("duplicity output:\n%s" % output_command)
    if error_command:
        logger.error("duplicity error:\n%s" % error_command)

    """ Unset the env path """
    setPass('', 0)
    return


line = '*' * 80
""" 0 argv : launch video help """
if len(sys.argv) == 1:
    print "Duplone - Duplicity and rclone script\n\
Version: 0.1 - 20180404 \n\n\
USAGE:\n\
\tduplone bck-full host service --> perform full backup\n\
\tduplone bck-incr host service --> perform incremental backup\n\
\tduplone status host service   --> show backups status\n\
\tduplone del-ret host service  --> delete backups (using retention)\n\
\tduplone del-all host service  --> delete all backups (except last N)\n"
    exit()
""" >=1 argv : script is starting"""
logger = logFile()
logger.info("\n%s\n* STARTING BACKUP OPERATIONS - %s\n%s"
            % (line, datetime.datetime.now().strftime("%Y%m%d-%H:%M"), line))
data = jsonToDict('conf.json')
""" 3 argv is correct...let's go"""
if len(sys.argv) == 4:
    """ argv1 is the command to call
        argv2 is the origin to send command
        argv3 is the destination service
    """
    logger.info("Type: %s | Source: %s | Destination: %s "
                % (sys.argv[1], sys.argv[2], sys.argv[3]))

    """Check if argv1 is correct/defined from default."""
    command = sys.argv[1]
    commList = ['bck-full', 'bck-incr', 'del-ret', 'del-all', 'status']
    if command in commList:
        logger.info("Argument %s is correct" % command)
        if command in commList[0]:
            command = 'full'
        elif command in commList[1]:
            command = 'incremental'
        elif command in commList[2]:
            command = 'remove-older-than'
        elif command in commList[3]:
            command = 'remove-all-but-n-full'
        elif command in commList[4]:
            command = 'collection-status'
    else:
        logger.error("Wrong value :'%s' is not valid" % command)
        exit()
    origin = sys.argv[2]
    destination = sys.argv[3]
    """ if origin are present in conf.json"""
    if origin in data:
        """ if argv3 is all perform command to all destination"""
        if destination == 'all':
            logger.info("Multiple selection - all destination")
            for multi_dest in data[origin]:
                logger.info("Multiple selection - working on %s" % multi_dest)
                setCommand(command, origin, multi_dest)
            """ if it's not all check if destination is correct written and
            perform command to destination """
        elif destination in data[origin]:
            logger.info("Destination: '%s'" % destination)
            setCommand(command, origin, destination)
            """ if it's bad written or not present...error """
        else:
            logger.error("Argument '%s' doesen't exists - check the name" % destination)
            exit()
    logger.info("\n%s\n* BACKUP OPERATIONS ENDED - %s\n%s"
                % (line, datetime.datetime.now().strftime("%Y%m%d-%H:%M"), line))
else:
    logger.error("OPS! Command line error: Expected 3 args, got %s " % len(sys.argv))
    exit()
