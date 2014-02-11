#! /usr/bin/env python
import os.path

import torndb

import tornado.auth
import tornado.httpserver
import tornado.options
import tornado.ioloop
import tornado.web

import markdown


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
            (r"/test", TestHandler),
            (r"/write", WriteHandler),
            (r"/entry", EntryHandler),
            (r"/removeEntry", RemoveEntryHandler)
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

class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db
    
    def get_current_user(self):
        user = self.get_secure_cookie("user")
        if not user:
            return None
        return user

class TestHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("index.html")

class WriteHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        entry_id = self.get_argument("id", None)
        entry = None
        if entry_id:
            entry = self.db.get("SELECT * FROM entry_v WHERE entry_id = %s", int(entry_id)) 
            print entry["markdown"]
        self.render("write.html", entry=entry)

    @tornado.web.authenticated
    def post(self):
        entry_id = self.get_argument("id", None)
        title = self.get_argument("title", "Untitled")

        #save markdown
        self.db.execute(
               "INSERT INTO markdowns SET markdown=%s",
                self.get_argument("markdown", ""),
                )
        
        markdown_id = int(self.db.execute("SELECT LAST_INSERT_ID()"))
        
        #create new entry or   
        #update curent_markdown for existing entry
        
        if entry_id:
            self.db.execute(
                "UPDATE entries SET title=%s,markdown_id=%s where entry_id=%s",
                self.get_argument("title","untitled"),
                int(markdown_id),
                int(entry_id)
            )
        else:
            #new entry
            user_email = self.get_secure_cookie("user")
            self.db.execute(
                "INSERT INTO entries SET title=%s,markdown_id=%s,slug=%s,author_id=(\
                SELECT id FROM users WHERE email=%s)",
                title,markdown_id,'-'.join(title.split()),user_email
            )
        self.write("Post Successfully Published!")

       

class EntryHandler(BaseHandler):
    def get(self):
        entry_id = self.get_argument("entry_id", None)
        entry = None
        if entry_id:
            entry = self.db.get("SELECT * from entry_v where entry_id=%s",
                    int(entry_id))
        self.render("entry.html", entry=entry)



        
class AuthLoginHandler(BaseHandler, tornado.auth.GoogleMixin):
    @tornado.web.asynchronous
    def get(self):
        if self.get_argument("openid.mode", None):
            self.get_authenticated_user(self.async_callback(self._on_auth))
            return
        self.authenticate_redirect() 

    def _on_auth(self, user):
        if not user:
            raise tornado.web.HTTPError(500, "Google auth failed")
        print "username: " + user["name"]
        self.set_secure_cookie("user", user["email"])
        self.redirect(self.get_argument("next","/"))
    
class HomeHandler(BaseHandler):
    def get(self):
        entries = self.db.query("select * from entry_v order by entry_id desc limit 10")
        for entry in entries:
            entry["html"] = markdown.markdown(entry["markdown"])
        self.render("index.html",entries=entries)


class RemoveEntryHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        entry_id = self.get_argument("id", None)
        if entry_id:
            self.db.execute("DELETE FROM entries WHERE id=%s", entry_id)
            self.write("OK")
        else:
            self.write("Does not exist")



def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
