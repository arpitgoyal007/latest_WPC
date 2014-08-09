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
from google.appengine.api import images
from google.appengine.ext import db

import utils

template_dir = os.path.join(os.path.dirname(__file__), "new_templates")
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
			self.render('index_user.html', me=self.user)

class BlogPermpageHandler(PageHandler):
	def get(self, resource):
		blogKey = get_key_urlunsafe(resource)
		if blogKey:
			userKey = blogKey.parent()
			user = userKey.get()
			templateVals = {'me': self.user}
			if self.user:
				if self.user == user:
					templateVals['user'] = self.user
				else:
					templateVals['user'] = user
			else:
				templateVals['user'] = user
			templateVals['blog'] = blogKey.get()
			self.render('blogperm.html', **templateVals)
		else:
			self.redirect('/')

	def post(self, resource):
		blogKey = get_key_urlunsafe(resource)
		if blogKey:
			action = self.request.get('actionType')
			if action == "delete":
				delete_blog(blogKey, self.user.key)
				self.redirect('/%s/blogs' % self.user.key.id())
			elif action == "edit":
				self.redirect('/editblog/%s' % resource)

class BlogNewHandler(PageHandler):
	def get(self):
		if self.user:
			templateVals = {'me': self.user}
			self.render('new_blog.html', **templateVals)
		else:
			self.redirect('/')

	def post(self):
		if self.user:
			title = self.request.get('title')
			content = self.request.get('content')
			if title and content:
				create_blog(title, content, self.user.key)
				self.redirect('/%s/blogs' % self.user.key.id())
			else:
				errorMsg = "Please enter both title and content!"
				templateVals = {'me': self.user, 'title': title, 'content': content, 'submitError': errorMsg}
				self.render('new_blog.html', **templateVals)
		else:
			self.redirect('/')

class BlogEditHandler(PageHandler):
	def get(self, resource):
		if self.user:
			templateVals = {'me': self.user}
			blogKey = get_key_urlunsafe(resource)
			if blogKey:
				if self.user.key == blogKey.parent():
					blog = blogKey.get()
					if blog:
						templateVals['title'] = blog.title
						templateVals['content'] = blog.content
						self.render('edit_blog.html', **templateVals)
					else:
						self.redirect('/')
				else:
					self.redirect('/')
			else:
				self.redirect('/')
		else:
			self.redirect('/')

	def post(self, resource):
		if self.user:
			blogKey = get_key_urlunsafe(resource)
			if blogKey:
				if self.user.key == blogKey.parent():
					blog = blogKey.get()
					if blog:
						title = self.request.get('title')
						content = self.request.get('content')
						if title and content:
							blog.title = title
							blog.content = content
							blog.put()
							self.redirect('/%s/blogs' % self.user.key.id())
						else:
							errorMsg = "Please enter both title and content!"
							templateVals = {'me': self.user, 'title': title, 'content': content, 'submitError': errorMsg}
							self.render('edit_blog.html', **templateVals)
					else:
						self.redirect('/')
				else:
					self.redirect('/')
			else:
				self.redirect('/')
		else:
			self.redirect('/')

class PhotoPermpageHandler(PageHandler):
	def get(self, resource):
		photoKey = get_key_urlunsafe(resource)
		if photoKey:
			userKey = photoKey.parent()
			user = userKey.get()
			templateVals = {'me': self.user}
			if self.user:
				if self.user == user:
					templateVals['user'] = self.user
				else:
					templateVals['user'] = user
			else:
				templateVals['user'] = user
			photos = Picture.of_ancestor(user.key)
			templateVals['photos'] = photos	
			templateVals['photo'] = photoKey.get()
			self.render('photoperm.html', **templateVals)
		else:
			self.redirect('/')

	def post(self, resource):
		photoKey = get_key_urlunsafe(resource)
		if photoKey:
			action = self.request.get('actionType')
			if action == "delete":
				delete_photo(photoKey, self.user.key)
				self.redirect('/%s/photos' % self.user.key.id())
			elif action == "edit":
				self.redirect('/editphoto/%s' % resource)

class PhotoNewHandler(PageHandler):
	def get(self):
		if self.user:
			templateVals = {'me': self.user}
			uploadUrl = blobstore.create_upload_url('/uploadphoto')
			templateVals['uploadUrl'] = uploadUrl
			self.render('upload_photo.html', **templateVals)
		else:
			self.redirect('/')

class PhotoEditHandler(PageHandler):
	def get(self):
		if self.user:
			templateVals = {'me': self.user}
			resource = self.request.get('ids')
			logging.info(resource)
			photoList = get_photolist_from_urlstring(resource, self.user.key)
			templateVals['photos'] = photoList
			self.render('edit_photo.html', **templateVals)
		else:
			self.redirect('/')

	def post(self):
		if self.user:
			resource = self.request.get('ids')
			photoList = get_photolist_from_urlstring(resource, self.user.key)
			captionList = self.request.get_all('caption')
			descriptionList = self.request.get_all('description')
			for i in range(len(photoList)):
				photo = photoList[i]
				caption = captionList[i]
				description = descriptionList[i]
				photo.caption = caption
				photo.description = description
				photo.put()
				self.redirect('/%s/photos' % self.user.key.id())
		else:
			self.redirect('/')

class UserSettingsHandler(blobstore_handlers.BlobstoreUploadHandler, PageHandler):
	def get(self):
		if self.user:
			templateVals = {'me': self.user}
			self.render('usersettings.html', **templateVals)
		else:
			self.redirect('/')

	def post(self):
		name = self.request.get('name')
		alt_email = self.request.get('alt_email')
		password = self.request.get('password')
		verifyPassword = self.request.get('verifyPassword')
		country = self.request.get('country')
		facebook = self.request.get('facebook')
		youtube = self.request.get('youtube')
		google_plus = self.request.get('google_plus')
		twitter = self.request.get('twitter')
		pinterest = self.request.get('pinterest')
		website = self.request.get('website')
		
		update_user_name (name)
		update_user_alt_email (alt_email)
		update_user_country(country)
		update_social_profiles(facebook, youtube, google_plus, twitter, pinterest, website)
		self.redirect('usersettings.html')

class PhotoUploadHandler(blobstore_handlers.BlobstoreUploadHandler, PageHandler):
	def post(self):
		if self.user:
			uploads = self.get_uploads('files')
			photoList = []
			if len(uploads)>0:
				for upload in uploads:
					blobInfo = upload
					photo = create_picture(blobInfo.key(), self.user.key)
					photoList.append(photo)
				resource = get_edit_photo_urlstring(photoList)
				if len(photoList) != 0:
					uploaddone = 1;
				#self.redirect('/editphoto?ids=%s' % resource)
				self.redirect('/%s/photos' % self.user.key.id())
			else:
				uploadUrl = blobstore.create_upload_url('/uploadphoto')
				errorMsg = "Please choose a photo!"
				templateVals = {'me': self.user, 'uploadUrl': uploadUrl, 'submitError': errorMsg}
				self.render('upload_photo.html', **templateVals)
		else:
			self.redirect('/')

class PhotoServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
	def get(self, resource):
		resource = str(urllib.unquote(resource))
		blobInfo = blobstore.BlobInfo.get(resource)
		self.send_blob(blobInfo)

class UserStudioHandler(PageHandler):
	def get(self, resource):
		#userid = str(urllib.unquote(resource))
		userid = resource
		user = User.get_by_id(userid)
		templateVals = {'me': self.user}
		if user:
			if self.user:
				if self.user == user:
					templateVals['user'] = self.user
				else:
					templateVals['user'] = user
			else:
				templateVals['user'] = user
			photos = Picture.of_ancestor(user.key)
			templateVals['photos'] = photos	
			self.render('user_studio.html', **templateVals)
		else:
			self.redirect('/')
			

class UserBlogsHandler(PageHandler):
	def get(self, resource):
		userid = resource
		user = User.get_by_id(userid)
		templateVals = {'me': self.user}
		if user:
			if self.user:
				if self.user == user:
					templateVals['user'] = self.user
				else:
					templateVals['user'] = user
			else:
				templateVals['user'] = user
			blogs = Blog.of_ancestor(user.key)
			templateVals['blogs'] = blogs
			self.render('user_blogs.html', **templateVals)
		else:
			self.redirect('/')

class UserPhotosHandler(PageHandler):
	def get(self, resource):
		userid = resource
		user = User.get_by_id(userid)
		templateVals = {'me': self.user}
		if user:
			if self.user:
				if self.user == user:
					templateVals['user'] = self.user
				else:
					templateVals['user'] = user
			else:
				templateVals['user'] = user
			photos = Picture.of_ancestor(user.key)
			templateVals['photos'] = photos
			self.render('user_photos.html', **templateVals)
		else:
			self.redirect('/')
			
	def post(self, resource):
		photoKey = get_key_urlunsafe(resource)
		if photoKey:
			action = self.request.get('actionType')
			if action == "delete":
				delete_photo(photoKey, self.user.key)
				self.redirect('/%s/photos' % self.user.key.id())
			elif action == "edit":
				self.redirect('/editphoto/%s' % resource)

class SigninHandler(PageHandler):
	def get(self):
		if self.user:
			self.redirect('/')
		else:
			self.render("signin.html")

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
				if not prevUser:
					user = create_user(email, name, password)
					self.login(user)
					self.redirect("/")
				else:
					templateVals['signupError'] = "Account already exists for this Email ID!"
			else:
				templateVals['signupError'] = "Enter all fields!"
			self.render('signin.html', **templateVals)
	#	except:
	#		self.page_error()

class LoginHandler(PageHandler):
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
				else:
					templateVals['signinError'] = "Account doesn't exist for this Email ID!"
			else:
				templateVals['signinError'] = "Enter both Email ID and Password!"
			self.render('signin.html', **templateVals)
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
			('/signin', SigninHandler),
			('/signup', SignupHandler),
			('/login', LoginHandler),
			('/logout', LogoutHandler),
			('/blog/([^/]+)', BlogPermpageHandler),
			('/photo/([^/]+)', PhotoPermpageHandler),
			('/editblog/([^/]+)', BlogEditHandler),
			('/newblog', BlogNewHandler),
			('/editphoto', PhotoEditHandler),
			('/newphoto', PhotoNewHandler),
			('/uploadphoto', PhotoUploadHandler),
			('/usersettings', UserSettingsHandler),
			('/servephoto/([^/]+)', PhotoServeHandler),
			('/([^/]+)/blogs', UserBlogsHandler),
			('/([^/]+)/photos', UserPhotosHandler),
			('/([^/]+)', UserStudioHandler),
			('/([^.]+)', DefaultHandler),
			('/', MainHandler)
			], debug=True)