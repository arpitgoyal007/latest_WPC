import re
import random
import hashlib
import hmac
from string import letters
import logging

COOKIE_USERINFO_SECRET = "userinfosecret"
COOKIE_DEFAULT_SECRET = "defaultsecret"

def format_cookie(cookie):
	cookieDict = {}
	if cookie:
		cookieList = cookie.split(":")
		for c in cookieList:
			cVals = c.split("=")
			cookieDict[cVals[0]] = cVals[1]
	else:
		logging.error("Cookie empty in format_cookie")
	return cookieDict

def hash_cookie_val(secret, cookieVal):
	return hmac.new(secret, cookieVal).hexdigest()

def find_cookie_secret(cookieName):
	if cookieName == "userinfo":
		secret = COOKIE_USERINFO_SECRET
	else:
		secret = COOKIE_DEFAULT_SECRET
	return secret

def secure_cookie_val(cookieName, cookieVal):
	secret = find_cookie_secret(cookieName)
	return "%s|%s" % (cookieVal, hash_cookie_val(secret, cookieVal))

def check_secure_cookie_val(cookieName, secureCookieVal):
	secret = find_cookie_secret(cookieName)
	secureCookieValList = secureCookieVal.split('|')
	if len(secureCookieValList) > 1:
		cookieVal = secureCookieValList[0]
		cookieValHash = secureCookieValList[1]
		return hash_cookie_val(secret, cookieVal) == cookieValHash

def make_password_salt(length=5):
	return "".join(random.choice(letters) for x in xrange(length))

def hash_password(userId, userPwd, salt=None):
	if not salt:
		salt = make_password_salt()
	pwdHash = hashlib.sha256(userId + userPwd + salt).hexdigest()
	return "%s,%s" % (salt, pwdHash)

def valid_password(userId, userPwd, securePwd):
	salt = securePwd.split(',')[0]
	return hash_password(userId, userPwd, salt) == securePwd