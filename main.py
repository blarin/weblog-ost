#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import webapp2
import jinja2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=["jinja2.ext.autoescape"],
    autoescape=True)

class MainHandler(webapp2.RequestHandler):

    def get(self):
        if users.get_current_user():
          login_url = users.create_logout_url(self.request.uri)
          login_message = "Logout"
          user_name = users.get_current_user()
        else:
          login_url = users.create_login_url(self.request.uri)
          login_message = "You Must Login"
          user_name = ""

        values = {
          "login_url": login_url,
          "login_message": login_message,
          "user_name": user_name
        }

        template = JINJA_ENVIRONMENT.get_template("index.html")
        self.response.write(template.render(values))

def blog_key(blog_name):
  return ndb.Key("Blog", blog_name)

class BlogPost(ndb.Model):

  author = ndb.UserProperty()
  title = ndb.StringProperty(indexed=False)
  content = ndb.StringProperty(indexed=False)
  tags = ndb.StringProperty(indexed=False)
  date = ndb.DateTimeProperty(auto_now_add=True)

class BlogHandler(webapp2.RequestHandler):

  def get(self):
    last_slash = self.request.url.rfind("/") + 1
    blog_name = self.request.url[last_slash::]

    if users.get_current_user() and blog_name != "":
      login_url = users.create_logout_url(self.request.uri)
      login_message = "Logout"
      user_name = users.get_current_user()
    else:
      self.redirect("/")
      return

    query = BlogPost.query(
        ancestor=blog_key(blog_name)).order(-BlogPost.date)
    blog_posts = query.fetch(10)

    values = {
      "blog_posts": blog_posts,
      "login_url": login_url,
      "login_message": login_message,
      "user_name": user_name,
      "blog_name": blog_name
    }

    template = JINJA_ENVIRONMENT.get_template("blog.html")
    self.response.write(template.render(values))        

class WriteHandler(webapp2.RequestHandler):

  def post(self):
    blog_name = self.request.get("blog_name")

    if users.get_current_user() and blog_name != "":
      blog_post = BlogPost(parent=blog_key(blog_name))
      blog_post.author = users.get_current_user()
    else:
      self.redirect("/")
      return

    blog_post.title = self.request.get("title")
    blog_post.content = self.request.get("content")
    blog_post.put()

    query_params = {"name": blog_name}
    self.redirect("/blog/" + blog_name)


class ArticleHandler(webapp2.RequestHandler):

  def get(self):
    # last_slash = self.request.url.rfind("/") + 1
    # blog_name = self.request.url[last_slash::]


    # if users.get_current_user() and blog_name != "":
    #   login_url = users.create_logout_url(self.request.uri)
    #   login_message = "Logout"
    #   user_name = users.get_current_user()
    # else:
    #   self.redirect("/")
    #   return

    # values = {
    #   "login_url": login_url,
    #   "login_message": login_message,
    #   "user_name": user_name,
    #   "blog_name": blog_name
    # }
    values = {
          "troll": "alot"
        }

    template = JINJA_ENVIRONMENT.get_template("article.html")
    self.response.write(template.render(values)) 

app = webapp2.WSGIApplication([
  ("/blog/.*/write", WriteHandler),
  ("/blog/article/.*", ArticleHandler),
  ("/blog/.*", BlogHandler),
  ("/.*", MainHandler)
], debug=True)
