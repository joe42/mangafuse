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
from threading import Thread
from urllib2 import HTTPError


class ServerError(StoreAccessError):
    def __init__(self, msg):
        super(ServerError, self).__init__(msg) 


class MangaStore(Store):
    def __init__(self, config):
        self._logging_handler = 'mangafuse'
        self.logger = logging.getLogger(self._logging_handler)
        self.logger.info("mangafuse initialized")
        self.host = 'http://www.manga-access.com'
        self.mangas = {}
        self.imgcache = {}
        self.current_cache_dir = ''
        self.config_file_path = '.mangafuse.cfg'
        self.cache_file_path = '.mangafuse.cache'
        self.is_mature = '?mature_confirm=1'
        if os.path.exists(self.cache_file_path):
            if os.path.getsize(self.cache_file_path) > 1000000000:
                os.remove(self.cache_file_path)
        self.mangas = shelve.open(self.config_file_path)
        self.logger.info("mangas: "+repr(self.mangas))
        self.imgcache = shelve.open(self.cache_file_path)
        super(MangaStore, self).__init__() 

    def get_name(self):
        self.logger.debug("getting name")
        return "mangafuse"
    

    def get_mangapart_from_path(self, path_to_dir):
        manga = path_to_dir.split('/')[1] # /manga name/chapter number,  /manga name/chapter number/picture name
        return manga
    
    def mask_mangaurlpart(self, mangaurlpart):
        mangaurlpart = mangaurlpart.replace(' ', '_')
        return mangaurlpart
    
    #_(Manhwa)
    def get_chapter_from_filepath(self, path_to_file):
        return os.path.basename(os.path.dirname(path_to_file)) # /manga name/chapter number/picture name

    def get_url_from_filepath(self, path_to_file):
        manga = self.get_mangaurlpart_from_path(path_to_file)
        chapter = self.get_chapter_from_filepath(path_to_file)
        first_letter_of_manga = manga[0]
        filename = os.path.basename(path_to_file)
        url = "%s/manga/%s/%s/chapter/%s/%s%s" % (self.host, first_letter_of_manga, manga, chapter, filename,self.is_mature)
        return url
   


    def get_image(self, path_to_file):
        if self.imgcache.has_key(path_to_file):
            return self.imgcache[path_to_file]
        self.logger.debug("caching file: " +path_to_file)
        if self.current_cache_dir != os.path.dirname(path_to_file):
            self.current_cache_dir = os.path.dirname(path_to_file)
            current_dir_listing =  self.get_directory_listing(self.current_cache_dir)
            current_dir_listing.remove(path_to_file)
            for path in current_dir_listing:
                t = Thread(target=self.get_image, args=(path,))
                t.start()
        url = self.get_url_from_filepath(path_to_file)
        f = urllib2.urlopen(url)
        if f.code != 200:
            raise Exception("Abort with status code: " + f.code, 0)
        html = f.read()
        f.close()
        pattern1 = 'id="pic".*?src="(.*?png)"' 
        pattern2 = 'id="pic".*?src="(.*?jpg)"' 
        imageurl = re.search(pattern1,html,re.MULTILINE | re.IGNORECASE | re.DOTALL)
        if not imageurl:
            imageurl = re.search(pattern2,html,re.MULTILINE | re.IGNORECASE | re.DOTALL)
        f = urllib2.urlopen(imageurl.group(1))
        ret = f.read()
        f.close()
        self.imgcache[path_to_file] = ret
        return ret

    def delete(self, path):
        self.logger.debug("deleting " +path)
        self._raise_error_if_invalid_path(path)
        self.remove_manga(path)
        
        
    def get_file(self, path_to_file): 
        self.logger.debug("getting file: " +path_to_file)
        self._raise_error_if_invalid_path(path_to_file)
        try:
            img = self.get_image(path_to_file)
            return img
        except Exception, e:
            raise StoreAccessError("Transfer error: "+str(e), 0)
        
    def account_info(self):
        self.logger.debug("retrieving account info")
        return 'www.manga-access.com'

    def get_mangaurlpart_from_path(self, path):
        self.logger.debug("retrieve manga url part from path "+path )
        manga =  self.get_mangapart_from_path(path)
        if manga in self.mangas:
            self.logger.debug("get manga url part from cache: "+self.mangas[manga])
            return self.mangas[manga]
        mangaurlpart = self.mask_mangaurlpart(manga )
        url = self.get_url_from_mangaurlpart(mangaurlpart)
        try:
            urllib2.urlopen(url)
        except HTTPError:
            self.logger.debug(url +" is no manga url")
            try:
                mangaurlpart +="_(Manhwa)" 
                url = self.get_url_from_mangaurlpart(mangaurlpart)
                urllib2.urlopen(url)
            except HTTPError:
                self.logger.debug(url+" is no manwa")
                return ''
        return mangaurlpart

    def add_manga(self, directory):
        self.mangas[self.get_mangapart_from_path(directory)] = self.get_mangaurlpart_from_path(directory)
        
    def remove_manga(self, directory):
        del self.mangas[self.get_mangapart_from_path(directory)]
        for path in self.imgcache.keys():
            if path.startswith(directory):
                del self.imgcache[path]

    def create_directory(self, directory):
        self.logger.debug("creating manga directory " +directory)
        self._raise_error_if_invalid_path(directory)
        try:
            self.add_manga(directory)
            self.logger.debug("created directory " +directory)
        except Exception, e:
            raise StoreAccessError("Transfer error: "+str(e), 0)
        
    def move(self, path_to_src, path_to_dest):
        self.logger.debug("moving " +path_to_src+" to "+path_to_dest)
        self._raise_error_if_invalid_path(path_to_src)
        self._raise_error_if_invalid_path(path_to_dest)
        self.remove_manga(path_to_src)
        self.create_directory(path_to_dest)
        
    def get_overall_space(self):
        return 0

    def get_used_space(self):
        return 0
    

    def get_url_from_mangaurlpart(self, manga):
        first_letter_of_manga = manga[0]
        url = self.host + '/manga/' + first_letter_of_manga + '/' + manga+self.is_mature
        return url

    def get_chapters(self, dirpath):
        self.logger.debug("get chapters for "+dirpath)
        mangaurlpart = self.get_mangaurlpart_from_path(dirpath)
        if mangaurlpart == '':
            return []
        first_letter_of_manga = mangaurlpart[0]
        url = self.get_url_from_mangaurlpart(mangaurlpart)
        
        self.logger.debug("chapter url "+url)
        f = urllib2.urlopen(url)
        html = f.read()
        f.close()
        mangaurlpart = mangaurlpart.replace('(', '\(')
        mangaurlpart = mangaurlpart.replace(')', '\)')
        pattern = 'href=".*?/'+first_letter_of_manga+'/'+mangaurlpart+'/'+'chapter/(.*?)"' #href="/manga/B/Bleach/chapter/304.1"
        self.logger.debug("chapter pattern "+pattern)
        chapters = re.findall(pattern,html,re.MULTILINE | re.IGNORECASE)
        self.logger.debug("chapters "+repr(chapters))        
        return chapters
    
    def get_images(self, dirpath):
        if self.imgcache.has_key(dirpath):
            return self.imgcache[dirpath]
        self.logger.debug("caching listing of "+dirpath)
        if self.current_cache_dir != os.path.dirname(dirpath):
            self.current_cache_dir = os.path.dirname(dirpath)
            current_dir_listing =  self.get_directory_listing(self.current_cache_dir)
            current_dir_listing.remove(dirpath)
            for path in current_dir_listing:
                t = Thread(target=self.get_images, args=(path,))
                t.start()
        mangaurlpart = self.get_mangaurlpart_from_path(dirpath)
        first_letter_of_manga = mangaurlpart[0]
        chapter = os.path.basename(dirpath)
        url =  self.host + '/manga/' + first_letter_of_manga + '/' + mangaurlpart +'/'+'chapter/'+chapter
        self.logger.debug("get images from. "+url)
        f = urllib2.urlopen(url)
        if f.code != 200:
            raise Exception("Abort with status code: " + f.code, 0)
        html = f.read()
        mangaurlpart = mangaurlpart.replace('(', '\(')
        mangaurlpart = mangaurlpart.replace(')', '\)')
        pattern = 'href=".*?/'+first_letter_of_manga+'/'+mangaurlpart+'/'+'chapter/'+chapter+'/(.*?)"' #/manga/O/One_Piece/chapter/10/24
        self.logger.debug("get images pattern. "+pattern)
        images = re.findall(pattern,html,re.MULTILINE | re.IGNORECASE)
        self.imgcache[dirpath] = images
        return images
        
        
    def get_directory_listing(self, directory):
        def add_directory_prefix(x): return directory+'/'+x;
        self.logger.debug("getting directory listing for "+directory)
        self._raise_error_if_invalid_path(directory)
        if directory == "/":
            return list(self.mangas.keys())
        try:
            if self.is_chapterpath(directory):
                self.logger.debug("get listing images")
                return map(add_directory_prefix, self.get_images(directory))
            return map(add_directory_prefix, self.get_chapters(directory))
        except Exception, e:
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
            ret["modified"] = time.time()
            ret["created"] = time.time()
            ret["path"] = "/"
            ret["is_dir"] = True
            return ret;
        
        manga = self.get_mangapart_from_path(path)
        if self.is_filepath(path):
            self.logger.debug("is filepath ")
            ret = {}
            if self.imgcache.has_key(path):
                ret["bytes"] = len(self.imgcache[path])
            else:
                ret["bytes"] = 10000000
            ret["modified"] = time.time()-60
            ret["created"] = time.time()-60
            ret["path"] = path
            ret["is_dir"] = False
            return ret
        elif not manga in self.mangas:
            raise NoSuchFilesytemObjectError("",0)
        else:
            self.logger.debug("getting manga path for "+manga)
            ret = {}
            ret["bytes"] = 0
            ret["modified"] = time.time()-60
            ret["created"] = time.time()-60
            ret["path"] = path
            ret["is_dir"] = True
            return ret;
    
    def get_logging_handler(self):
        return self._logging_handler
    
        












