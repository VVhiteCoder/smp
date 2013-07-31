import tornado.ioloop
import tornado.web
import tornado.httpserver
from tornado.options import define, options
from PIL import Image
import os
from conf import *

define('port', default=9999, help="run on port 9999", type=int)


def get_blank():
    """
    return blank image in case:
    1. image doesn't exist
    2. is a directory
    """
    f = open(os.path.join(APP_ROOT, 'static/img/blank.jpg'))
    return f


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


class Thumbs():
    """
    create and provide thumbs for request images
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
        return open(os.path.join(self.root_path, os.path.join(THUMB_DIR, self.filename)))

    # def open_thumb(self):
    #     try:
    #         f = open(os.path.join(self.root_path, os.path.join(THUMB_DIR, self.filename)))
    #     except:
    #         f = self.create_thumb()
    #     return f

    def get_thumb(self):
        if os.path.isfile(self.path):
            thumb = self.open_thumb()
        else:
            thumb = get_blank()
        return thumb

################################# RequestHandlers ####################################


class MainHandler(tornado.web.RequestHandler):
    """top main url"""
    def get(self, path=None):
        gfl = GenerateFileList()
        # path = self.get_argument("q", None)
        if path:
            p = path if path[0] == '/' else '/' + path
            (dir_list, file_list) = gfl.ls(p)
            root_path = gfl.get_root_path(p)
        else:
            root_path = None
            (dir_list, file_list) = gfl.ls(PHOTO_PATH)

        self.render("base.html",
                    dir_list=dir_list,
                    file_list=file_list,
                    root_path=root_path,
                    title="smp")


class ThumbsHandler(tornado.web.RequestHandler):
    """get thumbs """
    def __init__(self, *args, **kwargs):
        self.gfl = GenerateFileList()
        super(ThumbsHandler, self).__init__(*args, **kwargs)

    # def open_file(self, path):
    #     self.thumb = Thumbs(path)
    #     if self.gfl.check_integrity(path) and os.path.isfile(self.path):
    #         thumb = self.thumb.get_thumb()
    #     else:
    #         thumb = get_blank()
    #     return thumb

    def get(self, path=None):
        self.set_header('Content-type', 'image/' + os.path.splitext(path)[1].replace('.', ''))

        self.thumb = Thumbs(path)
        if self.gfl.check_integrity(path) and os.path.isfile(path):
            try:
                thumb = self.thumb.get_thumb()
            except:
                thumb = self.thumb.create_thumb()
        else:
            thumb = get_blank()

        self.write(thumb.read())


#
# class ThumbsHandler(tornado.web.RequestHandler):
#     """get thumbs """
#     def __init__(self, *args, **kwargs):
#         self.gfl = GenerateFileList()
#         super(ThumbsHandler, self).__init__(*args, **kwargs)
#
#     def open_file(self, path):
#         self.thumb = Thumbs(path)
#         if self.gfl.check_integrity(path):
#             thumb = self.thumb.get_thumb()
#         else:
#             thumb = get_blank()
#         return thumb
#
#     def get(self, path=None):
#         self.set_header('Content-type', 'image/' + os.path.splitext(path)[1].replace('.', ''))
#         self.write(self.open_file(path).read())

class DownloadHandler(tornado.web.RequestHandler):
    """
    download file, asynchronously
    """
    def __init__(self, *args, **kwargs):
        self.gfl = GenerateFileList()
        super(DownloadHandler, self).__init__(*args, **kwargs)

    def open_file(self, path):
        if self.gfl.check_integrity(path):
            f = open(path, 'r')
        else:
            f = get_blank()
        return f

    # @tornado.web.asynchronous
    def get(self, path=None):
        self.set_header('Content-type', 'image/' + os.path.splitext(path)[1].replace('.', ''))
        self.write(self.open_file(path).read())
        # self.finish()


app = tornado.web.Application(
       [
        (r"/smp_thumb([^$]+)", ThumbsHandler),
        (r"/download([^$]+)", DownloadHandler),
        (r"/", MainHandler),
        (r"/([^$]+)", MainHandler)
        ],
    template_path=os.path.join(os.path.dirname(__file__), 'templates'),
    static_path=os.path.join(os.path.dirname(__file__), 'static'),
    debug=True
)

if __name__ == '__main__':
    # app.listen(9999)
    #################
    options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
    #####################
    # gfl = GenerateFileList()
    # gfl.walk(PATHS[0])
    # print(gfl.photo_dirs)