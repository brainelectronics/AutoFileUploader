#!/usr/local/bin/python2
# -*- coding: UTF-8 -*-
#

"""
This script will search at the given path, defined in the
config.json file, for files with a specific patter.
This is also defined in the config.json file.
By using the SSH credits defined in the loginData.json file
the specified files will be uploaded to a remote directory

Doing so can help to increase speed of providing OTA updates
on every build of a file.
The script should be extended to check for changes in the
predefined folder and trigger the upload automatically
"""

import datetime
import json
import pysftp
import os

__author__ = "Jonas Scharpf"
__copyright__ = "Copyright 2019, brainelectronics"
__version__ = "1.0.0"
__maintainer__ = "Jonas Scharpf"
__email__ = "jonas@brainelectronics.de"
__status__ = "Prototype"

# load host, username and password from config.json
with open('../afu/fileConfig.json') as json_data_file:
    configDataDict = json.load(json_data_file)

# refer to loginTemplate.json
with open('../afu/loginData.json') as json_data_file:
    loginDataDict = json.load(json_data_file)
# print(json.dumps(loginDataDict, indent=4, sort_keys=True))


myHostname = loginDataDict['sftp']['host']
myUsername = loginDataDict['sftp']['user']
myPassword = loginDataDict['sftp']['password']

# define the path where to search for files
localPath = configDataDict['server'][0]['localPath']
filePattern = configDataDict['server'][0]['pattern']
remoteFilePath = configDataDict['server'][0]['remotePath']
versionFile = configDataDict['server'][0]['version']
localFilePath = None
localFileName = None


print "searching at '%s'" %(localPath)
for file in os.listdir(localPath):
    if file.endswith(filePattern):
        localFileName = file
        localFilePath = os.path.join(localPath, file)
print "Found file called: '%s'" %(localFilePath)


print "Creating version file"
versionFilePath = os.path.join(localPath, versionFile)
with open(versionFilePath, "w") as aFile:
    epochDateTime = datetime.datetime.utcfromtimestamp(0)
    todayDateTime = datetime.datetime.today()
    daysSinceEpoch = (todayDateTime - epochDateTime).days
    aFile.write("%s" %(daysSinceEpoch))
# aFile.close()
print "File '%s' created" %(versionFilePath)


if localFilePath != None:
    print "Try to open connection..."
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    with pysftp.Connection(host=myHostname, username=myUsername, password=myPassword) as sftp:
        remoteFilePath = os.path.join(remoteFilePath, localFileName)

        print "Uploading file(s) to/as: %s" %(remoteFilePath)
        sftp.put(localpath=localFilePath, remotepath=remoteFilePath, confirm=False)
        sftp.put(localpath=versionFilePath, remotepath=remoteFilePath, confirm=False)
        # sftp.remove(remotefile=remoteFilePath)
        print "Upload done"

        print "Files found remote:"
        # change to a directory
        sftp.cwd(os.path.dirname(remoteFilePath))

        # Get the directory and file listing
        directories = sftp.listdir()

        # Prints out the directories and files, line by line
        for directory in directories:
            print "\t", directory

print "Done"
# connection is closed as we leave the with

