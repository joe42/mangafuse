# -*- coding: iso-8859-15 -*-
'''
Created on 08.04.2011

@author: joe
'''

import time
import datetime
from cloudfusion.dropbox import client, auth
from cloudfusion.store.store import *
import logging
import logging.config
import os.path
from cloudfusion.store.dropbox.file_decorator import NameableFile
import tempfile
import ConfigParser
import StringIO
import cloudfusion
import urllib2
import re
import shelve
import threading
from threading import Thread, Timer
from urllib2 import HTTPError
import time

def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param ExceptionToCheck: the exception to check. may be a tuple of
        excpetions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """
    def deco_retry(f):
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            try_one_last_time = True
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                    try_one_last_time = False
                    break
                except ExceptionToCheck, e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print msg
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            if try_one_last_time:
                return f(*args, **kwargs)
            return
        return f_retry  # true decorator
    return deco_retry


class ServerError(StoreAccessError):
    def __init__(self, msg):
        super(ServerError, self).__init__(msg) 
        
class SynchronizedLoggerDecorator(object):
    def __init__(self, logger):
        self.logger = logger
        self.lock = threading.Lock()
    def debug(self, msg):
        self.lock.acquire()
        self.logger.debug(msg)
        self.lock.release()
    def info(self, msg):
        self.lock.acquire()
        self.logger.info(msg)
        self.lock.release()
    def __getattr__(self, name):
        return getattr(self.logger, name)

        
class MostRecentChapterLoader(object):
    def __init__(self, mangaStore, mangaRetrievalAPI, logger):
        self.mangaRetrievalAPI = mangaRetrievalAPI
        self.mangaStore = mangaStore
        self.logger = logger
        t = Thread(target=self.run)
        t.start()
        self.logger.debug("initialized MostRecentChapterLoader")
    def run(self):
        while True:
            time.sleep(5)
            self.logger.debug("getting most recent chapters ")
            mangas = self.mangaRetrievalAPI.get_manganames()
            for manganame in mangas:
                self.logger.debug("getting most recent chapter: "+manganame)
                try:
                    chapters = self.mangaRetrievalAPI.get_chapters(manganame)
                    chapter = max(map(float,chapters))
                    chapter = int(chapter) # float maps '30' to 30.0  
                    path = "/%s/%s/0001" % (manganame,chapter)
                    self.logger.debug("getting most recent chapter: "+path)
                    self.mangaStore.get_image(path)
                    self.logger.debug("got most recent chapter: "+path)
                except e:
                    self.logger.debug("exception! : "+str(e))
                time.sleep(10)
            time.sleep ( 60*10 )

class FileCache(object):
    def __init__(self, cache_max_size = 1000000000, cache_file_path = '.mangafuse.cache'):
        self.cache = {} 
        self.cache_file_path = cache_file_path
        if os.path.exists(self.cache_file_path):
            if self.get_size() > cache_max_size:
                os.remove(self.cache_file_path)
        self.cache = shelve.open(self.cache_file_path)
        
    def get_size(self):
        return os.path.getsize(self.cache_file_path)
    def has_file(self, filepath):
        return self.cache.has_key(filepath)
    def get_file(self, filepath):
        return self.cache[filepath]
    def set_file(self, filepath, file):
        self.cache[filepath] = file
    def delete_file(self, filepath):
        del self.cache[filepath]
    def get_filesize(self, filepath):
        if self.has_file(filepath):
            return len(self.cache[filepath])
        return 10000000
    
    def delete_files_in_directory(self, directory):
        for path in self.cache.keys():
            if path.startswith(directory):
                self.delete_file(path)

class MangaRetrievalAPI(object):
    def __init__(self, logger, is_mature=True):
        self.logger = logger
        self.logger.debug("initializing mangaretrieval api")
        self.host = 'http://www.manga-access.com'
        if is_mature:
            self.is_mature = '?mature_confirm=1'
        else: 
            self.is_mature= ''
        
        self.mangas = {}
        self.current_cache_dir = '' #the directory that is currently being cached 
        self.config_file_path = '.mangafuse.cfg'
        self.mangas = shelve.open(self.config_file_path)
    def get_manganames(self):
        return self.mangas;
            
    def has_manga(self, manganame):
        return manganame in self.mangas
    def has_chapter(self, manganame, chapter):
        return chapter in get_chapters(manganame) 
    
    @retry(urllib2.URLError, tries=4, delay=3, backoff=2)
    def get_chapters(self, manganame):
        manga_urlpart = self.__get_mangaurlpart(manganame)
        if manga_urlpart == '':
            return []
        first_letter_of_manga = manga_urlpart[0]
        url = self.__get_chapter_url(manga_urlpart)
        self.logger.debug("get chapters for manga %s from url %s"%(manganame,url))
        f = urllib2.urlopen(url)
        html = f.read()
        f.close()
        manga_urlpart = manga_urlpart.replace('(', '\(')
        manga_urlpart = manga_urlpart.replace(')', '\)')
        pattern = 'href=".*?/'+first_letter_of_manga+'/'+manga_urlpart+'/'+'chapter/(.*?)"' #href="/manga/B/Bleach/chapter/304.1"
        chapters = re.findall(pattern,html,re.MULTILINE | re.IGNORECASE)
        self.logger.debug("got chapters for manga %s from url %s"%(manganame,url))
        return chapters
    
    @retry(urllib2.URLError, tries=4, delay=3, backoff=2)
    def get_image(self, manganame, chapter, filename):
        manga_urlpart = self.__get_mangaurlpart(manganame)
        url = self.__get_image_url(manga_urlpart, chapter, filename)
        self.logger.debug("get image from "+url)
        f = urllib2.urlopen(url)
        if f.code != 200:
            self.logger.debug("failed with code "+f.code)
            raise Exception("Abort with status code: " + f.code, 0)
        html = f.read()
        f.close()
        pattern1 = 'id="pic".*?src="(.*?png)"' 
        pattern2 = 'id="pic".*?src="(.*?jpg)"' 
        imageurl = re.search(pattern1,html,re.MULTILINE | re.IGNORECASE | re.DOTALL)
        if not imageurl:
            imageurl = re.search(pattern2,html,re.MULTILINE | re.IGNORECASE | re.DOTALL)
        try:
            f = urllib2.urlopen(imageurl.group(1))
        except e:
            self.logger.debug("failed getting image: "+imageurl.group(1))
            raise
        if f.code != 200:
            self.logger.debug("failed with code "+f.code)
            raise Exception("Abort with status code: " + f.code, 0)
        ret = f.read()
        f.close()
        self.logger.debug("got image from "+url)
        return ret
    def get_imagenames(self, manganame, chapter):
        first_letter_of_manga = manganame[0]
        manga_urlpart = self.__get_mangaurlpart(manganame)
        url =  self.host + '/manga/' + first_letter_of_manga + '/' + manga_urlpart +'/'+'chapter/'+chapter
        self.logger.debug("getting image listing for %s of chapter %s"%(manganame, chapter))
        f = urllib2.urlopen(url)
        if f.code != 200:
            self.logger.debug("failed getting image names from "+url+" with code "+f.code)
            raise Exception("Abort with status code: " + f.code, 0)
        html = f.read()
        f.close()
        manga_urlpart = manga_urlpart.replace('(', '\(')
        manga_urlpart = manga_urlpart.replace(')', '\)')
        pattern = 'href=".*?/'+first_letter_of_manga+'/'+manga_urlpart+'/'+'chapter/'+chapter+'/(.*?)"' #/manga/O/One_Piece/chapter/10/24
        images = re.findall(pattern,html,re.MULTILINE | re.IGNORECASE)
        self.logger.debug("got image listing for %s of chapter %s: %s"%(manganame, chapter,repr(images)))
        return images
    def __get_image_url(self, manga_urlpart, chapter, filename):
        first_letter_of_manga = manga_urlpart[0]
        url = "%s/manga/%s/%s/chapter/%s/%s%s" % (self.host, first_letter_of_manga, manga_urlpart, chapter, filename,self.is_mature)
        self.logger.debug("image url: "+url)
        return url
    def mask_mangaurlpart(self, manga_urlpart):
        ret = manga_urlpart.replace(' ', '_')
        return ret
    def __get_chapter_url(self, manga_urlpart):
        self.logger.debug("getting url with chapters for "+manga_urlpart)
        first_letter_of_manga = manga_urlpart[0]
        url = self.host + '/manga/' + first_letter_of_manga + '/' + manga_urlpart+self.is_mature
        return url
    
    def __get_mangaurlpart(self, manganame):
        self.logger.debug("retrieve manga url from manga "+manganame )
        if manganame in self.mangas:
            self.logger.debug("get manga url part from cache: "+self.mangas[manganame])
            return self.mangas[manganame]
        manga_urlpart = self.mask_mangaurlpart(manganame )
        url = self.__get_chapter_url(manga_urlpart)
        try:
            urllib2.urlopen(url)
        except HTTPError:
            self.logger.debug(url +" is no manga url")
            try:
                manga_urlpart +="_(Manhwa)" 
                url = self.__get_chapter_url(manga_urlpart)
                urllib2.urlopen(url)
            except HTTPError:
                self.logger.debug(url+" is no manwa")
                return ''
        return manga_urlpart
    
    def add_manga(self, manganame):
        self.mangas[manganame] = self.__get_mangaurlpart(manganame)
    
    def remove_manga(self, manganame):
        del self.mangas[manganame]
    
class ManhwaRetrievalAPI(MangaRetrievalAPI):
    def get_imagenames(self, manganame, chapter):
        imagenames = super(ManhwaRetrievalAPI, self).get_imagenames(manganame, chapter)
        return [name.zfill(4) for name in imagenames]
    def get_image(self, manganame, chapter, filename):
        return super(ManhwaRetrievalAPI, self).get_image(manganame, chapter, filename.lstrip('0'))

class MangaStore(Store):
    def __init__(self, config):
        self._logging_handler = 'mangafuse'
        self.logger = logging.getLogger(self._logging_handler)
        self.logger.info("mangafuse initialized")
        self.logger = SynchronizedLoggerDecorator(self.logger)
        self.cache = FileCache()
        self.store = ManhwaRetrievalAPI(self.logger)
        self.current_cache_dir = '' #the directory that is currently being cached 
        self.logger.info("mangas: "+repr(self.store.get_manganames()))
        self.mostRecentChapterLoader = MostRecentChapterLoader(self, self.store, self.logger)
        super(MangaStore, self).__init__() 

    def get_name(self):
        self.logger.debug("getting name")
        return "mangafuse"
    
    def get_mangapart_from_path(self, path_to_dir):
        manga = path_to_dir.split('/')[1] # /manga name/chapter number,  /manga name/chapter number/picture name
        return manga
    
    #_(Manhwa)
    def get_chapter_from_filepath(self, path_to_file):
        return os.path.basename(os.path.dirname(path_to_file)) # /manga name/chapter number/picture name

    def get_image(self, path_to_file):
        if self.cache.has_file(path_to_file):
            return self.cache.get_file(path_to_file)
        self.logger.debug("caching file: " +path_to_file)
        if self.current_cache_dir != os.path.dirname(path_to_file):
            self.current_cache_dir = os.path.dirname(path_to_file)
            current_dir_listing =  self.get_directory_listing(self.current_cache_dir)
            current_dir_listing.remove(path_to_file)
            self.logger.debug("retrieve files of directory %s in parallel" % self.current_cache_dir)
            self.logger.debug("retrieve in parallel "+repr(current_dir_listing))
            for path in current_dir_listing:
                t = Thread(target=self.get_file, args=(path,))
                t.start()
        manganame =  self.get_mangapart_from_path(path_to_file)
        chapter = self.get_chapter_from_filepath(path_to_file)
        image_nr = os.path.basename(path_to_file)
        ret = self.store.get_image(manganame, chapter, image_nr)
        self.logger.debug("got image 2")
        self.cache.set_file(path_to_file, ret) 
        self.logger.debug("cached file: " +path_to_file)
        return ret

    def delete(self, path):
        self.logger.debug("deleting " +path)
        self._raise_error_if_invalid_path(path)
        self.remove_manga(path)
        
        
    def get_file(self, path_to_file): 
        self.logger.debug("getting file: " +path_to_file)
        self._raise_error_if_invalid_path(path_to_file)
        try:
            return self.get_image(path_to_file)
        except Exception, e:
            self.logger.debug("get_file(%s) failed with %s"%(path_to_file,str(e)))
            raise StoreAccessError("Transfer error: "+str(e), 0)
        
    def account_info(self):
        self.logger.debug("retrieving account info")
        return 'www.manga-access.com'
    
    def remove_manga(self, directory):
        self.store.remove_manga(self.get_mangapart_from_path(directory))
        self.cache.delete_files_in_directory(directory)

    def create_directory(self, directory):
        self.logger.debug("creating manga directory " +directory)
        self._raise_error_if_invalid_path(directory)
        try:
            manganame = self.get_mangapart_from_path(directory)
            self.logger.debug("manganame " +manganame)
            self.store.add_manga(manganame)
            self.logger.debug("created directory " +directory)
        except Exception, e:
            self.logger.debug("create_directory(%s) failed with %s"%(directory,str(e)))
            raise StoreAccessError("Transfer error: "+str(e), 0)
        
    def move(self, path_to_src, path_to_dest):
        self.logger.debug("moving " +path_to_src+" to "+path_to_dest)
        self._raise_error_if_invalid_path(path_to_src)
        self._raise_error_if_invalid_path(path_to_dest)
        self.remove_manga(path_to_src)
        self.create_directory(path_to_dest)
        
    def get_overall_space(self):
        return self.cache.get_size()

    def get_used_space(self):
        return self.cache.get_size()
    
    def get_chapters(self, dirpath):
        self.logger.debug("get chapters for "+dirpath)
        manganame = self.get_mangapart_from_path(dirpath)
        return self.store.get_chapters(manganame)
    
    def get_images(self, dirpath):
        """
        Get image names of a directory.
        Get image names from the directory from cache if possible. 
        Otherwise retrieve and cache image names of all directories at the same level in parallel.
        """           
        if self.cache.has_file(dirpath):
            return self.cache.get_file(dirpath)
        self.logger.debug("caching listing of "+dirpath)
        if self.current_cache_dir != os.path.dirname(dirpath):
            self.current_cache_dir = os.path.dirname(dirpath)
            current_dir_listing =  self.get_directory_listing(self.current_cache_dir)
            current_dir_listing.remove(dirpath)
            for path in current_dir_listing:
                t = Thread(target=self.get_images, args=(path,))
                t.start()
        manganame = self.get_mangapart_from_path(dirpath)
        chapter = os.path.basename(dirpath)
        images = self.store.get_imagenames(manganame, chapter)
        self.cache.set_file(dirpath, images)
        self.logger.debug("cached listing of "+dirpath)
        return images
        
        
    def get_directory_listing(self, directory):
        def add_directory_prefix(x): return directory+'/'+x;
        self.logger.debug("getting directory listing for "+directory)
        self._raise_error_if_invalid_path(directory)
        if directory == "/":
            return list(self.store.get_manganames())
        try:
            if self.is_chapterpath(directory):
                self.logger.debug("get listing images")
                return map(add_directory_prefix, self.get_images(directory))
            return map(add_directory_prefix, self.get_chapters(directory))
        except Exception, e:
            self.logger.debug("get_directory_listing(%s) failed with %s"%(directory,str(e)))
            raise StoreAccessError("Transfer error: "+str(e), 0)
    
    def is_chapterpath(self, path):
        return re.match("/.*/[0-9].*[^/]*", path) #/Bleach/120
    
    def is_filepath(self, path):
        return re.match("/.*/[0-9].*/[0-9][^/]*", path) #/Bleach/120/1

    def _get_metadata(self, path):
        self.logger.debug("getting metadata for "+path)
        self._raise_error_if_invalid_path(path)
        if path == "/": # workaraund for root metadata
            ret = {}
            ret["bytes"] = 0
            ret["modified"] = 0
            ret["created"] = 0
            ret["path"] = "/"
            ret["is_dir"] = True
            return ret;
        
        manga = self.get_mangapart_from_path(path)
        if self.is_filepath(path):
            self.logger.debug("is filepath")
            ret = {}
            ret["bytes"] = self.cache.get_filesize(path)
            ret["modified"] = 0
            ret["created"] = 0
            ret["path"] = path
            ret["is_dir"] = False
            return ret
        elif not manga in self.store.get_manganames():
            self.logger.debug("_get_metadata(%s) failed with %s"%(path,"NoSuchFilesystemObjectError"))
            raise NoSuchFilesytemObjectError("",0)
        else:
            self.logger.debug("is manga path")
            ret = {}
            ret["bytes"] = 0
            ret["modified"] = 0
            ret["created"] = 0
            ret["path"] = path
            ret["is_dir"] = True
            return ret;
    
    def get_logging_handler(self):
        return self._logging_handler
    
        












