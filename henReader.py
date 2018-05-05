# -*- coding: utf-8 -*-

# =====** henReader Ultimate **=====
# *** Put *.zip in library/
# 2018.05.04: 1st live with *.zip support
# ==================================

import base64
import os
import hashlib

from bottle import Bottle, route, run, template, static_file
from PIL import Image
import zipfile

BOOK_DIR = './library'

def evrCheck():
	print('Checking runtime...')
	if os.name == 'nt':
		print('Windows NG!')
		return -1
	for fname in ['css', 'thumb', BOOK_DIR]:
		if not os.path.exists(fname):
			os.mkdir(fname)

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

hashLst = {}

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

@route('/')
def index():

	frontPage = ''
	hl = hashlib.md5()

	bookLst = filter(lambda x: '.zip' in x, os.listdir(BOOK_DIR))
	for bookName in bookLst:
		# ----- Make frontpage
		z = zipfile.ZipFile('./library/' + bookName)
		hl.update(base64.b64encode(bookName))
		bn_md5 = hl.hexdigest()
		path_thumb = './thumb/' + bn_md5
		if os.path.exists(path_thumb) == False:
			with open('%s' % path_thumb, 'w' ) as o:
				o.write(z.read(sorted(extFilter(z.namelist(), ['.jpg', '.png', '.jpeg']))[0]))
			imgCompress(path_thumb, path_thumb, (256, 256))
		z.close()

		frontPage += '''
		<li class="li gallary_item">
		<div class="pic_box">%s</div>
		<div class="info">%s</div>
		</li>
		''' % (imgUrlGen(path_thumb, ('book/%s/0' % bn_md5, '_blank')), bookName)

		#----- Update hashLst
		hashLst[bn_md5] = bookName
	return standardHTML('index', frontPage)

@route('/<fname>')
def default(fname):
	return static_file(fname, root='.')

@route('/css/<fname>')
def default(fname):
	return static_file(fname, root='./css/')

@route('/thumb/<fname>')
def default(fname):
	return static_file(fname, root='./thumb/', mimetype='image/png')

@route('/book/<nameHash>/<page>')
def reader(nameHash, page):
	bookPath = './library/' + unicode(hashLst[nameHash], 'utf-8')
	# print bookPath
	zbook = zipfile.ZipFile(bookPath)
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