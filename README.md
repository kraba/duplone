# Duplone, automate duplicity & rclone

## Few words about duplicity & rclone

[duplicity](http://duplicity.nongnu.org/) *backs directories by producing encrypted tar-format volumes and uploading them to a remote or local file server.* It's a very good tool to produce backup! Nothing else.

[rclone](https://github.com/ncw/rclone) *is a command line program to sync files and directories to and from* cloud & non-cloud (storage) providers.

[duplicity-rclone](https://github.com/GilGalaad/duplicity-rclone) is a duplicity backend to using rclone, written by [Francesco Magno](https://github.com/GilGalaad).

## What's is duplone?

Duplone is a script to automate duplicity & rclone backups, written in Python, who can help you to create/delete/verify backups trough cloud providers.  Actually the code have only Hubic and Google Drive/Suite as service but you can easily modify the code and add it (and send to me a message, I'll update it).

Duplone read the configured `conf.json` file and launch a full or incremental backup, a full or partial delete of backups or read the status of backups trough duplicity.

The idea is to use three simple parameters to launch the desired function:
```sh
     duplone bck-full host service --> perform full backup
     duplone bck-incr host service --> perform incremental backup
     duplone status host service   --> show backups status
     duplone del-ret host service  --> delete backups (using retention)
     duplone del-all host service  --> delete all backups (except last N)
```
### JSON configuration file:
The JSON configuration file is like the one below, description of key/value trough quotation marks:
```json
{
  "my-host-desired-name":
    {
      "my-service-name" : {
      "dest_type": "put here your destination: hubic, gdrive or sftp",
      "dest_path": "destination path of hubic, gdrive or sftp",
      "bck_path" : "source path of backup",
      "encryptkey": "your encrypted key",
      "passphrase" : "your key passphrase",
      "exclude_dir" : "do you exclude a directory from backup?",
      "using_rclone" : "yes or not or empty",
      "retention_days" : "day of retention in M(months) D(days) or Y(year)",
      "retention_full" : "how many full backup to save",
      "only_sftp_string" : "user@host:port if you use sftp, otherwise empty"
        }
    }
}
```
A simple example of JSON configuration file is below. We want from our workstation to create a backup of:
 - home directory `/home/name` to hubic cloud storage in `/default/my-homedir` (without /default/ in hubic we can't see it on control panel). GPG key is ABC123C4 and the passphrase is myp4ssphr4s3. We also want to exclude to backup the directories `/home/name/tmp /home/name/var`.  Obviously we want to use rclone and we want a retention of 1 month for the full/incremental backup and at least 1 full backup always online.
 - `/var` directory to Google Drive/Suite in `bck-vardir`. GPG key is ABC123C4 and the passphrase is myp4ssphr4s3. We also want to exclude to backup the directories `/var/log /var/mail`. Obviously we want to use rclone and we want a retention of 3 month for the full/incremental backup and at least 2 full backup always online.

```json
{
  "myworkstation":
    {
      "homedir" : {
        "dest_type": "hubic",
        "dest_path": "/default/my-homedir",
        "bck_path" : "/home/name",
        "encryptkey": "ABC123C4",
        "passphrase" : "myp4ssphr4s3",
        "exclude_dir" : "/home/name/tmp /home/name/var",
        "using_rclone" : "yes",
        "retention_days" : "1M",
        "retention_full" : "1",
        "only_sftp_string" : ""
      },
      "vardir" : {
        "dest_type": "gdrive",
        "dest_path": "/bck-vardir",
        "bck_path" : "/var",
        "encryptkey": "ABC123C4",
        "passphrase" : "myp4ssphr4s3",
        "exclude_dir" : "/var/log /var/mail",
        "using_rclone" : "yes",
        "retention_days" : "3M",
        "retention_full" : "2",
        "only_sftp_string" : ""
        }
    }
}
```
Remember to save the `conf.json` file in the same directory of `duplone.py`.

### Launch duplone script
At the moment only five options are available:

 - **Full backup - create first backup** : `./duplone.py bck-full host service`, using the previously example:

   `./duplone.py bck-full myworkstation homedir`

   `./duplone.py bck-full myworkstation vardir`

   or launch script with `all` option as third argument and it execute all configured key presents on `conf.json`:

   `./duplone.py bck-full myworkstation all`

   If you launch it, a new full backup will be created on destination cloud storage.

 - **Incremental backup** : `./duplone.py bck-incr host service`, using the previously example:

   `./duplone.py bck-incr myworkstation homedir`

   `./duplone.py bck-incr myworkstation vardir`

   or launch script with `all` option as third argument and it execute all configured key presents on `conf.json`:

   `./duplone.py bck-incr myworkstation all`

   If you launch it, a new incremental backup will be created (and attach to the last full backup) on destination cloud storage.

 - **Status / Collection status of backups** : `./duplone.py status host service`, using the previously example:

   `./duplone.py status myworkstation homedir`

   `./duplone.py status myworkstation vardir`

   or launch script with `all` option as third argument and it execute all configured key presents on `conf.json`:

   `./duplone.py status myworkstation all`

   If you launch it, the collection status of backup will be written/reported to log file.

 - **Delete all full backups+incremental with retention flag** : `./duplone.py del-ret host service`, using the previously example:

   `./duplone.py del-ret myworkstation homedir`

   `./duplone.py del-ret myworkstation vardir`

   or launch script with `all` option as third argument and it execute all configured key presents on `conf.json`:

   `./duplone.py del-ret myworkstation all`

   If you launch it, all full backups (and incremental files attached) older than retention (1D, 1M, 1Y....) will be deleted. If you've only one full backup nothing will be delete.

  - **Delete all full backups+incremental except a number in retention flag** : `./duplone.py del-all host service`, using the previously example:

    `./duplone.py del-all myworkstation homedir`

    `./duplone.py del-all myworkstation vardir`

    or launch script with `all` option as third argument and it execute all configured key presents on `conf.json`:

     `./duplone.py del-all myworkstation all`

     If you launch it, all full backups (and incremental files attached) older than the last flagged (1,2 ...N) in conf.son will be deleted.

### Logging
Duplone have its log file, `duplone.log` . It contains all info and errors information, if you need to debug the script please change the `setLevel`of logger:
```python
logger.setLevel(logging.DEBUG)
```

An example of `duplone.log` is :

	(incremental backup)
    ********************************************************************************
    * STARTING BACKUP OPERATIONS - 20180406-15:07
    ********************************************************************************
    2018-04-06 15:07:17,378|INFO --> Type: bck-incr | Source: myworkstation | Destination: homedir
    2018-04-06 15:07:17,378|INFO --> Argument bck-incr is correct
    2018-04-06 15:07:17,378|INFO --> Destination: 'homedir'
    2018-04-06 15:07:17,404|INFO --> Destination service: 'hubic'
    2018-04-06 15:07:17,404|INFO --> Passphrase setted in environment
    2018-04-06 15:09:59,463|INFO --> duplicity output:
    Local and Remote metadata are synchronized, no sync needed.
    Last full backup date: Wed Apr  4 20:14:16 2018
    --------------[ Backup Statistics ]--------------
    StartTime 1523020051.19 (Fri Apr  6 15:07:31 2018)
    EndTime 1523020162.07 (Fri Apr  6 15:09:22 2018)
    ElapsedTime 110.88 (1 minute 50.88 seconds)
    SourceFiles 162818
    SourceFileSize 5733715706 (5.34 GB)
    NewFiles 121
    NewFileSize 34904932 (33.3 MB)
    DeletedFiles 31
    ChangedFiles 209
    ChangedFileSize 691008103 (659 MB)
    ChangedDeltaSize 0 (0 bytes)
    DeltaEntries 361
    RawDeltaSize 98231410 (93.7 MB)
    TotalDestinationSizeChange 41126565 (39.2 MB)
    Errors 0
    -------------------------------------------------
    2018-04-06 15:09:59,474|INFO --> Passphrase unsetted in environment
    2018-04-06 15:09:59,478|INFO -->
    ********************************************************************************
    * BACKUP OPERATIONS ENDED - 20180406-15:09
    ********************************************************************************

### Dependencies
You need a working environment with duplicty, rclone (with configured cloud providers), duplicity-rclone, GPG key configured with passphrase and python (with these libs : json, sys, os, subprocess, re, gnupg, logging, logging.handlers, datetime, glob, gzip).
Duplone check if duplicty and rclone are present, if GPG key is available and set/unset passphrase.


## To do list / Next features

 1. Integrate all know & working cloud providers
 2. Crypt the passphrase
 3. Restore trough command line
 4. Catching & managing duplicity error (network problems, cache corrupted...)
 5. Code fixing

## Author, version & license

Duplone was written by Matteo Basso during April 2018.

Code review/help by [Giuseppe Biolo](https://github.com/gbiolo)

Current version is : **0.1**

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
    along with this program.  If not, see https://www.gnu.org/licenses/.
