import tornado.ioloop
import tornado.gen
import tornado.web
import tornado.httpserver
from tornado.options import define, options
import os
from conf import *
from file_handler import get_blank, GenerateFileList, Thumbs, FileInfoDictAssembler

define('port', default=9999, help="run on port 9999", type=int)

################################# RequestHandlers ####################################
# class DirCountHandler(tornado.web.RequestHandler):
#     """count contained dirs and files of a path"""
#     def __init__(self, *args, **kwargs):
#         self.gfl = GenerateFileList()
#         super(DirCountHandler, self).__init__(*args, **kwargs)
#
#     def get(self, path=None):
#         p = path if path[0] == '/' else '/' + path
#         (dir_list, file_list) = self.gfl.ls(p)
#         self.write(simplejson.dumps({'dir_count': len(dir_list), 'file_count': len(file_list)}))


class MainHandler(tornado.web.RequestHandler):
    """top main url"""
    def get(self, path=None):
        gfl = GenerateFileList()
        # path = self.get_argument("q", None)
        if path:
            p = path if path[0] == '/' else '/' + path
            fida = FileInfoDictAssembler(item_path=p)
            (dir_list, file_list) = fida.fetch()
            root_path = gfl.get_root_path(p)
        else:
            root_path = None
            fida = FileInfoDictAssembler(item_path=PHOTO_PATH)
            (dir_list, file_list) = fida.fetch()

        self.render("base.html",
                    dir_list=dir_list,
                    file_list=file_list,
                    root_path=root_path,
                    title="smp")


class ThumbsHandler(tornado.web.RequestHandler):
    """get thumbs asynchronous"""
    def __init__(self, *args, **kwargs):
        self.gfl = GenerateFileList()
        self.thumb_image = None
        super(ThumbsHandler, self).__init__(*args, **kwargs)

    def get_thumb(self):
        self.thumb_image = self.thumb_obj.get_thumb()

    def create_thumb(self):
        self.thumb_image = self.thumb_obj.create_thumb()

    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self, path=None):
        self.set_header('Content-type', 'image/' + os.path.splitext(path)[1].replace('.', ''))
        self.thumb_obj = Thumbs(path)

        if self.gfl.check_integrity(path) and os.path.isfile(path):
            if self.thumb_obj.open_thumb():
                self.get_thumb()
                self.write(self.thumb_image.read())
                self.finish()
            else:
                tornado.gen.Task(self.create_thumb())
                tornado.gen.Task(self.get_thumb())
                self.write(self.thumb_image.read())
                self.finish()
        else:
            self.thumb_image = get_blank()
            self.write(self.thumb_image.read())
            self.finish()


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

    @tornado.web.asynchronous
    def get(self, path=None):
        self.set_header('Content-type', 'image/' + os.path.splitext(path)[1].replace('.', ''))
        self.write(self.open_file(path).read())
        self.finish()


app = tornado.web.Application(
       [#(r"/smp_count([^$]+)", DirCountHandler),
        (r"/smp_thumb([^$]+)", ThumbsHandler),
        (r"/smp_download([^$]+)", DownloadHandler),
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