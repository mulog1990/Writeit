#! /usr/bin/env python
#-*- coding:utf-8 -*-
import os.path

import torndb

import tornado.auth
import tornado.httpserver
import tornado.options
import tornado.ioloop
import tornado.web

import markdown
import utils
import query

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
            (r"/write/([^/]*)", WriteHandler),
            (r"/entry", EntryHandler),
            (r"/entry/([^/]+)", EntryHandler),
            (r"/ajax/parse", ParseHandler),           #takes markdown input, returns html
            (r"/ajax/get-slug", SlugHandler),
            (r"/ajax/removeEntry/([^/]+)", RemoveEntryHandler),
            (r"/tags", TagsHandler),
            (r"/tag/([^/]+)", TagHandler),
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

class ParseHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        md = self.get_argument("markdown","")
        self.write(markdown.markdown(md))
#self.write(markdown.markdown(unicode(md, "utf-8")))

class TestHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("index.html")

class WriteHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, param):
        #entry_id = self.get_argument("id", None)
        slug = param
        entry = None
        tags = None
        if slug:
            entry = self.db.get("SELECT * FROM entry_v WHERE slug=%s", slug) 
            entry["tags"] = query.get_tags(self.db, entry["entry_id"])
        self.render("write.html", entry=entry)

    @tornado.web.authenticated
    def post(self, param):
        title = self.get_argument("title", "Untitled")
        new_slug = self.get_argument("new-slug", None)
        tags = self.get_argument("tags", None)
        if tags:
            tags = tags.split(",")

        slug = param

        #save markdown
        self.db.execute(
               "INSERT INTO markdowns SET markdown=%s",
                self.get_argument("markdown", ""),
                )
        
        markdown_id = int(self.db.execute("SELECT LAST_INSERT_ID()"))
        
 
        #create new entry or   
        #update curent_markdown for existing entry
        new = False

        if slug:
            self.db.execute(
                "UPDATE entries SET title=%s,markdown_id=%s,slug=%s where slug=%s",
                self.get_argument("title","untitled"),
                int(markdown_id),
                new_slug,
                slug)
        else:
            #new entry
            user_email = self.get_secure_cookie("user")
            self.db.execute(
                "INSERT INTO entries SET title=%s,markdown_id=%s,slug=%s,author_id=(\
                SELECT id FROM users WHERE email=%s)",
                title,markdown_id,new_slug,user_email
            )

        #save tags
        query.update_tags(self.db, new_slug, tags)

        self.redirect("/entry/" + new_slug)

       

class EntryHandler(BaseHandler):
    def render_self(self, entry):
        html = markdown.markdown(entry["markdown"], extensions=["fenced_code"])
        entry["html"] = html
        del entry["markdown"]
        entry["tags"] = self.db.query("SELECT tag FROM tag_v WHERE entry_id=%s",
                int(entry["entry_id"]))

        neighbors = query.get_neighbor_entries(self.db, entry["entry_id"])
        print neighbors

        self.render("entry.html", entry=entry, neighbors=neighbors)

    def get(self):
        entry = None
        entry_id = self.get_argument("entry_id", None)
        if entry_id:
            entry = self.db.get("SELECT * FROM entry_v where entry_id=%s",
                  int(entry_id))
            render_self(entry)

    def get(self, param):
        entry = None
        if param:
            slug = param
            entry = self.db.get("SELECT * FROM entry_v where slug=%s", slug)
            self.render_self(entry)
        else:
            self.write("What the fuck")


            



        
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
        new = self.get_arguments("new", None)
        for entry in entries:
            entry["summary"] = utils.strip_html(markdown.markdown(entry["markdown"]))
            if len(entry["summary"]) > 300:
                entry["summary"] = entry["summary"][:300]
            entry["date"] = entry["published"]

        user = self.get_current_user()
        
        
        args = locals()
        args.pop('self')
        self.render("index.html", **args)


class RemoveEntryHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, param):
        slug = param
        if slug:
            self.db.execute("DELETE FROM entries WHERE slug=%s", slug)
            self.write("OK")
        else:
            self.write("Does not exist")


class SlugHandler(BaseHandler):
    def get(self):
        slug = self.get_argument("slug", None)
        if not slug:
            slug = "no-name-dumbass"
        slug = slug.replace(u" ", u"-")
        if not query.check_slug(self.db, slug):
            seq = 2
            slug += "-"
            slug += str(seq)
            while not query.check_slug(self.db, slug):
                seq += 1
            slug = slug[:-1]
            slug += str(seq)
        self.write(slug)


class TagsHandler(BaseHandler):
    def get(self):
        tags = query.get_all_tags(self.db)
        self.render("tags.html", tags=tags)

class TagHandler(BaseHandler):
    def get(self, param):
        tag = param
        entries = query.get_entries_by_tag(self.db, tag)
        utils.attach_summary(entries)
        user = self.get_current_user()
        self.render("tag.html", entries=entries, user=user, tag=tag)

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
