""" DM5 manga downloader """

import abc
import re
import logging
import threading
import time
import sys
import os
import os.path
import json
import urllib.parse

import requests
import js2py
from bs4 import BeautifulSoup


class BaseManga:
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:64.0) Gecko/20100101 Firefox/64.0',
        'Accept': '*/*',
        'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
    }

    CHAPTER_DIR_PREFIX = 'ch_'

    def __init__(self, manga_url):
        self.manga_url = manga_url

        self.headers = {**self.HEADERS, 'Referer': self.manga_url}

        self._chapters = []
        self._get_chapters()

    def download(self, from_chapter, to_chapter, destdir):
        if to_chapter != -1 and from_chapter > to_chapter:
            raise ValueError(
                'to_chapter should be larger than or equal to from_chapter, or -1 (until end)')

        if not os.path.exists(destdir):
            os.mkdir(destdir)

        for chapter in self._chapters:
            if (chapter.index == from_chapter
                    or (chapter.index > from_chapter and
                        (to_chapter == -1 or chapter.index <= to_chapter))):
                chapter.download(
                    os.path.join(destdir, self.CHAPTER_DIR_PREFIX + str(chapter.index)))

    def get_chapter(self, index):
        return [x for x in self._chapters if x.index == index][0]

    @abc.abstractmethod
    def _get_chapters(self):
        pass

class BaseChapter:
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:64.0) Gecko/20100101 Firefox/64.0',
        'Accept': '*/*',
        'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'X-Requested-With': 'XMLHttpRequest',
    }

    def __init__(self, index, url):
        self.index = index
        self.url = url

        self.headers = {**self.HEADERS, 'Referer': self.url}
        self._images = []

    def __repr__(self):
        return f'<Chapter index={self.index} url={self.url}>'

    def download(self, destdir):
        """write to self._images"""
        def _download_image(img_url, filename):
            if not os.path.exists(filename):
                resp = requests.get(img_url, headers=self.headers)
                print(f'writing to {filename}')
                open(filename, 'wb').write(resp.content)
            else:
                print(f'skipping {filename}')

        print(f'downloading chapter {self.index}: {self.url}')

        if not os.path.exists(destdir):
            os.mkdir(destdir)

        if not self._images:
            self._get_image_urls()

        pool = []
        for image in self._images:
            filepath = os.path.join(destdir, f'{image["index"] :02}.jpg')
            thd = threading.Thread(target=_download_image, args=(image['url'], filepath))
            thd.start()
            pool.append(thd)
        for thd in pool:
            thd.join()

    @property
    def images(self):
        if not self._images:
            self._get_image_urls()
        return self._images

    @abc.abstractmethod
    def _get_image_urls(self):
        pass

class Dm5Manga(BaseManga):
    def __init__(self, manga_url):
        BaseManga.__init__(self, manga_url)

    def _get_chapters(self):
        b = BeautifulSoup(requests.get(self.manga_url, headers=self.headers).text, 'html.parser')

        for li in b.find(id='detail-list-select-1').find_all('li'):
            index = int(re.search(r'[0-9]+', li.text).group(0))
            chapter_url = urllib.parse.urljoin(self.manga_url, li.find('a')['href'])

            self._chapters.append(Dm5Chapter(index, chapter_url))
#          self._chapters.sort(key=lambda x: x.index)

class Dm5Chapter(BaseChapter):
    def __init__(self, index, url):
        BaseChapter.__init__(self, index, url)

    def _get_image_urls(self):
        logging.debug(f'getting image URLs of chapter {self.index}')

        sess = requests.Session()
        chapter_cover = sess.get(self.url)
        mid = re.search(r'DM5_MID=([0-9]*);', chapter_cover.text).group(1)
        cid = re.search(r'DM5_CID=([0-9]*);', chapter_cover.text).group(1)
        viewsign = re.search(r'DM5_VIEWSIGN="([a-f0-9]*)";', chapter_cover.text).group(1)
        viewsign_dt = re.search(r'DM5_VIEWSIGN_DT="([0-9\-: ]*)";', chapter_cover.text).group(1)

#          b = BeautifulSoup(chapter_cover.text, 'html.parser')
#          pages = max([1] + [int(e.text) for e in b.find(id='chapterpager').find_all('a')])

        data = {
            'cid': cid,
            'page': 1,
            'key': '',
            'language': 1,
            'gtk': 6,
            '_cid': cid,
            '_mid': mid,
            '_sign': viewsign,
            '_dt': viewsign_dt,
        }

        result = []
        attempts = 0
        while attempts <= 5:
            attempts += 1

            resp1 = sess.get('http://www.dm5.com/chapterfun.ashx', data=data, headers=self.headers)

            time.sleep(3)
            data['page'] = 2
            #      s.cookies['image_time_cookie'] = s.cookies['image_time_cookie'][:-1] + '1'
            #      s.cookies['dm5imgcooke'] = '804828%7C2'
            #      s.cookies['firsturl'] = 'http%3A%2F%2Fwww.dm5.com%2Fm804828%2F'
            #      s.cookies['dm5cookieenabletest'] = '1'
            resp2 = sess.get('http://www.dm5.com/chapterfun.ashx', data=data, headers=self.headers)

            try:
                r = js2py.eval_js(resp1.text)
                result += r
                r = js2py.eval_js(resp2.text)
                result += r
            except js2py.internals.simplex.JsException:
                logging.debug('js raw data:')
                logging.debug(resp1.text)
                logging.debug(resp2.text)
            else:
                break

        if not result:
            raise RuntimeError('get image URLs failed')
        result = set(result)
        for url in result:
            self._images.append({
                'index': int(re.search(r'([0-9]+)_[0-9]+\.(jpg|jpeg|png)', url).group(1)),
                'filename': re.sub(r'([0-9]+)_[0-9]+\.(jpg|jpeg|png)', r'\1.\2', url),
                'url': url,
            })
        self._images.sort(key=lambda x: x['index'])



def download_manga(manga_url, from_chapter, to_chapter, destdir):
    if urllib.parse.urlsplit(manga_url)[1] == 'www.dm5.com':
        Dm5Manga(manga_url).download(from_chapter, to_chapter, destdir)
    else:
        # more manga websites will be supported
        raise NotImplementedError('unsupported site')

def print_image_urls(manga_url, chapter_index):
    chapter = Dm5Manga(manga_url).get_chapter(chapter_index)
    if urllib.parse.urlsplit(manga_url)[1] == 'www.dm5.com':
        print(json.dumps({
            'referer': chapter.url,
            'image_urls': [x['url'] for x in chapter.images]}))
    else:
        # more manga websites will be supported
        raise NotImplementedError('unsupported site')


def main():
    args = sys.argv
    dump = False
    if '-d' in args:
        dump = True
        args.remove('-d')

    try:
        if dump:
            print_image_urls(args[1], int(args[2]))
        else:
            if args[4:]:
                download_manga(args[1], int(args[2]), int(args[3]), args[4].replace('/', ''))
            elif args[3:]:
                download_manga(args[1], int(args[2]), int(args[3]), 'manga')
            elif args[2:]:
                download_manga(args[1], int(args[2]), int(args[2]), 'manga')
            else:
                raise ValueError
    except ValueError:
        print(f'Usage: {sys.argv[0]} manga_url from_chapter [to_chapter] [destdir]')
        print('destdir default to ./manga')
        print('to_chapter can be omitted (only one chapter), or -1 (until the latest)')
        exit(127)

def tmp_main():
    m = Dm5Manga('http://www.dm5.com/manhua-wudengfendehuajia/')
    print(m._chapters)
    print(m._chapters[0].images)
    m.download(1,1,'manga')

if __name__ == '__main__':
#      logging.basicConfig(level='DEBUG')
    main()

# download_chapter('http://www.dm5.com/m553813')
# download_manga('http://www.dm5.com/manhua-jisuxuexiaodezhuliye/', 22)
