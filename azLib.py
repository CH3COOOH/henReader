# -*- coding: utf-8 -*-
# <-- AZLIBRARY PROJECT (Python2) -->
# Started: 2018.02.02
# Latest: 2018.05.08

import os
import re
import hashlib
import base64

def timeNow():
	import datetime
	now = datetime.datetime.now()
	return {'YY': now.strftime('%Y'),
			'MM': now.strftime('%m'),
			'DD': now.strftime('%d'),
			'hh': now.strftime('%H'),
			'mm': now.strftime('%M'),
			'ss': now.strftime('%S')}

def multiReplace(origin, mapList):
	# mapList: {wordOri: wordChange, ...}
	for i in mapList.keys():
		origin = origin.replace(i, mapList[i])
	return origin

def reSearch(reStr, article):
	m = re.search(reStr, article)
	if m:
		return m.group()
	else:
		return None

class WebUtilize:

	# --- FUNCTION ---
	# Return the target page's html string
	# ----------------
	def getHtml(self, url, coding='utf-8'):
		import urllib2
		user_agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
		headers = {'User-Agent': user_agent}
		data = ''
		req = urllib2.Request(url, data, headers)
		response = urllib2.urlopen(req)
		return response.read().decode(coding)

class FileOperation:

	# --- EXAMPLE ---
	# <INPUT>
	# fl = fileLstMaker('.', ['.jpg'])
	# <OUTPUT>
	# ['./a.jpg', './b.jpg', './test/c.jpg', './test/test2/d.jpg', ...]
	# ---------------
	def fileLstMaker(self, folder, filter_=None):
		# print('[Info] Building the file list of folder %s...' % folder)
		fileLst = []
		for root, dirs, files in os.walk(folder):
			for f in files:
				fileLst.append(os.path.join(root, f))
		if filter_ != None:
			fileLst = filter((lambda x: os.path.splitext(x)[-1] in filter_), fileLst)
		return sorted(fileLst)

	# --- EXAMPLE ---
	# <INPUT>
	# fl = multiFileLstMaker(['.', './test'], ['.jpg'])
	# <OUTPUT>
	# {'.': [fileLstMaker1], './test': [fileLstMaker2], ...}
	# ---------------
	def multiFileLstMaker(self, folders, filter_=None):
		fileLst = {}
		for folder in folders:
			fileLst[folder] = self.fileLstMaker(folder, filter_)
		return fileLst

	# --- EXAMPLE ---
	# <INPUT>
	# fl = classifiedFileLst('.', ['.jpg'])
	# <OUTPUT>
	# {'.': [fLst1],
	# './001': [fLst2],
	# ...}
	# ---------------
	def classifiedFileLst(self, folder, filter_=None):
		fl = self.fileLstMaker(folder, filter_)
		csf = {}
		for p in fl:
			[folder, fname] = os.path.split(p)
			if folder in csf.keys():
				csf[folder].append(fname)
			else:
				csf[folder] = [fname]
		return csf


class Hash():

	def str2md5(self, plainText):
		hl = hashlib.md5()
		hl.update(base64.b64encode(plainText))
		return hl.hexdigest()