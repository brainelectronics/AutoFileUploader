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

from base64 import b64encode
import datetime
import json
import mechanize
import os
import pysftp
import requests
from stat import * # ST_SIZE etc
import time

__author__ = "Jonas Scharpf"
__copyright__ = "Copyright 2019, brainelectronics"
__version__ = "1.0.0"
__maintainer__ = "Jonas Scharpf"
__email__ = "jonas@brainelectronics.de"
__status__ = "Prototype"

class AutoFileUploader(object):
    """docstring for AutoFileUploader"""
    def __init__(self):
        super(AutoFileUploader, self).__init__()

        self.configFile = None
        self.loginFile = None
        self.configDataDict = dict()
        self.loginDataDict = dict()
        self.uploadFileList = list()
        self.uploadDeviceFile = None

    ##
    ## Sets the path to the configuration file.
    ##
    ## :param      theFile:  The file path
    ## :type       theFile:  JSON
    ##
    ## :returns:   Success of setting the file
    ## :rtype:     True on success, False otherwise
    ##
    def setConfigFile(self, theFile):
        returnValue = False

        if theFile:
            if os.path.isfile(theFile):
                self.configFile = theFile
                returnValue = True

        return returnValue

    ##
    ## Gets the path to the configuration file.
    ##
    ## :returns:   The configuration file.
    ## :rtype:     File path
    ##
    def getConfigFile(self):
        if self.configFile != None:
            return self.configFile

    ##
    ## Loads a config data to the config data dict.
    ##
    def loadConfigData(self):
        if self.configFile != None:
            self.configDataDict = self.loadConfigFile(theFile=self.getConfigFile())

    ##
    ## Gets the config data dictionary.
    ##
    ## :returns:   The config data dictionary.
    ## :rtype:     Dict
    ##
    def getConfigDataDict(self):
        return self.configDataDict

    ##
    ## Sets the path to the login configuration file.
    ##
    ## :param      theFile:  The file path
    ## :type       theFile:  JSON
    ##
    ## :returns:   Success of setting the file
    ## :rtype:     True on success, False otherwise
    ##
    def setLoginFile(self, theFile):
        returnValue = False

        if theFile:
            if os.path.isfile(theFile):
                self.loginFile = theFile
                returnValue = True

        return returnValue

    ##
    ## Gets the path to the login configuration file.
    ##
    ## :returns:   The configuration file.
    ## :rtype:     File path
    ##
    def getLoginFile(self):
        if self.loginFile != None:
            return self.loginFile

    ##
    ## Loads a login data to the login data dict.
    ##
    def loadLoginData(self):
        if self.loginFile != None:
            self.loginDataDict = self.loadConfigFile(theFile=self.getLoginFile())

    ##
    ## Gets the login data dictionary.
    ##
    ## :returns:   The login data dictionary.
    ## :rtype:     Dict
    ##
    def getLoginDataDict(self):
        return self.loginDataDict

    ##
    ## Loads a configuration file.
    ##
    ## :param      theFile:  The file
    ## :type       theFile:  JSON file
    ##
    ## :returns:   Dict of loaded JSON file
    ## :rtype:     Dict
    ##
    def loadConfigFile(self, theFile):
        loadedDict = dict()

        if (theFile != None) and (os.path.isfile(theFile)):
            with open(theFile) as aDataFile:
                loadedDict = json.load(aDataFile)

        return loadedDict

    ##
    ## Search for a file or patterns at the given path
    ##
    ## :param      searchPath:   The search path
    ## :param      filePattern:  The file pattern
    ## :param      theFile:      The explicit file
    ##
    ## :returns:   The full file path
    ## :rtype:     List
    ##
    def searchFile(self, searchPath, filePattern, theFile=None):
        fileList = list()

        for file in os.listdir(searchPath):
            matchingFile = None

            if not theFile:
                # user wants to search for a pattern
                if filePattern.upper() in file.upper():
                    matchingFile = file
            else:
                # user wants to search for a specific file
                if theFile.upper() == file.upper():
                    matchingFile = file

            if matchingFile != None:
                localFilePath = os.path.join(searchPath, matchingFile)
                fileList.append(localFilePath)

        return fileList

    ##
    ## Create list of files which are specified in the config file
    ## Map to dict with the upload path and the version file
    ##
    def findAllFilesForServer(self):
        if bool(self.configDataDict['server']):
            for file in self.configDataDict['server']:
                aFoundFileList = self.searchFile(
                    searchPath=file['localPath'],
                    filePattern=file['pattern'],
                    theFile=file['name'])

                if aFoundFileList:
                    # a file with the specified patter has been found
                    tmpDict = dict()
                    tmpDict['local'] = aFoundFileList
                    tmpDict['remote'] = file['remotePath']
                    tmpDict['version'] = file['version']
                    self.uploadFileList.append(tmpDict)

    ##
    ## Gets all found files.
    ##
    ## :returns:   All files.
    ## :rtype:     List of dict
    ##
    def getAllFilesForServer(self):
        return self.uploadFileList

    ##
    ## Create list of files which are specified in the config file
    ## Map to dict with the upload path and the version file
    ##
    def findFileForDevice(self):
        if bool(self.configDataDict['device']):
            deviceConfig = self.configDataDict['device']
            # print deviceConfig
            aFoundFile = self.searchFile(
                searchPath=deviceConfig['localPath'],
                filePattern=deviceConfig['pattern'],
                theFile=deviceConfig['name'])

            if aFoundFile:
                # a file with the specified patter has been found
                self.uploadDeviceFile = aFoundFile[0]

    ##
    ## Gets the file for device.
    ##
    ## :returns:   The file for device.
    ## :rtype:     file
    ##
    def getFileForDevice(self):
        return self.uploadDeviceFile

    ##
    ## Create a unique version file for each found file
    ##
    ## :param      timeBase:       The time base, either days since epoch or seconds
    ## :type       timeBase:       string
    ## :param      customContent:  A user given customContent, optional, e.g. a timestamp
    ## :type       customContent:  string
    ##
    def versionizeAllFilesForServer(self, timeBase='days', customContent=None):
        if self.uploadFileList:
            for file in self.uploadFileList:
                versionFileDirectory = os.path.dirname(file['local'][0])
                versionFileName = os.path.join(versionFileDirectory, file['version'])

                # print "want to create version file at: %s" %(versionFileDirectory)
                self.createVersionFile(filePath=versionFileName, timeBase=timeBase, customContent=customContent)

    ##
    ## Creates a version file.
    ##
    ## :param      filePath:  The full file path with name of the file
    ## :param      timeBase:  The time base, either days since epoch or seconds
    ## :type       timeBase:  string
    ## :param      timestamp: A user given custom content, optional, e.g. a timestamp
    ## :type       timestamp: string
    ##
    def createVersionFile(self, filePath, timeBase='days', customContent=None):
        if os.path.exists(os.path.dirname(filePath)):
            if customContent == None:
                epochDateTime = datetime.datetime.utcfromtimestamp(0)
                todayDateTime = datetime.datetime.today()

                if timeBase.lower() == "days":
                    # timestamp since epoch in days
                    versionFileContent = (todayDateTime - epochDateTime).days
                elif timeBase.lower() == "seconds":
                    # timestamp since epoch in seconds
                    versionFileContent = int(time.time())
            else:
                # user provided custom
                versionFileContent = customContent

            with open(filePath, "w") as aVersionFile:
                aVersionFile.write("%s" %(versionFileContent))

    ##
    ## Uploads all files to the server.
    ##
    def uploadAllFilesToServer(self):
        self.uploadFilesToServer(fileList=self.getAllFilesForServer())

    ##
    ## Check if SFTP login data are set
    ##
    ## :returns:   True on success, False otherwise
    ## :rtype:     bool
    ##
    def checkForSftpLoginData(self):
        returnValue = False

        dataDict = self.getLoginDataDict()['sftp']
        if dataDict:
            if dataDict['host'] and dataDict['user'] and dataDict['password']:
                returnValue = True

        return returnValue

    ##
    ## Check if ESP login data are set
    ##
    ## :returns:   True on success, False otherwise
    ## :rtype:     bool
    ##
    def checkForEspLoginData(self):
        returnValue = False

        dataDict = self.getLoginDataDict()['esp']
        if dataDict:
            if dataDict['url']:# and dataDict['user'] and dataDict['password']:
                # url is enough, username or password must not be set
                returnValue = True

        return returnValue

    ##
    ## Check for a valid setting of the login JSON file
    ##
    ## :param      service:  The service
    ## :type       service:  string
    ##
    ## :returns:   True on success, False otherwise
    ## :rtype:     bool
    ##
    def checkForValidLoginData(self, service):
        returnValue = False

        if service in self.getLoginDataDict().keys():
            if service.upper() == "sftp".upper():
                returnValue = self.checkForSftpLoginData()
            elif service.upper() == "esp".upper():
                returnValue = self.checkForEspLoginData()

        return returnValue

    ##
    ## Gets the file information.
    ##
    ## :param      theFile:  The file
    ## :type       theFile:  Path to a file
    ##
    ## :returns:   The file information.
    ## :rtype:     list
    ##
    def getFileInfo(self, theFile):
        fileData = None

        if os.path.exists(theFile):
            fileData = os.stat(theFile)

        return fileData

    ##
    ## Prints an upload information.
    ##
    ## :param      theFile:     The file
    ## :type       theFile:     Path to a file
    ## :param      fileNumber:  This file number
    ## :type       fileNumber:  integer
    ## :param      totalFiles:  The total number of files
    ## :type       totalFiles:  integer
    ##
    def printUploadInfo(self, theFile, fileNumber, totalFiles):
        fileData = self.getFileInfo(theFile=theFile)
        if fileData:
            print "Uploaded %d/%d (%1.1f%%) file '%s' (%dkB) " %(fileNumber, totalFiles, (fileNumber/float(totalFiles))*100.0, os.path.basename(theFile), fileData[ST_SIZE]/1000)

    ##
    ## Uploads a file to device.
    ##
    ## :param      theFile:  The file
    ## :type       theFile:  Path to a file
    ##
    def uploadFileToDevice(self, theFile):
        if self.checkForValidLoginData(service="esp") and (theFile != None):
            print "Establishing connection to ESP device..."

            espDataDict = self.getLoginDataDict()["esp"]

            b64login = b64encode('%s:%s' % (espDataDict['user'], espDataDict['password']))

            br = mechanize.Browser()

            br.addheaders.append(('Authorization', 'Basic %s' %(b64login)))

            # open(url_or_request, data=None, timeout=<object object>)[source]
            br.open(espDataDict['url'], timeout=10.0)

            br.select_form(nr=0)

            br.form.add_file(open(theFile,'r'))
            self.printUploadInfo(
                theFile=theFile,
                fileNumber=1,
                totalFiles=1)

            print "Wait until reboot is performed"

            # need to use try to catch HTTP 404 error after submission
            try:
                resp = br.submit()
            except Exception as e:
                pass

            print "Upload to device completed"

    def uploadFilesToServer(self, fileList):
        totalFilesToUpload = 0

        for ele in fileList:
            totalFilesToUpload += len(ele['local'])

            if len(ele['version']):
                # only count if version file is set
                totalFilesToUpload += 1

        if self.checkForValidLoginData(service="sftp"):
            print "Establishing connection to server..."

            sftpDataDict = self.getLoginDataDict()["sftp"]

            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None

            with pysftp.Connection(host=sftpDataDict['host'], username=sftpDataDict['user'], password=sftpDataDict['password']) as sftp:
                tmpFileUploadCounter = 0
                for fileDict in fileList:
                    for file in fileDict['local']:
                        # check for file to upload
                        if os.path.exists(file):
                            remoteFilePath = os.path.join(fileDict['remote'], os.path.basename(file))
                            # print "Uploading local '%s' to remote '%s'" %(file, remoteFilePath)

                            sftp.put(localpath=file, remotepath=remoteFilePath, confirm=False)

                            tmpFileUploadCounter += 1
                            self.printUploadInfo(
                                theFile=file,
                                fileNumber=tmpFileUploadCounter,
                                totalFiles=totalFilesToUpload)

                    # check for version file
                    localVersionFilePath = os.path.join(os.path.dirname(file), fileDict['version'])
                    if os.path.exists(localVersionFilePath):
                        remoteFilePath = os.path.join(fileDict['remote'], fileDict['version'])
                        # print "Uploading local '%s' to remote '%s'" %(fileDict['version'], remoteFilePath)

                        sftp.put(localpath=localVersionFilePath, remotepath=remoteFilePath, confirm=False)

                        tmpFileUploadCounter += 1
                        self.printUploadInfo(
                            theFile=localVersionFilePath,
                            fileNumber=tmpFileUploadCounter,
                            totalFiles=totalFilesToUpload)

            print "Upload to server completed"

if __name__ == '__main__':
    afu = AutoFileUploader()

    afu.setConfigFile(theFile='fileConfig.json')
    afu.setLoginFile(theFile='loginData.json')
    afu.loadConfigData()
    afu.loadLoginData()

    print "Login Data"
    print json.dumps(afu.getLoginDataDict(), indent=4, sort_keys=True)
    print "File Data"
    print json.dumps(afu.getConfigDataDict(), indent=4, sort_keys=True)


    # upload files to the server
    afu.findAllFilesForServer()
    print "Found files for server"
    print json.dumps(afu.getAllFilesForServer(), indent=4, sort_keys=True)

    afu.versionizeAllFilesForServer(timeBase="days", customContent=None)

    # afu.uploadFilesToServer(fileList=afu.getAllFilesForServer())
    afu.uploadAllFilesToServer()


    # upload the file to the device
    afu.findFileForDevice()
    print "Found file for device"
    print afu.getFileForDevice()
    afu.uploadFileToDevice(theFile=afu.getFileForDevice())

# exit()
