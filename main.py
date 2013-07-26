import tornado.ioloop
import tornado.web
import os
from conf import *


class GenerateFileList():
    def __init__(self):
        self.photo_dirs = {}
        self.file_list = {}

    def check_extension(self, f=''):
        for extension in PHOTO_EXTENSIONS:
            (name, ext) = os.path.splitext(f)
            if extension.lower() in ext or extension.upper() in ext:
                return True

    def check_include_photo(self, path=''):
        # iterate over dir's files
        for f in os.listdir(path):
            # check file is photo
            self.check_extension(os.path.join(path, f))

    def get_file_list(self, path=''):
        for f in os.listdir(path):
            (name, ext) = os.path.splitext(f)
            if os.path.isfile(os.path.join(path, f)) and self.check_extension():
                self.file_list[f] = os.path.join(path, f)
        return self.file_list

    def walk(self, path=''):
        for ff in os.listdir(path):
            if os.path.isdir(os.path.join(path, ff)) and not ff[0] == '.':
                self.photo_dirs[ff] = os.path.join(path, ff)
        return self.photo_dirs

    def check_integrity(self, path=''):
        for sh_path in PATHS:
            if not sh_path in path:
                return False
        return True

    def ls(self, path=''):
        if self.check_integrity(path):
            pass
        else:
            return 'error'


    # def walk(self, path=''):
    #     for r, d, f in os.walk(path):
    #         self.dirs.append(r)
    #     for d in self.dirs:
    #         if self.check_include_photo(d):
    #             (path, dirname) = os.path.split(d)
    #             if not dirname[0] == '.':
    #                 self.photo_dirs[dirname] = d
    #     return self.photo_dirs

    # def get_dirlist(self, path=''):
    #     pass


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        gfl = GenerateFileList()
        file_name = self.get_argument("q", None)
        if file_name:
            dir_list = gfl.walk(file_name)
        else:
            dir_list = gfl.walk(PATHS[0])
        self.render("templates/base.html", dir_list=dir_list, title="smp")


app = tornado.web.Application(
    [(r"/", MainHandler), ]
)

if __name__ == '__main__':
    app.listen(9999)
    tornado.ioloop.IOLoop.instance().start()
    # gfl = GenerateFileList()
    # gfl.walk(PATHS[0])
    # print(gfl.photo_dirs)
