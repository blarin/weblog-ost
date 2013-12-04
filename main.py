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

import os
import urllib
import re

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
        user_name = users.get_current_user().nickname()
        user_id = users.get_current_user().user_id()
        blogs_query = Blog.query().filter(Blog.author == user_id).order(-Blog.date)
        blogs = blogs_query.fetch(10)
        other_blogs_query = Blog.query().filter(Blog.author != user_id).order(Blog.author).order(-Blog.date)
        other_blogs = other_blogs_query.fetch(10)
      else:
        login_url = users.create_login_url(self.request.uri)
        login_message = "You Must Login"
        user_name = ""
        blogs = []
        other_blogs = []

      values = {
        "blogs": blogs,
        "other_blogs": other_blogs,
        "login_url": login_url,
        "login_message": login_message,
        "user_name": user_name
      }

      template = JINJA_ENVIRONMENT.get_template("templates/index.html")
      self.response.write(template.render(values))

class BlogHandler(webapp2.RequestHandler):

  def get(self,blog_name):
    if users.get_current_user() and blog_name != "":
      login_url = users.create_logout_url(self.request.uri)
      login_message = "Logout"
      user_name = users.get_current_user().nickname()
      user_id = users.get_current_user().user_id()
    else:
      self.redirect("/")
      return

    # it would be nice if this would work  
    #blog_query = Blog.query(ancestor=blog_key(user_id)).order(-Blog.date)
    blog_query = Blog.query(ancestor=blog_key(user_id)).filter(Blog.name == blog_name)
    blog = blog_query.get()

    if not blog:
      blog_query = Blog.query().filter(Blog.name == blog_name)
      blog = blog_query.get()      

    query = Article.query(ancestor=article_key(blog_name)).order(-Article.date)
    articles = query.fetch(10)

    for article in articles[:]:
      if len(article.content) > 500:
        article.abbreviated_content = article.content[:497] + "..."
      else:
        article.abbreviated_content = article.content

    values = {
      "blog": blog,
      "articles": articles,
      "login_url": login_url,
      "login_message": login_message,
      "user_name": user_name,
      "user_id": user_id,
      "blog_name": blog_name,
    }

    template = JINJA_ENVIRONMENT.get_template("templates/blog.html")
    self.response.write(template.render(values))        

def blog_key(author):
  return ndb.Key("Author", author)

class Blog(ndb.Model):

  author = ndb.StringProperty()
  author_name = ndb.StringProperty()
  name = ndb.StringProperty()
  date = ndb.DateTimeProperty(auto_now_add=True)

class AddBlogHandler(webapp2.RequestHandler):

  def post(self):
    blog_name = self.request.get("blog_name")

    blog_query = Blog.query().filter(Blog.name == blog_name)
    blog = blog_query.get()
    user_id = users.get_current_user().user_id()
    user_name = users.get_current_user().nickname()

    if user_name and blog_name != "" and blog is None:
      blog = Blog(parent=blog_key(user_id))
      blog.author = user_id
      blog.author_name = user_name
    else:  
      self.redirect("/")
      return

    blog.name = blog_name
    blog.put()

    self.redirect("/blog/" + blog_name)

def article_key(blog_name):
  return ndb.Key("Blog", blog_name)

class Article(ndb.Model):

  author = ndb.StringProperty()
  author_name = ndb.StringProperty()
  blog_name = ndb.StringProperty()
  title = ndb.StringProperty()
  content = ndb.StringProperty(indexed=False)
  tags = ndb.StringProperty(indexed=False)
  date = ndb.DateTimeProperty(auto_now_add=True)

class WriteHandler(webapp2.RequestHandler):

  def post(self):
    blog_name = self.request.get("blog_name")

    if users.get_current_user() and blog_name != "":
      article = Article(parent=article_key(blog_name))
      article.author = users.get_current_user().user_id()
      article.author_name = users.get_current_user().nickname()
      article.blog_name = blog_name
    else:
      self.redirect("/")
      return

    article.title = self.request.get("title")
    article.content = self.request.get("content")
    article.put()

    self.redirect("/blog/" + blog_name + "/article/" + article.title);

class ArticleHandler(webapp2.RequestHandler):

  def get(self, blog_name, article_name):
    if users.get_current_user() and blog_name != "":
      login_url = users.create_logout_url(self.request.uri)
      login_message = "Logout"
      user_id = users.get_current_user().user_id()
      user_name = users.get_current_user().nickname()
    else:
      self.redirect("/")
      return

    article_query = Article.query(ancestor=article_key(blog_name)).filter(Article.title == article_name)
    article = article_query.get()

    values = {
      "login_url": login_url,
      "login_message": login_message,
      "user_name": user_name,
      "user_name": user_name,
      "user_id": user_id,
      "blog_name": blog_name,
      "article": article
    }

    template = JINJA_ENVIRONMENT.get_template("templates/article.html")
    self.response.write(template.render(values)) 

app = webapp2.WSGIApplication([
  ("/addblog", AddBlogHandler),
  ("/blog/.*/write", WriteHandler),
  ("/blog/(.*)/article/(.*)", ArticleHandler),
  ("/blog/(.*)", BlogHandler),
  ("/.*", MainHandler)
], debug=True)
