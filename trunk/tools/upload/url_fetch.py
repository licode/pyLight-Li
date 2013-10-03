import urllib2
import shutil
import urlparse
import os
import sys


def download(url, fileName=None):
    """This function is implemented by Michael Waterfall/lostlogic in stackoverflow"""
    def getFileName(url,openUrl):
        if 'Content-Disposition' in openUrl.info():
            # If the response has Content-Disposition, try to get filename from it
            cd = dict(map(
                lambda x: x.strip().split('=') if '=' in x else (x.strip(),''),
                openUrl.info()['Content-Disposition'].split(';')))
            if 'filename' in cd:
                filename = cd['filename'].strip("\"'")
                if filename: return filename
        # if no filename was found above, parse it out of the final URL.
        return os.path.basename(urlparse.urlsplit(openUrl.url)[2])

    try:
        r = urllib2.urlopen(urllib2.Request(url))
        fileName = fileName or getFileName(url,r)
        with open(fileName, 'wb') as f:
            shutil.copyfileobj(r,f)
    except:
        return 1
    r.close()
    return 0

def main():
    status = len(sys.argv) != 2 or download(sys.argv[1])
    sys.exit(status)
    
if __name__ == '__main__':
    main()