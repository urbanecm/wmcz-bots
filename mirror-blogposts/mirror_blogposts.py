#!/usr/bin/env python
#-*- coding: utf-8 -*-

import pymysql
import requests
import json
import os

config = json.loads(open('config.json').read())

API_URL = config.get('api')

def make_request(payload, post=False):
	if post:
		return requests.post(API_URL, data=payload, auth=(config.get('user'), config.get('password')))
	else:
		return requests.get(API_URL, params=payload, auth=(config.et('user'), config.get('password')))

def tools_db_connect(database):
	return pymysql.connect(
		database=database,
		host='tools-db',
		read_default_file=os.path.expanduser("~/replica.my.cnf"),
		charset='utf8mb4'
	)

def wordpress_connect():
	return tools_db_connect('s53887__wmcz_web_posts_p')

def tool_connect():
	return tools_db_connect('s53887__wmcz_blog_post_mirror')

pass
