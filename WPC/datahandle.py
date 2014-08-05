from datamodel import *
import utils
import logging

def create_user(email, name, password):
	user = User(id=email, name=name, email=email, score=0)
	user.passwordHash = utils.hash_password(email, password)
	userKey = user.put()
	fbook = create_favoritebook(userKey)
	sbook = create_storybook(userKey)
	mysbook = create_mystorybook(userKey)
	return user

def create_blog(title, content, parent_key):
	blog = Blog(title=title, content=content, likes=0, parent=parent_key)
	blogKey = blog.put()
	return blog

def create_picture(blobKey, parent_key):
	pic = Picture(blobKey=blobKey, likes=0, parent=parent_key)
	picKey = pic.put()
	return pic

def create_favoritebook(parent_key):
	fbook = Favoritebook(parent=parent_key)
	fbookKey = fbook.put()
	return fbook

def create_storybook(parent_key):
	sbook = Storybook(parent=parent_key)
	sbookKey = sbook.put()
	return sbook

def create_mystorybook(parent_key):
	sbook = MyStorybook(parent=parent_key)
	sbookKey = sbook.put()
	return sbook

def delete_blog(blog_key, user_key):
	if user_key == blog_key.parent():
		blog_key.delete()
	return

def delete_photo(photo_key, user_key):
	if user_key == photo_key.parent():
		blobKey = photo_key.get().blobKey
		blobInfo = blobstore.BlobInfo.get(blobKey)
		blobInfo.delete()
		photo_key.delete()
	return

def get_key_urlunsafe(urlsafeKey):
	try:
		unsafeKey = ndb.Key(urlsafe=urlsafeKey)
	except:
		unsafeKey = None
	return unsafeKey

def get_edit_photo_urlstring(photoList):
	urlString = ""
	for photo in photoList:
		urlString = urlString + str(photo.key.id()) + '+'
	urlString = urlString[:-1]
	return urlString

def get_photolist_from_urlstring(urlString, userKey):
	photoList = []
	if urlString:
		photoIdList = urlString.split(" ")
		for photoId in photoIdList:
			photo = ndb.Key('Picture', int(photoId), parent=userKey).get()
			photoList.append(photo)
			logging.info(photoId)
	else:
		logging.error("Empty urlString!")
	return photoList