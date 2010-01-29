#!/usr/bin/python
# -*- coding: utf-8 -*-

#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 3 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

from sys import argv
from uuid import uuid4
import re

try:
    from mod_python import apache
except:
    pass

class chatlog:
    def __init__(self, textlog, language):
        """
        Input a text/plain chatlog from zweipktfkt and get out HTML5 goodness.
        """

        self.textlog = textlog

        self.html5log = ""

        firstline = textlog.split("\n")[0]

        self.html5log += '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="''' + language + '''">
<head>
    <title>Log für ''' + firstline[15:24] + ' ' + firstline[-4:] + '''</title>
    <link rel="stylesheet" href="css/tango.css" title="Defaul-Stil" type="text/css"/>
</head>
<body>
<!-- link to last line -->'''

        for i, line in enumerate(textlog.split("\n")):

            # replace xml chars
            line = line.replace("&","&amp;")
            line = line.replace("<","&lt;")
            line = line.replace(">","&gt;")
            line = line.replace("'","&apos;")
            line = line.replace("\"","&quot;")

            # input is mixed utf-8 and latin-1
            try:
                line = unicode(line,'utf-8','strict').encode('ascii', 'xmlcharrefreplace')
            except UnicodeDecodeError:
                line = unicode(line,'latin-1','strict').encode('ascii', 'xmlcharrefreplace')

            # remove erroneous spaces
            try:
                if line[10] == " ":
                    line = line[:10] + line[11:]
            except IndexError:
                pass

            # markup log time, add anchors, mark non-speak lines
            try:
                int(line[:2])
                int(line[3:5])
                line = '<span class="time">' + line[:5] + '</span>' + line[5:]

                uuid = str(uuid4())
                if line[32:36] == "&lt;":
                    line = '<a class="line-marker" href="#' + uuid + '">#</a><span class="line dialog" id="' + uuid + '">' + line + '</span>'
                else:
                    line = '<a class="line-marker" href="#' + uuid + '">#</a><span class="line non-dialog" id="' + uuid + '">' + line + '</span>'
            except:
                pass

            # markup links
            uri_pattern = r'''(?<!\()\b([A-Za-z][A-Za-z0-9\+\.\-]*:([A-Za-z0-9\.\-_~:/\?#\[\]@!\$&'\(\)\*\+,;=]|%[A-Fa-f0-9]{2})+)'''
            uri_replacement = r'''<a href="\1">\1</a>'''

            line = re.sub(uri_pattern, uri_replacement, line)

            self.html5log += line + "<br/>\n"

        self.html5log += """</body>
</html>"""

        link = '''<a class="line-link" href="#''' + uuid + '''">⤓</a>'''
        self.html5log = self.html5log.replace("<!-- link to last line -->", link)

    def __str__(self):
        return self.html5log


if __name__ == '__main__':
    infile = argv[1]
    outfile = infile + ".xhtml"

    f = open(infile, "r")
    input = f.read()
    f.close()

    nicelog = str(chatlog(input, "de"))

    g = open(outfile, "w")
    g.write(nicelog)
    g.close()

def handler(req):
    req.content_type = "application/xhtml+xml; charset=UTF8"
    f = open(req.filename)
    req.write(str(chatlog(f.read(),"de")))
    f.close()
    return apache.OK
