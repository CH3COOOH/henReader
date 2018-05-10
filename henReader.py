# -*- coding: utf-8 -*-

VER = '1.0'
# =====** henReader Ultimate **=====
# *** os: rar required
# *** python: bottle, pillow and rarfile are required
# *** Put *.zip and *.rar in library/
#
# 2018.05.04(az): 1st live with *.zip support
# 2018.05.05(az): *.rar supported; adjust the layout; add simple entry password
# 2018.05.06(az): 2 layers folders supported; utilize azLib.py
# 2018.05.10(az): Now can import external config file; v1.0
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
from gevent import monkey
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

def u28(strRaw, emptyDel=False):
	if emptyDel:
		return strRaw.strip().encode('utf-8')
	else:
		return strRaw.encode('utf-8')

try:
	with open('./config.json', 'r') as o:
		dc = json.load(o)
		print('Try to load from ./config.json...')
	HOST = dc['bind']
	PORT = dc['port']

	PWD_SIMPLE = dc['url_pwd']
	ROOT_LIB = u28(dc['ROOT_LIB'])
	ROOT_STYLE = u28(dc['ROOT_CSS'])
	ROOT_THUMB = u28(dc['ROOT_THUMB'])
	FNAME_FOLDERICO = u28(dc['PATH_FOLDERICO'])
	FNAME_FS = u28(dc['PATH_FS'])
	FNAME_IDX = u28(dc['PATH_IDX'])
	FNAME_MAP = u28(dc['PATH_MAP'])
	TITLE_INDEX = u28(dc['title_index'])
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

def indexGen(bookLst, isIndex=True, root=ROOT_LIB):
	frontPage = ''

	# ----- Folder check & add to the page
	for folderName in bookLst.keys():
		# ----- Max folder layer supported.
		# ----- Whithout this, deeper folders would show on frontpage
		if len(folderName.split('/')) >= 4:
			continue

		folderName_md5 = hs.str2md5(folderName)
		hashLst[folderName_md5] = folderName
		# print ('%s %s' % (folderName, ROOT_LIB))
		if isIndex and folderName == ROOT_LIB[:-1]:
			continue
		if not isIndex:
			break
		frontPage += picBlock(FNAME_FOLDERICO, ('folder/%s' % folderName_md5, ''), strLengthLimit(folderName.replace(ROOT_LIB, ''), 48))
	
	for folderName in bookLst.keys():
		# ----- Comic from root
		if folderName == ROOT_LIB[:-1] or isIndex == False:
			for bookName in bookLst[folderName]:
				# ----- Make frontpage
				ach = achFormate(os.path.splitext(bookName)[-1], root+bookName)
				bn_md5 = hs.str2md5(bookName)
				path_thumb = ROOT_THUMB + bn_md5
				if os.path.exists(path_thumb) == False:
					with open('%s' % path_thumb, 'w' ) as o:
						o.write(ach.read(sorted(extFilter(ach.namelist(), ['.jpg', '.png', '.jpeg']))[0]))
					imgCompress(path_thumb, path_thumb, (256, 256))
				ach.close()

				subPath_md5 = hs.str2md5(root[:-1])
				frontPage += picBlock(path_thumb[1:], ('/book/%s/0' % (subPath_md5 + bn_md5), '_blank'), strLengthLimit(bookName, 48))
				#----- Update hashLst
				hashLst[bn_md5] = bookName
	stdHTML = standardHTML(TITLE_INDEX, frontPage)
	return stdHTML

def picBlock(imgPath, Url, text):
	return '''
			<li class="li gallary_item">
			<div class="pic_box">%s</div>
			<div class="info">%s</div>
			</li>
			''' % (imgUrlGen(imgPath, url=Url), text)



# =================================================
# Server response
# =================================================
@route('/'+PWD_SIMPLE)
def index():
	global bookLst
	bookLst = fo.classifiedFileLst(ROOT_LIB, ['.zip', '.rar'])
	bookLst_md5 = hs.str2md5(str(bookLst))
	if hs.str2md5(str(bookLst)) == RW(FNAME_FS, None, 'r'):
		hashLst = pickle.load(open(FNAME_MAP, 'r'))
		return static_file(FNAME_IDX, root='.')
	else:
		print('New file list created.')
		hashLst = {}
		stdHTML = indexGen(bookLst)
		RW(FNAME_FS, bookLst_md5, 'w')
		RW(FNAME_IDX, stdHTML, 'w')
		pickle.dump(hashLst, open(FNAME_MAP, 'w'))
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
def default(fname):
	return static_file(fname, root=ROOT_STYLE)

@route('/thumb/<fname>')
def default(fname):
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
	imgLst = sorted(extFilter(zbook.namelist(), ['.jpg', '.png', '.jpeg']))
	page_total = len(imgLst)
	if int(page) >= page_total:
		return 'You have finished this book.'
	fCurrent = 'data:image/jpeg;base64,' + base64.b64encode(zbook.read(imgLst[int(page)]))
	zbook.close()
	html_img = imgUrlGen(fCurrent, ('/book/%s/%d' % (pathHash, int(page)+1), ''), (1,1), 'mainImg') + '<br>'
	for i in xrange(page_total):
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
	return standardHTML(unicode(hashLst[pathHash[32:]], 'utf-8'), html_img)


if __name__ == '__main__':
	evrCheck()
	monkey.patch_all()

	bookLst = fo.classifiedFileLst(ROOT_LIB, ['.zip', '.rar'])
	cfs_md5 = hs.str2md5(str(bookLst))
	RW(FNAME_FS, cfs_md5, 'w')
	RW(FNAME_IDX, indexGen(bookLst), 'w')
	pickle.dump(hashLst, open(FNAME_MAP, 'w'))

	run(host=HOST, port=PORT, debug=True, server='gevent')