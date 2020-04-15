from random import randrange
import re
import urllib

socket = urllib.urlopen("http://www.youporn.com/random/video")
htmlSource = socket.read()
socket.close()

result = re.findall('<p class="message">((?:.|\\n)*?)</p>', htmlSource)
print "----" + result[randrange(len(result))] + "----"
