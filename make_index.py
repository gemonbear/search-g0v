# coding=utf-8
import os
from os import walk
import time
import sys
import re
import git
import json

from whoosh.index import create_in
from whoosh.fields import *
import whoosh.index as index
from whoosh.filedb.filestore import FileStorage
from jieba.analyse import ChineseAnalyzer
import html2text

sys.setrecursionlimit(200000)
g = git.cmd.Git('hackpad-backup-g0v')
g.execute(["git", "submodule", "update"])
print('pull from hackpad-backup-g0v: done')


try:
	last_update = open('last_update.txt').read()
	#讀取 pads.json ++
except:
	last_update = 0

with open('hackpad-backup-g0v/pads.json') as data_file:    
	data = json.load(data_file)

git_ff = {}
for pad in data:
	git_ff[pad['padid']] = pad

# 讀取 last_pads.json ++
with open('last_pads.json') as lp: 
	last_pads = json.load(lp)

ff = {}
for k,v in git_ff.items():
	if k not in last_pads:
		ff[k] = git_ff[k]
	if(v['last_backup_time'] > float(last_update)):
		ff[k] = git_ff[k]

print("總共 " + str(len(data)) + " 個 pad")
print("上次建立時間：" + time.ctime(float(last_update)))
print("需要更新數量：" + str(len(ff)))
print("開始建立分詞索引")
print("===================================")

# 使用结巴中文分词
analyzer = ChineseAnalyzer()

# 创建schema, stored为True表示能够被检索
schema = Schema(title=TEXT(stored=True), path=ID(stored=True, unique=True),
				f=TEXT(stored=True, analyzer=analyzer), content=TEXT(stored=False, analyzer=analyzer), modified=TEXT(stored=True))

# 按照schema定义信息，增加需要建立索引的文档
# 注意：字符串格式需要为unicode格式

# 存储schema信息至'indexdir'目录下
indexdir = 'indexdir/'

if not os.path.exists(indexdir):
	os.mkdir(indexdir)
	storage = FileStorage(indexdir)
	ix = create_in(indexdir, schema)
else:
	ix = index.open_dir(indexdir)
	# ix = create_in(indexdir, schema)
	print("open")

writer = ix.writer()

seg_list = []
i = 0
for fk, fx in ff.items():
	try:
		title = html2text.html2text(fx['title'])
		title.strip()
		title = re.sub('[\s+]', '', title)
	except:
		title = "untitled"

	html = open('hackpad-backup-g0v/' + fk + '.html').read()
	all_text = html2text.html2text(html)
	all_text = all_text.strip()
	all_text = re.sub('[\s+]', '', all_text)

	writer.update_document(title=title, path=u'/'+fk, f=fk,
    	                content=all_text, modified=str(time.ctime(fx['last_backup_time'])))	

	print(title + " | " + fk + " | " + str(time.ctime(fx['last_backup_time'])))

	# i = i + 1
	# if(i == 10):
	# 	break

writer.commit(merge=True)
open('last_update.txt', 'w').close()
with open('last_update.txt', 'a') as out:
	done_time = time.time()
	out.write(str(done_time) + '\n')

open('last_pads.json', 'w').close()
with open('last_pads.json', 'a') as out:
	out.write(json.dumps(git_ff))
	out.write('\n')

print("done")
