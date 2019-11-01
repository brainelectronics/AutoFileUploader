Auto File Uploader
========================

This project can be used to upload files of a specific directory to a server or OTA capable device via WiFi.

---------------

Installation
---------------

To install the package simply call the setup file

``python setup.py install``

or install all packages defines in the requirements.txt file

Description
---------------

This script can search for files or files with a specific pattern at a defined path.
A remote path has also to be defined in the config JSON file, located inside the afu folder.
The server adress as well as the username and its password to upload the file via SFTP have to be defined in a seperate login data JSON file, also located inside the afu folder.
By seperating the login data file from the data file config, you can commit your files config to a repo, while keeping your credentials private.

This module can additionally create a unique version file for each found file in the specified directory. The name can, as everything else, be set in the file config JSON.

Finally the version file and the found files (pattern based or by name) will then be uploaded to the server.

In addition also an upload to a device (ESP32 or ESP8266) can be configured in the file config JSON. The upload username and password have to be set, as for the server, in the login data JSON file.

To always upload the latest files to either a server and/or a device you can run the script every minute or hour with a cronjob ✨🍰✨
