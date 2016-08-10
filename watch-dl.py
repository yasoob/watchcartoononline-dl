# -*- coding: utf-8 -*-
import urllib
import re
import urllib2
import sys
import os

def info_extractor(url):
    _VALID_URL = r'(?:http://)?(?:www\.)?watchcartoononline\.com/([^/]+)'
    #checks if url is valid
    if re.match(_VALID_URL, url) is not None:
        #sets user_agent so watchcartoononline doesn't cause issues
        user_agent = 'Mozilla/5.0 (Windows NT 5.1; rv:10.0.1) Gecko/20100101 Firefox/10.0.1'
        headers = { 'User-Agent' : user_agent }
        
        print "[watchcartoononline-dl]  Opening webpage"
        request = urllib2.Request(url,headers=headers)
        webpage = urllib2.urlopen(request).read()
    
        print "[watchcartoononline-dl]  Finding video"
        video_url = re.search(r'<iframe id="(.+?)0" (.+?)>', webpage).group()
        video_url = re.search('src="(.+?)"', video_url).group(1).replace(' ','%20')
        
        # "clicks" the "Click Here to Watch Free" button to so it can access the actual video file url
        print "[watchcartoononline-dl]  Clicking stupid 'Watch Free' button"
        params = urllib.urlencode({'fuck_you':'','confirm':'Click Here to Watch Free!!'})
    
        print "[watchcartoononline-dl]  Getting video URL"
        request = urllib2.Request(video_url,params,headers=headers)
        video_webpage = urllib2.urlopen(request).read()
        #scrapes the actual file url
        final_url =  re.findall(r'file: "(.+?)"', video_webpage)
        #throws error if list is blank
        if not final_url:
            print "ERROR: Video not found"
        else:
            return urllib.unquote(final_url[-1]).replace(' ','%20')
    else:
        print "ERROR: URL was invalid, please use a valid URL from www.watchcartoononline.com"

def downloader(fileurl,file_name):
    #opens the video file url
    u = urllib2.urlopen(fileurl)
    #writes new file with the filename provided
    f = open(file_name, 'wb')
    #gets metadata
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    file_type = meta.getheaders("Content-Type")[0]
    print "[watchcartoononline-dl]  Filetype: %s" %(file_type)
    print "[watchcartoononline-dl]  Destination: %s" %(file_name)
    file_size_dl = 0
    block_size = 8192

    #Download loop
    while True:
        buffer = u.read(block_size)
        if not buffer:
            break

        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"[download]  %s of %s [%3.2f%%]" % (convertSize(file_size_dl), convertSize(file_size), file_size_dl * 100. / file_size)
        status = status + chr(8)*(len(status)+1)
        #print status
        sys.stdout.write(" %s" % status)
        sys.stdout.flush()

    #Download done. Close file stream
    f.close()

def convertSize(n, format='%(value).1f %(symbol)s', symbols='customary'):
    """
    Convert n bytes into a human readable string based on format.
    symbols can be either "customary", "customary_ext", "iec" or "iec_ext",
    see: http://goo.gl/kTQMs
    """
    SYMBOLS = {
    'customary'     : ('B', 'K', 'Mb', 'G', 'T', 'P', 'E', 'Z', 'Y'),
    'customary_ext' : ('byte', 'kilo', 'mega', 'giga', 'tera', 'peta', 'exa',
                       'zetta', 'iotta'),
    'iec'           : ('Bi', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi', 'Yi'),
    'iec_ext'       : ('byte', 'kibi', 'mebi', 'gibi', 'tebi', 'pebi', 'exbi',
                       'zebi', 'yobi'),
    }
    n = int(n)
    if n < 0:
        raise ValueError("n < 0")
    symbols = SYMBOLS[symbols]
    prefix = {}
    for i, s in enumerate(symbols[1:]):
        prefix[s] = 1 << (i+1)*10
    for symbol in reversed(symbols[1:]):
        if n >= prefix[symbol]:
            value = float(n) / prefix[symbol]
            return format % locals()
    return format % dict(symbol=symbols[0], value=n)

if __name__ == '__main__':
    if len(sys.argv[1:]) > 0:
        try:
            url = sys.argv[1]
            final_url = info_extractor(url)
            if final_url is None:
                print "ERROR: Try again"
            else:
                name = final_url.split('/')[-1]
                downloader(final_url,name)
        #throws error message when keyboard inturupted eg: ctrl+c
        except KeyboardInterrupt:
            print "\nERROR: Interrupted by user"
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)
    else:
        #Prints some info if there was no argument
        print "Usage: python watch-dl.py [URL...]" 
        print "ERROR: You must provide a valid URL from www.watchcartoononline.com"
