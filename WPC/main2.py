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
			
class UserGroupsHandler(PageHandler):
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
			groups = Group.of_ancestor(user.key)
			templateVals['groups'] = groups
			self.render('user_groups.html', **templateVals)
		else:
			self.redirect('/')

class BlogNewHandler(PageHandler, blobstore_handlers.BlobstoreUploadHandler):
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
			self.render('new_blog.html', **templateVals)
		else:
			self.redirect('/')

	def post(self, resource):
		if self.user:
			title = self.request.get('title')
			content = self.request.get('content')
			cover_img = self.request.get('cover_img')
			if title and content:
				blog = create_blog(title, content, cover_img, self.user.key)
				self.redirect('/blog/%s' % blog.key.urlsafe())
			else:
				errorMsg = "Please enter both title and content!"
				templateVals = {'me': self.user, 'title': title, 'content': content, 'submitError': errorMsg}
				self.render('new_blog.html', **templateVals)
		else:
			self.redirect('/')

class GroupNewHandler(PageHandler ,blobstore_handlers.BlobstoreUploadHandler):
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
			self.render('new_group.html', **templateVals)
		else:
			self.redirect('/')

	def post(self, resource):
		if self.user:
			action = self.request.get('actionType')
			if action == "create_group":			
				name = self.request.get('name')
				description = self.request.get('description')
				cover_img = self.request.get('cover_img')
				if name and description:
					group = create_group(name, description, cover_img, self.user.key)
					self.redirect('/group/%s' % group.key.urlsafe())
				else:
					errorMsg = "Please enter both title and content!"
					templateVals = {'me': self.user, 'name': name, 'description': description, 'submitError': errorMsg}
					self.render('new_group.html', **templateVals)
		else:
			self.redirect('/')

class BlogsHandler(PageHandler):
	def get(self):
		if not self.user:
			templateVals = {'me': ""}
			self.render('blogs.html', **templateVals)
		else:
			templateVals = {'me': self.user}
			blogs = Blog.of_ancestor(self.user.key)
			templateVals['blogs'] = blogs	
			self.render('blogs.html', **templateVals)

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
				self.render('blogs.html', **templateVals)
		else:
			self.redirect('/')


class SearchResultsHandler(PageHandler):
	def get(self):
		if self.user:
			templateVals = {'me': self.user}
			self.render('search_results.html', **templateVals)
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
				self.render('search_results.html', **templateVals)
		else:
			self.redirect('/')

class GroupsHandler(PageHandler):
	def get(self):
		if not self.user:
			templateVals = {'me': ""}
			self.render('groups.html', **templateVals)
		else:
			templateVals = {'me': self.user}
			self.render('groups.html', **templateVals)

class PhotosHandler(PageHandler):
	def get(self):
		if not self.user:
			templateVals = {'me': ""}
			self.render('photos.html', **templateVals)
		else:
			templateVals = {'me': self.user}
			self.render('photos.html', **templateVals)

class ForumHandler(PageHandler):
	def get(self):
		if not self.user:
			templateVals = {'me': ""}
			self.render('forum.html', **templateVals)
		else:
			templateVals = {'me': self.user}
			self.render('forum.html', **templateVals)

	def post(self):
		if self.user:
			title = self.request.get('title')
			content = self.request.get('content')
			if title and content:
				create_blog(title, content, self.user.key)
				self.redirect('/%s/forum' % self.user.key.id())
			else:
				errorMsg = "Please enter both title and content!"
				templateVals = {'me': self.user, 'title': title, 'content': content, 'submitError': errorMsg}
				self.render('forum.html', **templateVals)
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
					photo = photoKey.get()
					photo.viewed += 1
					photo.put()
					templateVals['user'] = user
			else:
				photo = photoKey.get()
				photo.viewed += 1
				photo.put()
				templateVals['user'] = user
			photos = Picture.of_ancestor(user.key)
			templateVals['photos'] = photos	
			templateVals['photo'] = photoKey.get()
			self.render('photoperm.html', **templateVals)
		else:
			self.redirect('/')

	def post(self, resource):
		photoKey = get_key_urlunsafe(resource)
		photo = photoKey.get()
		userKey = photoKey.parent()
		user = userKey.get()
		if user:
			if self.user:
				if self.user == user:
					action = self.request.get('actionType')
					photoKey = get_key_urlunsafe(self.request.get('photoKey'))
					if action == "delete":
						delete_photo(photoKey, self.user.key)
						self.redirect('/%s/photos' % self.user.key.id())
					elif action == "edit":
						self.redirect('/editphoto/%s' % photoKey.urlsafe())
					elif action == "like":	
						photo.likes += 1
						photo.put()
						self.redirect('/%s/photos' % self.user.key.id())
					elif action == "add_comment":
						comment = []
						comment.append(self.request.get('comment'))
						photo.comments = comment
						photo.put()
						self.redirect('/%s/photos' % self.user.key.id())
					elif action == "add_tag_album":
						tagList = self.request.get_all('tags')
						albumList = self.request.get_all('albums')
						#photo.tags.append(tagList)
						#photo.albums.append(albumList)
						photo.tags = tagList
						photo.albums = albumList
						photo.put()
						self.redirect('/%s/photos' % self.user.key.id())
				else:
					self.redirect('/')
			else:
				self.redirect('/')
		else:
			self.redirect('/')

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
					blog = blogKey.get()
					blog.viewed += 1
					blog.put()
					templateVals['user'] = user
			else:
				blog = blogKey.get()
				blog.viewed += 1
				blog.put()
				templateVals['user'] = user
			templateVals['blog'] = blogKey.get()
			self.render('blogperm.html', **templateVals)
		else:
			self.redirect('/')

	def post(self, resource):
		blogKey = get_key_urlunsafe(resource)
		blog = blogKey.get()
		templateVals ={'blog': blog, 'me':self.user}
		
		if blogKey:
			action = self.request.get('actionType')
			if action == "delete":
				delete_blog(blogKey, self.user.key)
				self.redirect('/%s/blogs' % self.user.key.id())
			elif action == "edit":
				self.redirect('/editblog/%s' % resource)
			elif action == "like":	
				blog.likes += 1
				blog.put()
				self.render('blogperm.html', **templateVals)

class GroupPermpageHandler(PageHandler):
	def get(self, resource):
		groupKey = get_key_urlunsafe(resource)
		if groupKey:
			userKey = groupKey.parent()
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
			templateVals['group'] = groupKey.get()
			self.render('groupperm.html', **templateVals)
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
				self.redirect('/editgroup/%s' % resource)

class PhotoNewHandler(PageHandler):
	def get(self):
		if self.user:
			templateVals = {'me': self.user}
			uploadUrl = blobstore.create_upload_url('/uploadphoto')
			templateVals['uploadUrl'] = uploadUrl
			self.render('upload_photo.html', **templateVals)
		else:
			self.redirect('/')

class PopUpPhotoNewHandler(PageHandler):
	def get(self):
		if self.user:
			uploadUrl = blobstore.create_upload_url('/popupuploadphoto')
			templateVals = {'me': self.user, 'uploadUrl': uploadUrl, 'upload_done': 0}
			self.render('upload_popup_photo.html', **templateVals)
		else:
			self.redirect('/')

class PopUpPhotoUploadHandler(blobstore_handlers.BlobstoreUploadHandler, PageHandler):
	def post(self):
		if self.user:
			uploads = self.get_uploads('files')
			captionList = self.request.get_all('caption')
			descriptionList = self.request.get_all('description')
			locationList = self.request.get_all('location')
			if len(uploads)>0:
				for i in range(len(uploads)):
					blobInfo = uploads[i]
					caption = ""
					description = ""
					location = ""
					photo = create_picture(blobInfo.key(), caption, description, location, self.user.key)
				blobInfo = uploads[0]
				templateVals = {'me': self.user, 'upload_done': 1 ,'coverphoto': blobInfo.key()}
				self.render('upload_popup_photo.html', **templateVals)
				#self.redirect('/%s/photos' % self.user.key.id())
			else:
				uploadUrl = blobstore.create_upload_url('/uploadphoto')
				errorMsg = "Please choose a photo!"
				templateVals = {'me': self.user, 'uploadUrl': uploadUrl, 'submitError': errorMsg}
				self.render('upload_photo.html', **templateVals)
		else:
			self.redirect('/')

class PhotoEditHandler(PageHandler):
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
			self.render('photoedit.html', **templateVals)
		else:
			self.redirect('/')

	def post(self, resource):
		if self.user:
			photoKey = get_key_urlunsafe(resource)
			photo = photoKey.get()
			caption = self.request.get('caption')
			description = self.request.get('description')
			location = self.request.get('location')
			camera = self.request.get('camera')
			lense = self.request.get('lense')
			shutter_speed = self.request.get('shutter_speed')
			aperture = self.request.get('aperture')
			iso = self.request.get('iso')
			tagList = self.request.get_all('tags')
			albumList = self.request.get_all('albums')
			
			photo.caption = caption
			photo.description = description
			photo.location = location
			photo.camera = camera
			photo.lense = lense
			photo.shutter_speed = shutter_speed
			photo.aperture = aperture
			photo.iso = iso
			photo.tags = tagList
			photo.albums = albumList
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
		if self.user:
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
			city = self.request.get('city')
			phone_num = self.request.get('phone_num')
			
			user = self.user
			user.city = city
			user.phone_num = phone_num
			user = update_user_name(name, user)
			user = update_user_alt_email(alt_email, user)
			user = update_user_country(country, user)
			user = update_social_profiles(facebook, youtube, google_plus, twitter, pinterest, website, user)
			user.put()
			self.redirect('/usersettings')
		else:
			self.redirect('/')

class PhotoUploadHandler(blobstore_handlers.BlobstoreUploadHandler, PageHandler):
	def post(self):
		if self.user:
			uploads = self.get_uploads('files')
			captionList = self.request.get_all('caption')
			descriptionList = self.request.get_all('description')
			locationList = self.request.get_all('location')
			if len(uploads)>0:
				for i in range(len(uploads)):
					blobInfo = uploads[i]
					caption = captionList[i]
					description = descriptionList[i]
					location = locationList[i]
					photo = create_picture(blobInfo.key(), caption, description, location, self.user.key)
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

class BlogServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
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
		userid = resource
		user = User.get_by_id(userid)
		logging.info(userid)
		logging.info(user)
		if user:
			if self.user:
				if self.user == user:
					action = self.request.get('actionType')
					photoKey = get_key_urlunsafe(self.request.get('photoKey'))
					if action == "delete":
						delete_photo(photoKey, self.user.key)
						self.redirect('/%s/photos' % self.user.key.id())
					elif action == "edit":
						self.redirect('/editphoto/%s' % photoKey.urlsafe())
				else:
					self.redirect('/')
			else:
				self.redirect('/')
		else:
			self.redirect('/')

class UserPhotosPopUpHandler(PageHandler):
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
			self.render('popup_user_photos.html', **templateVals)
		else:
			self.redirect('/')
			
	def post(self, resource):
		userid = resource
		user = User.get_by_id(userid)
		logging.info(userid)
		logging.info(user)
		if user:
			if self.user:
				if self.user == user:
					action = self.request.get('actionType')
					photoKey = get_key_urlunsafe(self.request.get('photoKey'))
					if action == "delete":
						delete_photo(photoKey, self.user.key)
						self.redirect('/%s/photos' % self.user.key.id())
					elif action == "edit":
						self.redirect('/editphoto/%s' % photoKey.urlsafe())
				else:
					self.redirect('/')
			else:
				self.redirect('/')
		else:
			self.redirect('/')

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
			('/group/([^/]+)', GroupPermpageHandler),
			('/photo/([^/]+)', PhotoPermpageHandler),
			('/editblog/([^/]+)', BlogEditHandler),
			('/([^/]+)/newblog', BlogNewHandler),
			('/([^/]+)/newgroup', GroupNewHandler),
			('/blog' , BlogsHandler),
			('/groups' , GroupsHandler),
			('/photos' , PhotosHandler),
			('/forum', ForumHandler),
			('/search_results', SearchResultsHandler),
			('/editphoto/([^/]+)', PhotoEditHandler),
			('/newphoto', PhotoNewHandler),
			('/popupnewphoto', PopUpPhotoNewHandler),
			('/uploadphoto', PhotoUploadHandler),
			('/popupuploadphoto', PopUpPhotoUploadHandler),
			('/usersettings', UserSettingsHandler),
			('/photo_upload_settings',UserSettingsHandler),
			('/servephoto/([^/]+)', PhotoServeHandler),
			('/serveblog/([^/]+)', BlogServeHandler),
			('/([^/]+)/user_blogs', UserBlogsHandler),
			('/([^/]+)/user_groups', UserGroupsHandler),
			('/([^/]+)/photos', UserPhotosHandler),
			('/([^/]+)/popupphotos', UserPhotosPopUpHandler),
			('/([^/]+)', UserStudioHandler),
			('/([^.]+)', DefaultHandler),
			('/', MainHandler)
			], debug=True)