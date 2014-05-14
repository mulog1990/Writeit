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
            (r"/about", AboutHandler),
            (r"/write/([^/]*)", WriteHandler),
            (r"/archive", ArchiveHandler),
            (r"/entry", EntryHandler),
            (r"/entry/([^/]+)", EntryHandler),
            (r"/ajax/parse", ParseHandler), #takes markdown input, returns html
            (r"/ajax/get-slug", SlugHandler),
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

class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db
    
    def get_current_user(self):
        user = self.get_secure_cookie("user")
        if not user:
            return None
        return user


    def get(self):
        self.write_error(404)

    def write_error(self, status_code, **kwargs):
        self.render("error.html", status_code=status_code)


class ParseHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        md = self.get_argument("markdown","")
        self.write(markdown.markdown(md, extensions=["fenced_code"]))
#self.write(markdown.markdown(unicode(md, "utf-8")))

class AboutHandler(BaseHandler):
    def get(self):
        self.render("about.html")

class WriteHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, param):
        #entry_id = self.get_argument("id", None)
        slug = param
        entry = None
        tags = None
        if slug:
            entry = query.get_entry_by_slug(self.db, slug) 
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
        markdown_id = query.save_markdown(db=self.db, 
                markdown=self.get_argument("markdown", ""),
                slug=slug
        )
        

        #create new entry or   
        #update curent_markdown for existing entry
        new = False

        if slug:
            query.update_entry(
                self.db,
                title,
                int(markdown_id),
                new_slug,
                slug
            )

        else:
            #new entry
            user_email = self.get_secure_cookie("user")
            query.create_entry(self.db, title, markdown_id,\
                    new_slug, user_email)
        
        #save tags
        query.update_tags(self.db, new_slug, tags)

        self.redirect("/entry/" + new_slug)

class ArchiveHandler(BaseHandler):
    def get(self):
        import datetime
        earliest_year = query.get_earliest_year(self.db).year
        current_year = datetime.datetime.today().year
        archive = {}
        for year in range (earliest_year, current_year + 1):
            archive[year] = query.get_entries_by_year(self.db, year)
        self.render("archive.html", archive=archive)
        
       

class EntryHandler(BaseHandler):
    def render_self(self, entry):
        #convert stored markdown to html for output
        html = markdown.markdown(entry["markdown"], extensions=["fenced_code"])
        entry["html"] = html
        del entry["markdown"]
        
        #get tags for current entry
        entry["tags"] = query.get_tags(self.db, entry["entry_id"])
        
        neighbors = query.get_neighbor_entries(self.db, entry["entry_id"])
        user = self.get_current_user()
 
        self.render("entry.html", entry=entry, neighbors=neighbors, user=user)

# def get(self):
#       entry = None
#entry_id = self.get_argument("entry_id", None)
#       if entry_id:
#           entry = self.db.get("SELECT * FROM entry_v where entry_id=%s",
#                 int(entry_id))
#           render_self(entry)

    def get(self, param):
        entry = None
        if param:
            slug = param
            entry = query.get_entry_by_slug(self.db, slug)
            self.render_self(entry)
        else:
            self.write("This should not happen")


class AutoTagHandler(BaseHandler):
    def get(self):
        text = self.get_argument("markdown", None)
        if text:
            self.write(",".join(utils.auto_tag(text)))
            
        self.finish()



        
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
        entries = query.get_fresh_entries(self.db, 3)
        new = self.get_arguments("new", None)
        for entry in entries:
            entry["summary"] = utils.strip_html(
                    markdown.markdown(entry["markdown"])
            )
            #show abstract only
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
            query.remove_entry(self.db, slug)
            self.write("OK")
        else:
            self.write("Does not exist")


class SlugHandler(BaseHandler):
    #finds available slug
    def get(self):
        slug = self.get_argument("slug", None)
        if not slug:
            slug = "no-slug"
        slug = slug.replace(u" ", u"-")
        
        #append proper sequence number to avoid conflict
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
