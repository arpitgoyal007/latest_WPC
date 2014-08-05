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
import re
import urllib
import webapp2
import jinja2
import logging

from datamodel import *
from datahandle import *
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

import utils

template_dir = os.path.join(os.path.dirname(__file__), "Templates_dir")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

class PageHandler(webapp2.RequestHandler):
	def get(self):
		self.redirect('/default')

	def post(self):
		self.redirect('/default')

	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

	def page_error(self):
		self.redirect("/")

	def set_secure_cookie(self, name, val):
		secureVal = utils.secure_cookie_val(name, val)
		self.response.headers.add_header('Set-Cookie', "%s=%s" % (name, str(secureVal)))

	def read_secure_cookie(self, name):
		secureVal = self.request.cookies.get(name)
		if secureVal and utils.check_secure_cookie_val(name, secureVal):
			return secureVal.split('|')[0]

	def del_cookie(self, name):
		self.response.headers.add_header('Set-Cookie', "%s=" % name)

	def login(self, user):
		self.set_secure_cookie('userinfo', "id=%s" % user.key.id())

	def logout(self):
		self.del_cookie('userinfo')

	def initialize(self, *a, **kw):
		webapp2.RequestHandler.initialize(self, *a, **kw)
		self.user = self.user_cookie_authenticate()

	def user_cookie_authenticate(self):
		userinfo = utils.format_cookie(self.read_secure_cookie('userinfo'))
		userid = userinfo.get('id')
		if userid:
			return User.get_by_id(userid)

class MainHandler(PageHandler):
	def get(self):
		if not self.user:
			self.render('index.html')
		else:
			self.render('home.html', me=self.user)

class BlogPermpageHandler(PageHandler):
	def get(self, resource):
		if self.user:
			pass
		else:
			pass

class EditBlogHandler(PageHandler):
	def get(self, resource):
		if self.user:
			pass
		else:
			pass

class PhotoPermpageHandler(PageHandler):
	def get(self, resource):
		if self.user:
			pass
		else:
			pass

class UserHomeHandler(PageHandler):
	def get(self, resource):
		if self.user:
			pass
		else:
			pass

class UserBlogsHandler(PageHandler):
	def get(self, resource):
		if self.user:
			pass
		else:
			pass

class UserPhotosHandler(PageHandler):
	def get(self, resource):
		if self.user:
			pass
		else:
			pass

class SigninHandler(PageHandler):
	def post(self):
	#	try:
			email = self.request.get('email')
			password = self.request.get('password')
			templateVals = {'signinEmail': email}
			if email and password:
				user = User.get_by_id(email)
				if user:
					if utils.valid_password(email, password, user.passwordHash):
						self.login(user)
						self.redirect("/")
					else:
						templateVals['signinError'] = "Invalid password!"
						self.render('index.html', **templateVals)
				else:
					templateVals['signinError'] = "Account doesn't exist for this Email ID!"
					self.render('index.html', **templateVals)
			else:
				templateVals['signinError'] = "Enter both Email ID and Password!"
				self.render('index.html', **templateVals)
	#	except:
	#		self.page_error()

class SignupHandler(PageHandler):
	def post(self):
	#	try:
			name = self.request.get('name')
			email = self.request.get('email')
			password = self.request.get('password')
			verifyPassword = self.request.get('verifyPassword')
			templateVals = {'name': name, 'signupEmail': email}
			if name and email and password and (verifyPassword == password):
				prevUser = User.get_by_id(email)
				if prevUser:
					templateVals['signupError'] = "Account already exists for this Email ID!"
					self.render('index.html', **templateVals)
				else:
					user = create_user(email, name, password)
					self.login(user)
					self.redirect("/")
			else:
				templateVals['signupError'] = "Enter all fields!"
				self.render('index.html', **templateVals)
	#	except:
	#		self.page_error()

class MyStudioHandler(PageHandler):
	def get(self):
	#	try:
			templateVals = {'me': self.user}
			self.render('myStudio.html', **templateVals)
			#self.render('myStudio.html', username=self.user.username)
	#	except:
	#		self.page_error()

class MyBlogHandler(PageHandler):
	def get(self):
	#	try:
			blogs = Blog.query_book(self.user.key).fetch()
			templateVals = {'me': self.user, 'blogs': blogs}
			self.render('myBlog.html', **templateVals)
	#	except:
	#		self.page_error()

	def post(self):
	#	try:
			title = self.request.get('title')
			content = self.request.get('content')
			if title and content:
				create_blog(title, content, self.user.key)
				self.redirect("/myBlog")
			else:
				blogs = Blog.query_book(self.user.key).fetch()
				errorMsg = "Enter both title and content!"
				templateVals = {'me': self.user, 'title': title, 'content': content, 'submitError': errorMsg, 'blogs': blogs}
				self.render('myBlog.html', **templateVals)
	#	except:
	#		self.page_error()

class MyBlogPermalinkHandler(PageHandler):
	def get(self, resource):
	#	try:
			blog = Blog.get_by_id(int(resource), parent=self.user.key)
			self.render('myBlogPermalink.html', me=self.user, blog=blog)
	#	except:
	#		self.page_error()

	def post(self, resource):
		action = self.request.get('actionType')
		blog = Blog.get_by_id(int(resource), parent=self.user.key)
		if action == "delete":
			blog.key.delete()
			self.redirect('/myBlog')

class MyGalleryHandler(PageHandler):
	def get(self):
	#	try:
			pictures = Picture.query_book(self.user.key).fetch()
			upload_url = blobstore.create_upload_url('/uploadImage')
			self.render('myGallery.html', me=self.user, upload_url=upload_url, pictures=pictures)
	#	except:
	#		self.page_error()

class MyImagePermalinkHandler(PageHandler):
	def get(self, resource):
	#	try:
			pic = Picture.get_by_id(int(resource), parent=self.user.key)
			self.render('myImagePermalink.html', me=self.user, pic=pic)
	#	except:
	#		self.page_error()

	def post(self, resource):
		action = self.request.get('actionType')
	#	key = self.request.get('postKey')
		pic = Picture.get_by_id(int(resource), parent=self.user.key)
		if action == "delete":
			blobKey = pic.blobKey
			blobInfo = blobstore.BlobInfo.get(blobKey)
			blobInfo.delete()
			pic.key.delete()
			self.redirect('/myGallery')

class ImageUploadHandler(blobstore_handlers.BlobstoreUploadHandler, PageHandler):
	def post(self):
	#	try:
			caption = self.request.get('caption')
			upload = self.get_uploads('image')
			if len(upload)>0:
				blobInfo = upload[0]
				create_picture(caption, blobInfo.key(), self.user.key)
			#	self.redirect('/serveImage/%s' % blobInfo.key())
				self.redirect('/myGallery')
			else:
				pictures = Picture.query_book(self.user.key).fetch()
				upload_url = blobstore.create_upload_url('/uploadImage')
				errorMsg = "Please upload a file!"
				self.render('myGallery.html', me=self.user, upload_url=upload_url, pictures=pictures, caption=caption, submitError=errorMsg)
	#	except:
	#		self.page_error()

class ImageServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
	def get(self, resource):
	#	try:
			resource = str(urllib.unquote(resource))
			blobInfo = blobstore.BlobInfo.get(resource)
			self.send_blob(blobInfo)
	#	except:
	#		self.page_error()

class UserPageHandler(PageHandler):
	def get(self, user_resource):
	#	try:
			self.redirect('/usr/%s/studio' % user_resource)
	#	except:
	#		self.page_error()

class UserStudioHandler(PageHandler):
	def get(self, user_resource):
	#	try:
			if self.user:
				user = User.get_by_id(user_resource)
				self.render('userStudio.html', username=user.username, userid=user_resource)
			else:
				user = User.get_by_id(user_resource)
				self.render('userStudio.html', username=user.username, userid=user_resource)
	#	except:
	#		self.page_error()

class UserBlogHandler(PageHandler):
	def get(self, user_resource):
	#	try:
			if self.user:
				user = User.get_by_id(user_resource)
				blogs = Blog.query_book(user.key).fetch()
				self.render('userBlog.html', username=user.username, userid=user_resource, blogs=blogs)
			else:
				user = User.get_by_id(user_resource)
				blogs = Blog.query_book(user.key).fetch()
				self.render('userBlog.html', username=user.username, userid=user_resource, blogs=blogs)
	#	except:
	#		self.page_error()

class UserBlogPermalinkHandler(PageHandler):
	def get(self, user_resource, post_resource):
	#	try:
			if self.user:
				user = User.get_by_id(user_resource)
				blog = Blog.get_by_id(int(post_resource), parent=user.key)
				self.render('userBlogPermalink.html', username=user.username, userid=user_resource, blog=blog)
			else:
				user = User.get_by_id(user_resource)
				blog = Blog.get_by_id(int(post_resource), parent=user.key)
				self.render('userBlogPermalink.html', username=user.username, userid=user_resource, blog=blog)
	#	except:
	#		self.page_error()

class UserGalleryHandler(PageHandler):
	def get(self, user_resource):
	#	try:
			if self.user:	
				user = User.get_by_id(user_resource)
				pictures = Picture.query_book(user.key).fetch()
				self.render('userGallery.html', username=user.username, userid=user_resource, pictures=pictures)
			else:
				user = User.get_by_id(user_resource)
				pictures = Picture.query_book(user.key).fetch()
				self.render('userGallery.html', username=user.username, userid=user_resource, pictures=pictures)
	#	except:
	#		self.page_error()

class UserImagePermalinkHandler(PageHandler):
	def get(self, user_resource, post_resource):
	#	try:
			if self.user:
				user = User.get_by_id(user_resource)
				pic = Picture.get_by_id(int(post_resource), parent=user.key)
				self.render('userImagePermalink.html', username=user.username, userid=user_resource, pic=pic)
			else:
				user = User.get_by_id(user_resource)
				pic = Picture.get_by_id(int(post_resource), parent=user.key)
				self.render('userImagePermalink.html', username=user.username, userid=user_resource, pic=pic)
	#	except:
	#		self.page_error()

class LogoutHandler(PageHandler):
	def get(self):
		self.logout()
		self.redirect('/')

class DefaultHandler(PageHandler):
	def get(self, resource):
		self.redirect('/')

app = webapp2.WSGIApplication([
			('/', MainHandler),
			('/myStudio', MyStudioHandler),
			('/myBlog', MyBlogHandler),
			('/myBlog/blg/([^/]+)', MyBlogPermalinkHandler),
			('/myGallery', MyGalleryHandler),
			('/myGallery/img/([^/]+)', MyImagePermalinkHandler),
			('/uploadImage', ImageUploadHandler),
			('/serveImage/([^/]+)', ImageServeHandler),
			('/usr/([^/]+)', UserPageHandler),
			('/usr/([^/]+)/studio', UserStudioHandler),
			('/usr/([^/]+)/blog', UserBlogHandler),
			('/usr/([^/]+)/blog/blg/([^/]+)', UserBlogPermalinkHandler),
			('/usr/([^/]+)/gallery', UserGalleryHandler),
			('/usr/([^/]+)/gallery/img/([^/]+)', UserImagePermalinkHandler),
			('/signin', SigninHandler),
			('/signup', SignupHandler),
			('/logout', LogoutHandler),
			('/([^.]+)', DefaultHandler)
			], debug=True)

app2 = webapp2.WSGIApplication([
			('/', MainHandler),
			('/signin', SigninHandler),
			('/signup', SignupHandler),
			('/logout', LogoutHandler),
			('/blog/([^/]+)', BlogPermpageHandler),
			('/photo/([^/]+)', PhotoPermpageHandler),
			('/editblog/([^/]+)', EditBlogHandler),
			('/([^/]+)', UserHomeHandler),
			('/([^/]+)/blogs', UserBlogsHandler),
			('/([^/]+)/photos', UserPhotosHandler),
			('/([^.]+)', DefaultHandler)
			], debug=True)