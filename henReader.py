# -*- coding: utf-8 -*-

# =====** henReader Ultimate **=====
# *** Put *.zip in library/
# 2018.05.04(az): 1st live with *.zip support
# 2018.05.05(az): *.rar supported; adjust the layout
# * The *.css files are not created by me :)
# ==================================

import base64
import os
import hashlib
import zipfile

from bottle import Bottle, route, run, template, static_file
from PIL import Image
import rarfile

ROOT_LIB = './library/'
ROOT_STYLE = './css/'
ROOT_THUMB = './thumb/'

TITLE_INDEX = 'henReader'

def evrCheck():
	print('Checking runtime...')
	if os.name == 'nt':
		print('Windows, NG!')
		exit()
	# for fname in ['css', 'thumb', ROOT_LIB]:
	# 	if not os.path.exists(fname):
	# 		os.mkdir(fname)

def imgCompress(fname, sname, resize=(128, 128)):
	img = Image.open(fname)
	img.thumbnail(resize)
	img.save(sname, 'PNG')

def imgUrlGen(path, url=False, resize=(128, 128), ID=None):
	if not url:
		return '<img src=\"%s\" width=\"%d\" height=\"%d\">' % (path, resize[0], resize[1])
	else:
		return '<a href=\"%s\" target=\"%s\"><img src=\"%s\" id=\"%s\"></a>' % (url[0], url[1], path, ID)

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

hashLst = {}

@route('/')
def index():

	frontPage = ''
	hl = hashlib.md5()

	bookLst = filter((lambda x: os.path.splitext(x)[-1] in ['.rar', '.zip']), os.listdir(ROOT_LIB))
	for bookName in bookLst:
		# ----- Make frontpage
		ach = achFormate(os.path.splitext(bookName)[-1], ROOT_LIB+bookName)
		hl.update(base64.b64encode(bookName))
		bn_md5 = hl.hexdigest()
		path_thumb = ROOT_THUMB + bn_md5
		if os.path.exists(path_thumb) == False:
			with open('%s' % path_thumb, 'w' ) as o:
				o.write(ach.read(sorted(extFilter(ach.namelist(), ['.jpg', '.png', '.jpeg']))[0]))
			imgCompress(path_thumb, path_thumb, (256, 256))
		ach.close()

		frontPage += '''
		<li class="li gallary_item">
		<div class="pic_box">%s</div>
		<div class="info">%s</div>
		</li>
		''' % (imgUrlGen(path_thumb, ('book/%s/0' % bn_md5, '_blank')), bookName)

		#----- Update hashLst
		hashLst[bn_md5] = bookName
	return standardHTML(TITLE_INDEX, frontPage)

@route('/<fname>')
def default(fname):
	return static_file(fname, root='.')

@route('/css/<fname>')
def default(fname):
	return static_file(fname, root=ROOT_STYLE)

@route('/thumb/<fname>')
def default(fname):
	return static_file(fname, root=ROOT_THUMB, mimetype='image/png')

@route('/book/<nameHash>/<page>')
def reader(nameHash, page):
	bookPath = ROOT_LIB + unicode(hashLst[nameHash], 'utf-8')
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
	html_img = imgUrlGen(fCurrent, ('/book/%s/%d' % (nameHash, int(page)+1), ''), (512,512), 'mainImg') + '<br>'
	for i in xrange(page_total):
		html_img += '<a href=\"/book/%s/%d\">[%d]</a>' % (nameHash, i, i)
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
	return standardHTML(unicode(hashLst[nameHash], 'utf-8'), html_img)


if __name__ == '__main__':
	evrCheck()
	from gevent import monkey
	monkey.patch_all()
	run(host='0.0.0.0', port=8005, debug=True, server='gevent')