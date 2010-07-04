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
import re
import time
import locale

try:
    from mod_python import apache
except:
    pass

class chatlog:
    def __init__(self, textlog, language, plain=False):
        """
        Input a text/plain chatlog from zweipktfkt and get out HTML5 goodness.
        """

        self.log = ""

        firstline = textlog.split("\n")[0]
        try:
            locale.setlocale(locale.LC_ALL, "en_US.utf-8")
            datetime = time.strptime(firstline[15:])
        except ValueError:
            locale.setlocale(locale.LC_ALL, "de_DE.utf-8")
            datetime = time.strptime(firstline[15:])
        locale.setlocale(locale.LC_ALL, "de_DE.utf-8")

        if not plain:
            self.log += '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="''' + language + '''">
<head>
    <title>Log für ''' + time.strftime("%A, den %d. %B %Y", datetime) + '''</title>
    <link rel="stylesheet" href="css/tango.css" title="Defaul-Stil" type="text/css"/>
</head>
<body>
<a class="plaintextlink" href="?mode=plain">Plaintext</a><br />
<!-- link to last line -->'''

        for lineid, line in enumerate(textlog.split("\n")):

            # remove hosts
            line = re.sub(r'(^[0-9]{2}:[0-9]{2} [^<][^ ]*) \(.*@.*\) (has (joined|quit|left))', r'\1 \2', line)

            # replace xml chars
            if not plain:
                line = line.replace("&","&amp;")
                line = line.replace("<","&lt;")
                line = line.replace(">","&gt;")
                line = line.replace("'","&apos;")
                line = line.replace("\"","&quot;")

            # input is mixed utf-8 and latin-1
            try:
                line = unicode(line,'utf-8','strict')
            except UnicodeDecodeError:
                line = unicode(line,'latin-1','strict')
            if plain:
                line = line.encode('utf-8')
            else:
                line = line.encode('ascii', 'xmlcharrefreplace')

            # remove erroneous spaces
            try:
                if line[10] == " ":
                    line = line[:10] + line[11:]
            except IndexError:
                pass

            if not plain:
                # markup log time, add anchors, mark non-speak lines
                try:
                    int(line[:2])
                    int(line[3:5])
                    line = '<span class="time">' + line[:5] + '</span>' + line[5:]
        
                    if line[32:36] == "&lt;":
                        line = '<a class="line-marker" href="#' + str(lineid) + '">#</a><span class="line dialog" id="' + str(lineid) + '">' + line + '</span>'
                    else:
                        line = '<a class="line-marker" href="#' + str(lineid) + '">#</a><span class="line non-dialog" id="' + str(lineid) + '">' + line + '</span>'

                    lastlineid = lineid
                except ValueError:
                    pass

                # markup links
                uri_patterns = [ r'''((?<=\()\b[A-Za-z][A-Za-z0-9\+\.\-]*:([A-Za-z0-9\.\-_~:/\?#\[\]@!\$&'\(\)\*\+,;=]|%[A-Fa-f0-9]{2})+(?=\)))''', r'''((?<=&lt;)\b[A-Za-z][A-Za-z0-9\+\.\-]*:([A-Za-z0-9\.\-_~:/\?#\[\]@!\$&'\(\)\*\+,;=]|%[A-Fa-f0-9]{2})+(?=&gt;))''', r'''(?<!\()\b([A-Za-z][A-Za-z0-9\+\.\-]*:([A-Za-z0-9\.\-_~:/\?#\[\]@!\$&'\(\)\*\+,;=]|%[A-Fa-f0-9]{2})+)''', ]
                uri_replacement = r'''<a href="\1">\1</a>'''

                for p in uri_patterns:
                    line, nsubs = re.subn(p, uri_replacement, line)
                    if nsubs > 0: break     # only use first matching pattern

            self.log += line + ("\n" if plain else "<br/>\n")

            if (not plain) and line == textlog.split("\n")[-1:][0]:
                link = '''<a class="line-link" href="#''' + str(lastlineid) + '''">⤓</a>'''
                self.log = self.log.replace("<!-- link to last line -->", link)

        if not plain:
            self.log += """</body>
</html>"""

    def __str__(self):
        return self.log


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
    if req.args != None:
        params = dict([part.split('=') for part in req.args.split('&')])
        if 'mode' in params and params['mode'] == 'plain':
            plain = True
        else:
            plain = False
    else:
        plain = False

    if plain:
        req.content_type = "text/plain; charset=UTF8"
        f = open(req.filename)
        req.write(str(chatlog(f.read(),"de",plain=True)))
        f.close()
        return apache.OK
    else:
        req.content_type = "application/xhtml+xml; charset=UTF8"
        f = open(req.filename)
        req.write(str(chatlog(f.read(),"de",plain=False)))
        f.close()
        return apache.OK
