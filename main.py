import tornado.ioloop
import tornado.web
import os
from conf import *


class Thumbs():
    pass


class GenerateFileList():
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
        """
        for f in os.listdir(path):
            (name, ext) = os.path.splitext(f)
            if os.path.isfile(os.path.join(path, f)) and self.check_extension(f):
                self.file_list[f] = os.path.join(path, f)
        if len(self.file_list):
            return self.file_list
        else:
            return None

    def walk(self, path=''):
        """
        return dict of dirs from 'path' that contain permited files
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
        for sh_path in PATHS:
            if not sh_path in path:
                return False
        return True

    def ls(self, path=''):
        """
        return verified dirs and files of 'path'
        """
        if self.check_integrity(path):
            return [self.walk(path), self.get_file_list(path)]
        else:
            return 'error'


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        gfl = GenerateFileList()
        path = self.get_argument("q", None)
        if path:
            (dir_list, file_list) = gfl.ls(path)
        else:
            (dir_list, file_list) = gfl.ls(PATHS[0])
        self.render("templates/base.html",
                    dir_list=dir_list,
                    file_list=file_list,
                    title="smp")


app = tornado.web.Application(
    [(r"/", MainHandler), ]
)

if __name__ == '__main__':
    app.listen(9999)
    tornado.ioloop.IOLoop.instance().start()
    # gfl = GenerateFileList()
    # gfl.walk(PATHS[0])
    # print(gfl.photo_dirs)
