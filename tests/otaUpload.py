#!/usr/local/bin/python2
# -*- coding: UTF-8 -*-
#

"""
This script will upload the predefined filename to the OTA URL of a device

Drawback: After "clicking" the submit button we will face a timeout
Therefore the try exception was added
"""

from base64 import b64encode
import mechanize
from bs4 import BeautifulSoup
import requests

__author__ = "Jonas Scharpf"
__copyright__ = "Copyright 2019, brainelectronics"
__version__ = "1.0.0"
__maintainer__ = "Jonas Scharpf"
__email__ = "jonas@brainelectronics.de"
__status__ = "Prototype"

url = 'http://192.168.178.50/firmware'
username = 'admin'
password = 'admin'
fileName = "/Users/Jones/Documents/Arduino/build/TFT_graphicstest_QR_code_OTA.ino.bin"

b64login = b64encode('%s:%s' % (username, password))

print "Starting"
br = mechanize.Browser()

# # Log information about HTTP redirects and Refreshes.
# br.set_debug_redirects(True)
# # Log HTTP response bodies (i.e. the HTML, most of the time).
# br.set_debug_responses(True)
# # Print HTTP headers.
# br.set_debug_http(True)

# br.addheaders= [('User-agent', 'Mozilla/5.0')]

br.addheaders.append(
  ('Authorization', 'Basic %s' % b64login )
)

# open(url_or_request, data=None, timeout=<object object>)[source]
br.open(url, timeout=10.0)
print "URL successfully opened"

r = br.response()
data = r.read()
print "=== === DATA === ==="
print data
print "=== "*3

# print "=== === SOUP === ==="
# soup = BeautifulSoup(data, 'html.parser')
# print soup.prettify()
# print "=== "*3

# print len(br.forms())
for form in br.forms():
    print "Form name:", form.name
    print form

br.select_form(nr=0)
print "Finished selecting the form nr=0"

br.form.add_file(open(fileName,'r'))
# br.form.add_file(open("test.png",'rb'),'images/png',filename,name='file')
# br.form.add_file(open(fileName), 'text/plain', fileName)
print "File added"
# socket.setdefaulttimeout(5.0)

try:
	br.submit()
	# resp = br.submit()
	# print "\n\n----------resp----------", resp.read() #Returning blank
	print "Clicked submit"
except Exception as e:
	pass
	print "Caught extension:", e


print "Finished"

