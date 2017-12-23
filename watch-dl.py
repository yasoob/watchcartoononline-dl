#! /usr/bin/python

# -*- coding: utf-8 -*-
# ported to python 3.x by Dragneel1234
from __future__ import print_function

try:
	from urllib2 import urlopen, Request, unquote, HTTPError
	from urllib import urlencode
except ImportError:
	from urllib.request import urlopen, Request
	from urllib.parse import urlencode, unquote
	from urllib.error import HTTPError

import re
import sys
import os
import os.path
import argparse

def info_extractor(url):
    _VALID_URL = b'(?:https://)?(?:www\.)?watchcartoononline\.io/([^/]+)'
    #checks if url is valid
    if re.match(_VALID_URL, url) is not None:
        #sets user_agent so watchcartoononline doesn't cause issues
        user_agent = 'Mozilla/5.0 (Windows NT 5.1; rv:10.0.1) Gecko/20100101 Firefox/10.0.1'
        headers = { 'User-Agent' : user_agent }

        print("[watchcartoononline-dl] Downloading webpage")
        request = Request(url.decode(),headers=headers)
        webpage = urlopen(request).read()

        print("[watchcartoononline-dl] Finding video")
        video_url = re.search(b'<iframe [^>]*src="https://www.watchcartoononline.io/inc/(.+?)>', webpage).group()
        video_url = re.search(b'src="(.+?)"', video_url).group(1).replace(b' ',b'%20')

        # "clicks" the "Click Here to Watch Free" button to so it can access the actual video file url
        #print("[watchcartoononline-dl]  Clicking stupid 'Watch Free' button"
        params = urlencode({'fuck_you':'','confirm':'Click Here to Watch Free!!'})

        print("[watchcartoononline-dl]  Getting video URL")
        request = Request(video_url.decode("utf-8"),params.encode(),headers=headers)
        video_webpage = urlopen(request).read()
        #scrapes the actual file url
        final_url =  re.findall(b'file: "(.+?)"', video_webpage)
        #throws error if list is blank
        if not final_url:
            print("ERROR: Video not found")
        else:
            return final_url[-1]
    else:
        print("ERROR: URL was invalid, please use a valid URL from www.watchcartoononline.com")

def episodes_extractor(episode_list, ep_range, directory):
    _VALID_URL = r'(?:https://)?(?:www\.)?watchcartoononline\.io/anime/([^/]+)'
    #check if url is valid
    if re.match(_VALID_URL, episode_list) is not None:

        #sets user_agent so watchcartoononline doesn't cause issues
        user_agent = 'Mozilla/5.0 (Windows NT 5.1; rv:10.0.1) Gecko/20100101 Firefox/10.0.1'
        headers = { 'User-Agent' : user_agent }

        print("[watchcartoononline-dl]  Downloading webpage")
        request = Request(episode_list, headers=headers)
        webpage = urlopen(request).read()

        print("[watchcartoononline-dl]  Finding episode(s)")

        #remove the end of the html, to avoid matching episodes in the 'recenly added' bar
        indexOfRecenly = webpage.find(b"Recenly")
        truncated = ""
        if indexOfRecenly != -1:
            truncated = webpage[:indexOfRecenly]
        else:
            print("WARNING: couldn't find 'Recenly Added' section in page, maybe the site layout has changed?")

        #todo: improve this regex to work for more stuff
        page_urls = re.findall(b'https://www.watchcartoononline.io/[a-zA-Z0-9-]+episode-[0-9]{1,4}[a-zA-Z0-9-]+', truncated)[::-1]
        #print(list of URLs we are about to download

        if len(ep_range) > 0:
            start = ep_range[0]
            end = ep_range[1]

            if end < start:
                print("ERROR: Please specify a valid episode range, end is before start")
                sys.exit(0)
            try:
                start_idx = [i for i, s in enumerate(page_urls) if str(start) in s][0]
                end_idx = [i for i, s in enumerate(page_urls) if str(end) in s][0]
            except:
                print("ERROR: Please specify a valid episode range, this range is out of range of the episodes")
                sys.exit(0)

            page_urls = page_urls[start_idx:end_idx+1]
            print("[watchcartoononline-dl]  Downloading episodes {} thru {}".format(start, end))


        print("URLs found:")
        for url in page_urls:
            print(url.decode("utf-8"))

        #run original script on each episode URL we found
        for url in page_urls:
            print("[watchcartoononline-dl]  Downloading "+ url.decode("utf-8"))
            doAnEpisode(url, directory)
    else:
        print("ERROR: URL was invalid, please use a valid URL from www.watchcartoononline.com")

def downloader(fileurl, file_name):
    try:
        #opens the video file url
        u = urlopen(fileurl)
    except HTTPError as he:
        print("HTTPError! code:"+str(he.code))
        return

    #gets metadata
    meta = u.info()
    file_size = int(u.info()["Content-Length"])
    file_type = u.info()["Content-Type"]

    #before downloading, check if file already exists and is the expected size
    if os.path.isfile(file_name) and os.path.getsize(file_name) == file_size:
        print("[watchcartoononline-dl]  file already exists and is the correct size, skipping...")
        return

    try:
        #writes new file with the filename provided
        f = open(file_name, 'wb')
    except IOError as e:
        print(e)
        print("ERROR: That directory doesn't exist, please create the folder or specify a valid folder.")
        sys.exit(0)

    print("[watchcartoononline-dl]  Filetype: %s" %(file_type))
    print("[watchcartoononline-dl]  Destination: %s" %(file_name))
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
        sys.stdout.write((" " * (int(os.environ.get("COLUMNS") or 80)-2)) + "\r")
        sys.stdout.write(status)
        sys.stdout.flush()

    #Download done. Close file stream
    f.close()
    sys.stdout.write(os.linesep)
    sys.stdout.flush()

def convertSize(n, format='%(value).1f %(symbol)s', symbols='iec'):
    """
    Convert n bytes into a human readable string based on format.
    symbols can be either "customary", "customary_ext", "iec" or "iec_ext",
    see: http://goo.gl/kTQMs
    """
    SYMBOLS = {
    'customary'     : ('B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y'),
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


def doAnEpisode(url, directory):
    #url = sys.argv[1]
    final_url = info_extractor(url)
    if final_url is None:
        print("ERROR: unable to extract video url from " + url.decode("utf-8"))
    else:
        name = final_url.replace('%20',' ').split('/')[-1]
        name = name[:name.find('?')] # remove trailing URL arguments
        name = unquote(name)

        if directory is None:
            directory = os.getcwd()
        downloader(final_url, os.path.join(directory, name))

if __name__ == '__main__':
    # Setup command line args, url, range, and directory
    parser = argparse.ArgumentParser(prog='watch-dl.py', usage='%(prog)s [URL] [-h] [-r START_EPISODE_NUMBER END_EPISODE_NUMBER] [-d DIRECTORY]')
    # parser = argparse.ArgumentParser()
    parser.add_argument('url', nargs=1)
    parser.add_argument('-r', '--range', nargs=2, type=int, help='Range of episodes to download.')
    parser.add_argument('-d', '--directory', nargs=1, help='Directory to download episodes to, if not provided will downlaod to current working directory.')
    parsed = parser.parse_args()
    # NOTE: args with '-' have it replaced with '_'
    print('Result:',  vars(parsed))

    try:
        url = parsed.url[0]
        ep_range = parsed.range if parsed.range else []
        dir = parsed.directory[0] if parsed.directory else ""
        if "/anime/" in url: #argument looks like an episode-list page
            print("[watchcartoononline-dl] looks like a list of episodes (season?), extracting episode page URLs...")
            episodes_extractor(url, ep_range, dir)
        else: #episode should be a video page
            doAnEpisode(url, dir)
    #throws error message for keyboard interrupt eg: ctrl+c
    except KeyboardInterrupt:
        print("\nERROR: Interrupted by user")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)


