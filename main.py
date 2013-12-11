#!/usr/bin/env python

import os
import urllib
import re
import math

from google.appengine.api import users
from google.appengine.ext import ndb

import webapp2
import jinja2

JINJA_ENVIRONMENT = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
  extensions=["jinja2.ext.autoescape"],
  autoescape=True)

def shorten(text):
  return find_links(text[:497] + "...")

def find_links(text):
  links = re.findall(r"(https?://\S+)", text)
  for link in links[:]:
    if link[-4:] == ".jpg" or link[-4:] == ".gif" or link[-4:] == ".png":
      text = text.replace(link, "<br/><a href='" + link + "' target='_blank'><img src='" + link + "'/></a><br/>")
    else:
      text = text.replace(link, "<a href='" + link + "' target='_blank'>" + link + "</a>")
  return text

class MainHandler(webapp2.RequestHandler):

  def get(self):
    page_size = 10
    if users.get_current_user():
      login_url = users.create_logout_url(self.request.uri)
      login_message = "Logout"
      user_name = users.get_current_user().nickname()
      user_id = users.get_current_user().user_id()
    else:
      login_url = users.create_login_url(self.request.uri)
      login_message = "Login"
      user_name = ""
      user_id = None
    
    blogs_page_number = self.request.get("bpage")        
    if not blogs_page_number:
      blogs_page_number = 1
    else:
      blogs_page_number = int(blogs_page_number)

    blogs_query = Blog.query().filter(Blog.author == user_id).order(-Blog.date)
    blogs = blogs_query.fetch(page_size, offset=((blogs_page_number - 1) * page_size))
    
    all_blogs_page_number = self.request.get("opage")
    if not all_blogs_page_number:
      all_blogs_page_number = 1
    else:
      all_blogs_page_number = int(all_blogs_page_number)

    all_blogs_query = Blog.query().order(-Blog.date)
    all_blogs_count_query = Blog.query().order(-Blog.date)
    all_blogs = all_blogs_query.fetch(page_size, offset=((all_blogs_page_number - 1) * page_size))

    blogs_count = blogs_query.count()
    all_blogs_count = all_blogs_count_query.count()

    if blogs_page_number * page_size < blogs_count:
      blogs_more_articles = True
    else:
      blogs_more_articles = False

    if all_blogs_page_number * page_size < all_blogs_count:
      all_blogs_more_articles = True
    else:
      all_blogs_more_articles = False

    tags = {}

    for blog in all_blogs:
      query = Article.query(ancestor=article_key(blog.name))
      articles = query.fetch()
      for article in articles:
        for tag in article.tags:
          if tag in tags:
            tags[tag] = tags[tag] + 1
          elif tag is not None and tag and tag not in tags:
            tags[tag] = 1

    values = {
      "blogs": blogs,
      "all_blogs": all_blogs,
      "tags": tags,
      "login_url": login_url,
      "login_message": login_message,
      "user_name": user_name,
      "blogs_more_blogs": blogs_more_articles,
      "blogs_page_number": blogs_page_number,
      "all_blogs_page_number": all_blogs_page_number,
      "all_blogs_more_blogs": all_blogs_more_articles
    }

    template = JINJA_ENVIRONMENT.get_template("templates/index.html")
    self.response.write(template.render(values))

class BlogHandler(webapp2.RequestHandler):

  def get(self,blog_name):
    page_size = 10
    if users.get_current_user() and blog_name != "":
      login_url = users.create_logout_url(self.request.uri)
      login_message = "Logout"
      user_name = users.get_current_user().nickname()
      user_id = users.get_current_user().user_id()
      blog_query = Blog.query(ancestor=blog_key(user_id)).filter(Blog.name == blog_name)
      blog = blog_query.get()
    else:
     login_url = users.create_login_url(self.request.uri)
     login_message = "Login"
     user_name = ""
     user_id = None
     blog = None

    page_number = self.request.get("page")
    if not page_number:
      page_number = 1
    else:
      page_number = int(page_number)

    if not blog:
      blog_query = Blog.query().filter(Blog.name == blog_name)
      blog = blog_query.get()      

    query = Article.query(ancestor=article_key(blog_name)).order(-Article.date)
    articles = query.fetch(page_size, offset=((page_number - 1) * page_size))
    count = query.count()

    if page_number * page_size < count:
      more_articles = True
    else:
      more_articles = False


    for article in articles[:]:
      if len(article.content) > 500:
        article.abbreviated_content = shorten(article.content)
      else:
        article.abbreviated_content = find_links(article.content)

    values = {
      "blog": blog,
      "articles": articles,
      "login_url": login_url,
      "login_message": login_message,
      "user_name": user_name,
      "user_id": user_id,
      "blog_name": blog_name,
      "page_number": page_number,
      "more_articles": more_articles
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
  tags = ndb.StringProperty(repeated=True)
  date = ndb.DateTimeProperty(auto_now=True)
  creation_date = ndb.DateTimeProperty(auto_now_add=True)

class AddArticleHandler(webapp2.RequestHandler):

  def post(self):
    blog_name = self.request.get("blog_name")

    article_query = Article.query().filter(Article.title == self.request.get("title"))
    article = article_query.get()

    if users.get_current_user() and blog_name != "" and self.request.get("title") != "" and article is None:
      article = Article(parent=article_key(blog_name))
      article.author = users.get_current_user().user_id()
      article.author_name = users.get_current_user().nickname()
      article.blog_name = blog_name
    else:
      self.redirect("/")
      return

    article.title = self.request.get("title")
    article.content = self.request.get("content")
    article.tags = self.request.get("tags").split(",")
    for i in range(0, len(article.tags)):
      article.tags[i] = article.tags[i].lower().strip()

    if article.title == "" or article.content == "":
      self.redirect("/blog/" + blog_name)
      return

    article.put()

    self.redirect("/blog/" + blog_name + "/article/" + article.title)

class EditArticleHandler(webapp2.RequestHandler):

  def get(self, blog_name, article_int_id):
    if users.get_current_user() and blog_name != "":
      login_url = users.create_logout_url(self.request.uri)
      login_message = "Logout"
      user_id = users.get_current_user().user_id()
      user_name = users.get_current_user().nickname()
      blog_query = Blog.query(ancestor=blog_key(user_id)).filter(Blog.name == blog_name)
      blog = blog_query.get()
    else:
      login_url = users.create_login_url(self.request.uri)
      login_message = "Login"
      user_name = ""
      user_id = None

    article = Article.get_by_id(int(article_int_id), parent=article_key(blog_name))

    if article.author != user_id:
      self.redirect("/blog/" + blog_name + "/article/" + article.title)
      return

    if not blog:
      blog_query = Blog.query().filter(Blog.name == blog_name)
      blog = blog_query.get()  

    values = {
      "login_url": login_url,
      "login_message": login_message,
      "user_name": user_name,
      "user_name": user_name,
      "user_id": user_id,
      "blog": blog,
      "article": article
    }

    template = JINJA_ENVIRONMENT.get_template("templates/edit-article.html")
    self.response.write(template.render(values)) 

  def post(self, blog_name, article_int_id):
    blog_name = self.request.get("blog_name")
    article_id = self.request.get("article-id")

    if users.get_current_user() and blog_name != "":
      article = Article.get_by_id(int(article_int_id), parent=article_key(blog_name))
      article.author = users.get_current_user().user_id()
      article.author_name = users.get_current_user().nickname()
      article.blog_name = blog_name
    else:
      self.redirect("/shitbag")
      return

    article.title = self.request.get("title")
    article.content = self.request.get("content")
    article.tags = self.request.get("tags").split(",")
    for i in range(0, len(article.tags)):
      article.tags[i] = article.tags[i].lower().strip()

    if article.title == "" or article.content == "":
      self.redirect("/blog/" + blog_name)
      return

    article.put()

    self.redirect("/blog/" + blog_name + "/article/" + article.title)

class ArticleHandler(webapp2.RequestHandler):

  def get(self, blog_name, article_name):
    if users.get_current_user() and blog_name != "":
      login_url = users.create_logout_url(self.request.uri)
      login_message = "Logout"
      user_id = users.get_current_user().user_id()
      user_name = users.get_current_user().nickname()
      blog_query = Blog.query(ancestor=blog_key(user_id)).filter(Blog.name == blog_name)
      blog = blog_query.get()
    else:
      login_url = users.create_login_url(self.request.uri)
      login_message = "Login"
      user_name = ""
      user_id = None
      blog = None

    article_query = Article.query(ancestor=article_key(blog_name)).filter(Article.title == article_name)
    article = article_query.get()

    if not blog:
      blog_query = Blog.query().filter(Blog.name == blog_name)
      blog = blog_query.get()  

    article.content = find_links(article.content)

    values = {
      "login_url": login_url,
      "login_message": login_message,
      "user_name": user_name,
      "user_name": user_name,
      "user_id": user_id,
      "blog": blog,
      "article": article
    }

    template = JINJA_ENVIRONMENT.get_template("templates/article.html")
    self.response.write(template.render(values)) 
    
class TagHandler(webapp2.RequestHandler):

  def get(self, tag_name):
    page_size = 10
    if users.get_current_user() and tag_name != "":
      login_url = users.create_logout_url(self.request.uri)
      login_message = "Logout"
      user_name = users.get_current_user().nickname()
      user_id = users.get_current_user().user_id()
    else:
      login_url = users.create_login_url(self.request.uri)
      login_message = "Login"
      user_name = ""
      user_id = None

    page_number = self.request.get("page")
    if not page_number:
      page_number = 1
    else:
      page_number = int(page_number)

    query = Article.query().order(-Article.date).filter(Article.tags == tag_name)
    articles = query.fetch(page_size, offset=((page_number - 1) * page_size))
    count = query.count()

    if page_number * page_size < count:
      more_articles = True
    else:
      more_articles = False


    for article in articles[:]:
      if len(article.content) > 500:
        article.abbreviated_content = shorten(article.content)
      else:
        article.abbreviated_content = find_links(article.content)

    values = {
      "articles": articles,
      "login_url": login_url,
      "login_message": login_message,
      "user_name": user_name,
      "user_id": user_id,
      "tag_name": tag_name,
      "page_number": page_number,
      "more_articles": more_articles
    }

    template = JINJA_ENVIRONMENT.get_template("templates/tag.html")
    self.response.write(template.render(values))     

def image_key(author):
  return ndb.Key("Author", author)

class Image(ndb.Model):

  author = ndb.StringProperty()
  author_name = ndb.StringProperty()
  image = ndb.BlobProperty()
  filename = ndb.StringProperty()
  date = ndb.DateTimeProperty(auto_now_add=True)

class ImageHandler(webapp2.RequestHandler):

  def get(self, filename):
    if users.get_current_user():
      login_url = users.create_logout_url(self.request.uri)
      login_message = "Logout"
      user_name = users.get_current_user().nickname()
      user_id = users.get_current_user().user_id()
    else:
      login_url = users.create_login_url(self.request.uri)
      login_message = "Login"
      user_name = ""
      user_id = None

    query = Image.query().order(-Image.date).filter(Image.author == user_id and Image.filename == filename)
    images = query.fetch()

    for image in images:
      self.response.headers["Content-Type"] = "image/jpg"
      self.response.out.write(image.image)

  def post(self, image_name):
    #image_name really doesn't have a meaning here
    if users.get_current_user():
      user_name = users.get_current_user().nickname()
      user_id = users.get_current_user().user_id()
      image = Image(parent=image_key(user_id))
      image.author = users.get_current_user().user_id()
      image.author_name = users.get_current_user().nickname()
    else:
      self.redirect("/")
      return

    filename = self.request.params["image"].filename
    count = 0

    extension = filename[-4:]
    name = filename[:-4]
    while True:
      query = Image.query().order(-Image.date).filter(Image.filename == filename)
      images = query.get()

      if images:
        count = count + 1
        name =  name + "%d" % count
        filename = name + extension
      else:
        break

    image.filename = filename
    image.image = self.request.get("image")
    image.put()

    self.redirect("/image/"+image.filename)

class ImagePageHandler(webapp2.RequestHandler):

  def get(self):
    page_size = 10
    if users.get_current_user():
      login_url = users.create_logout_url(self.request.uri)
      login_message = "Logout"
      user_name = users.get_current_user().nickname()
      user_id = users.get_current_user().user_id()
    else:
      self.redirect("/")
      return

    page_number = self.request.get("page")
    if not page_number:
      page_number = 1
    else:
      page_number = int(page_number)

    query = Image.query().order(-Image.date).filter(Article.author == user_id)
    images = query.fetch(page_size, offset=((page_number - 1) * page_size))
    count = query.count()

    if page_number * page_size < count:
      more_images = True
    else:
      more_images = False

    paths = os.path.split(self.request.url)
    page_url = paths[0]

    values = {
      "images": images,
      "page_url": page_url,
      "login_url": login_url,
      "login_message": login_message,
      "user_name": user_name,
      "user_id": user_id,
      "page_number": page_number,
      "more_images": more_images
    }

    template = JINJA_ENVIRONMENT.get_template("templates/image.html")
    self.response.write(template.render(values))

class RSSHandler(webapp2.RequestHandler):

  def get(self, blog_name):
    self.response.headers['Content-Type'] = "text/xml; charset=utf-8"
    if users.get_current_user() and blog_name != "":
      login_url = users.create_logout_url(self.request.uri)
      login_message = "Logout"
      user_name = users.get_current_user().nickname()
      user_id = users.get_current_user().user_id()
      blog_query = Blog.query(ancestor=blog_key(user_id)).filter(Blog.name == blog_name)
      blog = blog_query.get()
    else:
      user_name = ""
      user_id = None
      blog = None

    link = os.path.split(self.request.url)[0][:-3]

    if not blog:
      blog_query = Blog.query().filter(Blog.name == blog_name)
      blog = blog_query.get()      

    query = Article.query(ancestor=article_key(blog_name)).order(-Article.date)
    articles = query.fetch()

    values = {
      "blog": blog,
      "articles": articles,
      "user_name": user_name,
      "link": link
    }

    template = JINJA_ENVIRONMENT.get_template("templates/blog.rss")
    self.response.write(template.render(values))  

app = webapp2.WSGIApplication([
  ("/addblog", AddBlogHandler),
  ("/blog/.*/addarticle", AddArticleHandler),
  ("/blog/(.*)/article/(.*)/edit", EditArticleHandler),
  ("/blog/(.*)/article/(.*)", ArticleHandler),
  ("/image", ImagePageHandler),
  ("/image/(.*)", ImageHandler),
  ("/blog/(.*)", BlogHandler),
  ("/tag/(.*)", TagHandler),
  ("/rss/(.*)", RSSHandler),
  ("/.*", MainHandler)
], debug=True)
