# -*- coding:utf-8 -*-

VER = '1.2'
# =====** henReader Ultimate **=====
# *** os: rar required
# *** python: bottle, pillow and rarfile are required
# *** Put *.zip and *.rar in library/
#
# 2018.05.04(az): 1st live with *.zip support
# 2018.05.05(az): *.rar supported; adjust the layout; add simple entry password
# 2018.05.06(az): 2 layers folders supported; utilize azLib.py
# 2018.05.10(az): Now can import external config file; v1.0
# 2018.05.27(az): Page shows on title; add CG mode plugin
# 2018.09.17(az): Modified sort method to make it sort '10, 2' correctly
# 2019.08.10(az): Transplant to Python 3; add support to Windows
#
# * The *.css files are not created by me :)
# ==================================

import base64
import os
import hashlib
import zipfile
import pickle
import json

# The server depend on follow libraries:
# bottle, pillow, gevent, rarfile
# 'pip install ...' them all
from bottle import Bottle, route, run, template, static_file
from PIL import Image
import rarfile

import azLib as al

# Default config
# ------------------------------------
HOST = '0.0.0.0'
PORT = 8005
PWD_SIMPLE = ''

ROOT_LIB = './library/'
ROOT_STYLE = './css/'
ROOT_THUMB = './thumb/'
FNAME_FOLDERICO = './css/folder.jpg'
FNAME_FS = 'structure.md5'				# The hash of whole file structure
FNAME_IDX = 'index.htm'					# Cache of frontpage
FNAME_MAP = 'status.pcl'				# Map of hash -> file name

TITLE_INDEX = 'henReader'
# ------------------------------------

import re
re_digits = re.compile(r'(\d+)')
def emb_numbers(s):
	pieces=re_digits.split(s)
	pieces[1::2]=map(int,pieces[1::2])
	return pieces

def u28(strRaw, emptyDel=False):
	if emptyDel:
		return strRaw.strip().encode('utf-8')
	else:
		return strRaw.encode('utf-8')

# Read config file (or use default config)
try:
	with open('./config.json', 'r') as o:
		dc = json.load(o)
		print('Try to load from ./config.json...')
	HOST = dc['bind']
	PORT = dc['port']

	PWD_SIMPLE = dc['url_pwd']
	ROOT_LIB = dc['ROOT_LIB']
	ROOT_STYLE = dc['ROOT_CSS']
	ROOT_THUMB = dc['ROOT_THUMB']
	FNAME_FOLDERICO = dc['PATH_FOLDERICO']
	FNAME_FS = dc['PATH_FS']
	FNAME_IDX = dc['PATH_IDX']
	FNAME_MAP = dc['PATH_MAP']
	TITLE_INDEX = dc['title_index']
	rarfile.UNRAR_TOOL = dc['CMD_RAR']
except:
	print('There is no valid ./config.json. Default config used.')

cfs_md5 = None
fo = al.FileOperation()
hs = al.Hash()
hashLst = {}
bookLst = {}


def evrCheck():
	print('Checking runtime...')
	if os.name == 'nt':
		raw_input('Windows, NG!')
		exit()
	print('No problem.')
	print('''====================
 henReader ultimate
 ver %s
====================''' % VER)

def strLengthLimit(strRaw, length, replace='...'):
	if len(strRaw) >= length:
		return strRaw[:length] + replace
	else:
		return strRaw

# ----- Used to create small thumbnails
def imgCompress(fname, sname, resize=(128, 128)):
	img = Image.open(fname)
	img.thumbnail(resize)
	img.save(sname, 'PNG')

def extFilter(rawLst, supported):
	lstNew = []
	for i in rawLst:
		for s in supported:
			if s in i.lower():
				lstNew.append(i)
				break
	return lstNew	

def achFormate(ext, path):
	if ext == '.zip':
		return zipfile.ZipFile(path)
	elif ext == '.rar':
		return rarfile.RarFile(path)

def RW(fname, content, operation):
	if operation == 'w':
		with open(fname, 'w') as o:
			o.write(content)
		return 0
	else:
		with open(fname, 'r') as o:
			return o.read()


# =================================================
# This section is designed to generate html script
# =================================================
def imgUrlGen(path, url=False, resize=(128, 128), ID=None):
	if not url:
		return '<img src=\"%s\" width=\"%d\" height=\"%d\">' % (path, resize[0], resize[1])
	else:
		return '<a href=\"%s\" target=\"%s\"><img src=\"%s\" id=\"%s\"></a>' % (url[0], url[1], path, ID)

def standardHTML(title, content):
	return '''
<html>
<head>
	<title>%s</title>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8" /> 
	<meta name="viewport" content="width=device-width, minimum-scale=1.0, maximum-scale=1.0, user-scalable=0, user-scalable=no"/>
	<link rel="stylesheet" type="text/css" href="/css/main.css"/>
	<link rel="stylesheet" type="text/css" href="/css/style.css"/>
	<script src="/jquery.js"></script>
</head>
<body>
<div class="grid">
<div class="gallary_wrap">
<ul class="cc">
	%s
</ul>
</div>
</div>
<body>
	''' % (title, content)

def indexGen(bookLst, isIndex=True, root=ROOT_LIB, extraShelf=[]):
	frontPage = ''

	# ----- Folder check & add to the page
	for folderName in bookLst.keys():
		# ----- Max folder layer supported.
		# ----- Whithout this, deeper folders would show on frontpage
		if len(folderName.split('/')) >= 4:
			continue

		folderName_md5 = hs.str2md5(folderName.encode())
		hashLst[folderName_md5] = folderName

		if isIndex and folderName == ROOT_LIB[:-1]:
			continue
		if not isIndex:
			break
		frontPage += picBlock(FNAME_FOLDERICO, ('folder/%s' % folderName_md5, ''), strLengthLimit(folderName.replace(ROOT_LIB, ''), 10))
	
	# ----- Plugins can be added via this
	for exUrl in extraShelf:
		frontPage += picBlock(FNAME_FOLDERICO, (exUrl, '_blank'), exUrl)
	
	for folderName in bookLst.keys():
		# ----- Comic from root
		if folderName == ROOT_LIB[:-1] or isIndex == False:
			for bookName in bookLst[folderName]:
				# ----- Make frontpage
				ach = achFormate(os.path.splitext(bookName)[-1], root+bookName)
				bn_md5 = hs.str2md5(bookName.encode())
				path_thumb = ROOT_THUMB + bn_md5
				if os.path.exists(path_thumb) == False:
					with open('%s' % path_thumb, 'wb' ) as o:
						o.write(ach.read(sorted(extFilter(ach.namelist(), ['.jpg', '.png', '.jpeg']))[0]))
					imgCompress(path_thumb, path_thumb, (256, 256))
				ach.close()

				subPath_md5 = hs.str2md5(root[:-1].encode())
				frontPage += picBlock(path_thumb[1:], ('/book/%s/0' % (subPath_md5 + bn_md5), '_blank'), strLengthLimit(bookName, 10))
				#----- Update hashLst
				hashLst[bn_md5] = bookName
	stdHTML = standardHTML(TITLE_INDEX, frontPage)
	return stdHTML

def picBlock(imgPath, Url, text):
	if os.name == 'nt':
		text = ''
	return '''
			<li class="li gallary_item">
			<div class="pic_box">{0}</div>
			<div class="info">{1}</div>
			</li>
			'''.format(imgUrlGen(imgPath, url=Url), text)


class Plugins:
	# History file records url of last page that the user read
	def history(self, fname, text='LAST READ'):
		try:
			with open(fname, 'r') as o:
				last = o.read().strip()
			return '<a href=\"%s">%s</a>' % (last, text)
		except:
			return ''
	
	def CGMode(self, root_img, root_imgUrl='/cg', root_pageUrl='/cgs', page=0):
		imgPath = filter(lambda x: os.path.splitext(x)[-1] in ['.jpg', '.png', '.gif', '.jpeg'], os.listdir(root_img))
		imgPath = list(map(lambda x: root_imgUrl+'/'+x, imgPath))
		if page+1 == len(imgPath):
			html = imgUrlGen(imgPath[page], ('%s/%d' % (root_pageUrl, 0), ''), (1,1), 'mainImg') + '<br>'
		else:
			html = imgUrlGen(imgPath[page], ('%s/%d' % (root_pageUrl, page+1), ''), (1,1), 'mainImg') + '<br>'
		for i in range(len(imgPath)):
			html += '<a href=\"%s/%d\">[%d]</a>' % (root_pageUrl, i, i)
		html += '''
			<script>
			var BORDER = 1.05;
			if (1.0 * $('#mainImg').height() / $(window).height() >= 1.0 * $('#mainImg').width() / $(window).width()) {
				$('#mainImg').height($(window).height()/BORDER);
			} else {
				$('#mainImg').width($(window).width()/BORDER);
			}
			</script>
		'''
		return standardHTML('[%d]%s' % (page, root_imgUrl), html)
		
plugin = Plugins()

# =================================================
# Server response
# =================================================
@route('/'+PWD_SIMPLE)
def index():
	global bookLst
	bookLst = fo.classifiedFileLst(ROOT_LIB, ['.zip', '.rar'])
	bookLst_md5 = hs.str2md5(str(bookLst).encode())
	
	if bookLst_md5 == RW(FNAME_FS, None, 'r'):
		with open(FNAME_MAP, 'rb') as o:
			hashLst = pickle.load(o)
		return static_file(FNAME_IDX, root='.')
	else:
		print('New file list created.')
		hashLst = {}
		stdHTML = indexGen(bookLst, extraShelf=['/cgs/0'])
		RW(FNAME_FS, bookLst_md5, 'w')
		RW(FNAME_IDX, stdHTML, 'w')
		with open(FNAME_MAP, 'wb') as o:
			pickle.dump(hashLst, o)
		return stdHTML

@route('/folder/<folderHash>')
def folder(folderHash):
	folderName = hashLst[folderHash]
	# print('%s\n%s' % (folderName, bookLst[folderName]))
	subLst = {}
	subLst[folderName] = bookLst[folderName]
	return indexGen(subLst, False, folderName+'/')

@route('/<fname>')
def default(fname):
	if fname == 'henReader.py':
		return 'What do you want to do???'
	else:	
		return static_file(fname, root='.')

@route('/css/<fname>')
def css(fname):
	return static_file(fname, root=ROOT_STYLE)

@route('/thumb/<fname>')
def thumb(fname):
	return static_file(fname, root=ROOT_THUMB, mimetype='image/png')

@route('/book/<pathHash>/<page>')
def reader(pathHash, page):
	bookPath = '%s/%s' % (hashLst[pathHash[:32]], hashLst[pathHash[32:]])
	# print bookPath
	fExt = os.path.splitext(bookPath)[-1]
	if fExt == '.zip':
		zbook = zipfile.ZipFile(bookPath)
	elif fExt == '.rar':
		zbook = rarfile.RarFile(bookPath)
	imgLst = sorted(extFilter(zbook.namelist(), ['.jpg', '.png', '.jpeg']), key=emb_numbers)
	page_total = len(imgLst)
	if int(page) >= page_total:
		return 'You have finished this book.'
	fCurrent = 'data:image/jpeg;base64,' + base64.b64encode(zbook.read(imgLst[int(page)])).decode()
	zbook.close()
	html_img = imgUrlGen(fCurrent, ('/book/%s/%d' % (pathHash, int(page)+1), ''), (1,1), 'mainImg') + '<br>'
	for i in range(page_total):
		html_img += '<a href=\"/book/%s/%d\">[%d]</a>' % (pathHash, i, i)
	html_img += '''
	<script>
		var BORDER = 1.05;
		if (1.0 * $('#mainImg').height() / $(window).height() >= 1.0 * $('#mainImg').width() / $(window).width()) {
			$('#mainImg').height($(window).height()/BORDER);
		} else {
			$('#mainImg').width($(window).width()/BORDER);
		}
	</script>
	'''
	
	## This is user for histry plugin
	## --------------------------------------------
	# with open('reading', 'w') as o:
	# 	o.write('book/%s/%s' % (pathHash, page))
	## --------------------------------------------
	
	return standardHTML('[%s]'%page + hashLst[pathHash[32:]], html_img)

# CGMode plugin - 2018.05.27
# ----------------------------------------------------------------------
@route('/cg/<fname>')
def cgPath(fname):
	return static_file(fname, root=ROOT_LIB+'cg', mimetype='image/png')

@route('/cgs/<page>')
def cgMode(page):
	return plugin.CGMode(ROOT_LIB+'cg', page=int(page))
# ----------------------------------------------------------------------
	
if __name__ == '__main__':

	bookLst = fo.classifiedFileLst(ROOT_LIB, ['.zip', '.rar'])
	cfs_md5 = hs.str2md5(str(bookLst).encode())
	RW(FNAME_FS, cfs_md5, 'w')
	RW(FNAME_IDX, indexGen(bookLst, extraShelf=['/cgs/0']), 'w')
	with open(FNAME_MAP, 'wb') as o:
		pickle.dump(hashLst, o)

	run(host=HOST, port=PORT, debug=True)