from PIL import Image
import socket
import os
import simplejson
from conf import *


def get_blank():
    """
    return blank image in case:
    1. image doesn't exist
    2. is a directory
    """
    f = open(os.path.join(APP_ROOT, 'static/img/blank.jpg'))
    return f


class GenerateFileList(object):
    def __init__(self):
        self.photo_dirs = {}
        self.file_list = {}

    def check_extension(self, f=''):
        """
        check if extension of 'f' is listed in conf file
        """
        for extension in PHOTO_EXTENSIONS:
            (name, ext) = os.path.splitext(f)
            if extension.lower() in ext or extension.upper() in ext:
                return True

    def check_include_photo(self, path=''):
        """
        check if folder contain files with permitted extensions
        """
        # iterate over dir's files
        for f in os.listdir(path):
            # check file is photo
            self.check_extension(os.path.join(path, f))

    def get_file_list(self, path=''):
        """
        return dict of permitted files of a dir - 'path'
        { 'file_name(no ext)': 'file/path', }
        """
        for f in os.listdir(path):
            (name, ext) = os.path.splitext(f)
            if os.path.isfile(os.path.join(path, f)) and self.check_extension(f):
                self.file_list[name] = os.path.join(path, f)
        if len(self.file_list):
            return self.file_list
        else:
            return None

    def walk(self, path=''):
        """
        return dict of dirs from 'path' that contain permitted files
        { 'dir_name': 'dir_path', }
        """
        for ff in os.listdir(path):
            if os.path.isdir(os.path.join(path, ff)) and not ff[0] == '.':
                self.photo_dirs[ff] = os.path.join(path, ff)
        if len(self.photo_dirs):
            return self.photo_dirs
        else:
            return None

    def check_integrity(self, path=''):
        """
        check if path is not root dir of paths listed in conf file
        """
        if PHOTO_PATH in path:
            return True
        return False

    def get_root_path(self, path=''):
        """
        return root dir
        """
        (root_path, path_name) = os.path.split(path)
        if self.check_integrity(root_path):
            return root_path, path_name
        else:
            return False

    def ls(self, path=''):
        """
        return verified dirs and files of 'path'
        """
        if self.check_integrity(path):
            return [self.walk(path), self.get_file_list(path)]
        else:
            return [self.walk(PHOTO_PATH), self.get_file_list(PHOTO_PATH)]


class ItemInfo(object):
    """fetch info about directories/files"""
    def __init__(self, path):
        self.path = path
        self.count = {}
        self.gfl = GenerateFileList()

    def get_count(self):
        (dir_list, file_list) = self.gfl.ls(self.path)
        return {'dir_count': len(dir_list) if dir_list else 0,
                'file_count': len(file_list) if file_list else 0}


class FileInfoDictAssembler(GenerateFileList):
    def __init__(self, *args, **kwargs):
        self.path = kwargs.pop('item_path', None)
        super(FileInfoDictAssembler, self).__init__(*args, **kwargs)

    def fetch(self):
        # list
        (dir_list, file_list) = self.ls(self.path)
        # reorganize
        if dir_list:
            for key in dir_list:
                ii = ItemInfo(dir_list[key])
                dir_list[key] = {'path': dir_list[key]}
                dir_list[key] = dict(dir_list[key], **ii.get_count())
        if file_list:
            for key in file_list:
                file_list[key] = {'path': file_list[key]}
        return [dir_list, file_list]


class GeneralInfo():
    def get_hostname(self):
        return socket.gethostname()


class Thumbs():
    """
    create and provide thumbs for requested images
    """
    def __init__(self, path):
        self.path = path
        self.gfl = GenerateFileList()
        self.root_path = os.path.split(self.path)[0]
        self.filename = os.path.split(self.path)[1]

    def create_thumb_dir(self):
        if not os.path.isdir(os.path.join(self.root_path, THUMB_DIR)):
            os.makedirs(os.path.join(self.root_path, THUMB_DIR))

    def create_thumb(self):
        if self.gfl.check_extension(self.path):
            im = Image.open(self.path)
            im_resize = im.resize(THUMB_SIZE, Image.ANTIALIAS)
            # create dir if not exist
            self.create_thumb_dir()
            im_resize.save(os.path.join(self.root_path, os.path.join(THUMB_DIR, self.filename)))
            f = open(os.path.join(self.root_path, os.path.join(THUMB_DIR, self.filename)))
        else:
            f = get_blank()
        return f

    def open_thumb(self):
        try:
            f = open(os.path.join(self.root_path, os.path.join(THUMB_DIR, self.filename)))
        except:
            f = False
        return f

    def get_thumb(self):
        if os.path.isfile(self.path):
            thumb = self.open_thumb()
        else:
            thumb = get_blank()
        return thumb