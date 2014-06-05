#! /usr/bin/env python
#-*- coding:utf-8 -*-



import tornado.httpserver
import tornado.options
import tornado.ioloop



from handlers import *

from tornado.options import define, options
define("port", default=8888, help="run on given port", type=int)
define("mysql_host", default="127.0.0.1:3306")
define("mysql_database", default="writeit")
define("mysql_user", default="root")
define("mysql_password", default="123456")


class Application(tornado.web.Application):
    def __init__(self):
        handlers= [
            (r"/", HomeHandler),
            (r"/auth/login", AuthLoginHandler),
            (r"/about", AboutHandler),
            (r"/write/([^/]*)", WriteHandler),
            (r"/archive", ArchiveHandler),
            (r"/entry", EntryHandler),
            (r"/entry/([^/]+)", EntryHandler),
            (r"/ajax/parse", ParseHandler), #takes markdown input, returns html
            (r"/ajax/get-slug", SlugHandler),
            (r"/ajax/markdown/([^/]+)", MarkdownHandler),
            (r"/ajax/removeEntry/([^/]+)", RemoveEntryHandler),
            (r"/ajax/autoTag", AutoTagHandler),
            (r"/tags", TagsHandler),
            (r"/tag/([^/]+)", TagHandler),
            (r".*", BaseHandler)
        ]

        settings=dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            cookie_secret="afasfadsfdsfqwrwegefeqwrsd",
            login_url="/auth/login",
            debug=True
        )

        tornado.web.Application.__init__(self, handlers, **settings)

        self.db = torndb.Connection(
            host=options.mysql_host, database=options.mysql_database,
            user=options.mysql_user, password=options.mysql_password)





def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
