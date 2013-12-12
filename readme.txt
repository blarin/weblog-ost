Author: Ian Guerin
N#: N19555302
Project: WebLog-OST
URL: http://weblog-ost.appspot.com/

DOCUMENTATION:

  MISSING FEATURE:
  Links in an article's content are not longer replaced with clickable hyperlinks, and images are no longer displayed inline. The post is displayed as completely plain text. This has the added security bonus of dissallowing a user from injecting html into their posts.

  TESTING:
  Upon accessing this blogging platform you will be taken to the Main Page.

  From here, you can view all the blogs you have written (provided you are logged in)
  and all of the blogs that have been written by other users.
  On this page you may also view tags that have been used by other users in a "Tag Cloud".

  By logging in, you have the ability to create a blog, upload images, and write articles.
  Typing in a unique blog name and hitting "Create!" brings you to the blog, and you may then write an article. Adding urls that end ind .png .gif or .jpg allows the user to embed images
  into their articles (these images can be uploaded at /image).

  Older articles are available in /blog/name-of-blog by clicking the link "view older", you may then return by clicking "view newer".

  A user may also access a blog's rss feed by clicking the *rss icon* that is next to the author's nickname, beneath the name of the blog.

  DEVELOPING:
  This project is designed to follow as natural a flow as possible. The user accesses blogs, articles, images and tags pages. Images are their own entity that may be attached to many different articles. Articles belong to blogs, and blogs belong to users. Tags are an element of articles, but not kept in their own entity in a datastore. Tags can, however be viewed in their own page, which shows all articles mentioning that tag.

  This project has been written in Python for Google's App Engine. It is deployed at http://weblog-ost.appspot.com/. The file main.py handles all http get and post requests using a naming convention that is very straightforward (though perhaps verbose) and easy to gain insight as to the outcome of the handlers.

  Handlers that correspond to actual user views also correspond to a template that can be found in /templates. These use the jinja2 templating language.

  The styling for the site is written in CSS and is available at /stylesheets/main.css. All template files use the same style sheet. For that matter, all template files have the same header and footer, which can be found at /templates/header.html and /templates/footer.html, respectively.


  EXTRA CREDIT:
  I added the ability to follow specific blogs, as well as unfollow them (when bloggers get too annoying!). The user may then access their article feed at the url /feed. I think this is an important feature in creating an online blogging network