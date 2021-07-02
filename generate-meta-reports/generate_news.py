#!/usr/bin/env python

import subprocess
from subprocess import PIPE
import requests
import json
from datetime import datetime
import pywikibot
import pymysql
import os

site = pywikibot.Site('meta', 'meta')

class WordPress():
	def __init__(self):
		self.conn = pymysql.connect(
			database='s53887__wmcz_reports_p',
			host='tools-db',
			read_default_file=os.path.expanduser("~/replica.my.cnf"),
			charset='utf8mb4'
		)
	
	def get_posts(self, category=None):
		if category is None:
			with self.conn.cursor(pymysql.cursors.DictCursor) as cur:
				cur.execute('SELECT * FROM news_web')
				data = cur.fetchall()
		else:
			with self.conn.cursor(pymysql.cursors.DictCursor) as cur:
				cur.execute('SELECT * FROM news_web WHERE ID IN (SELECT post_id FROM news_category WHERE slug=%s)', (category, ))
				data = cur.fetchall()
		
		return data
	
	def get_post_tags(self, post_id):
		with self.conn.cursor() as cur:
			cur.execute('SELECT slug FROM news_tags WHERE post_id=%s', (post_id, ))
			data = cur.fetchall()
		return [x[0].replace('-en', '') for x in data]
	

if __name__ == "__main__":
	wp = WordPress()
	posts = wp.get_posts(category="nezarazene-en")

	output_dict = {}
	META_PAGE_PREFIX = "Wikimedia Czech Republic/Reports"
	for post in posts:
		d = post.get('post_date_gmt')
		date_fmt = d.strftime('%B %Y')
		page = pywikibot.Page(site, '%s/%s' % (META_PAGE_PREFIX, date_fmt))
		if page.exists():
			print('Skipping %s' % page.title())
			continue # TODO: maybe replace with a break?

		post_id = post.get('ID')
		post_tags = wp.get_post_tags(post_id)
		if len(post_tags) == 0:
			post_tag = "other"
		else:
			post_tag = post_tags[0] # TODO: support for multiple tags?
		if post_tag == 'ostatni':
			post_tag = 'other'
		if not date_fmt in output_dict:
			output_dict[date_fmt] = {}
	
		if not post_tag in output_dict[date_fmt]:
			output_dict[date_fmt][post_tag] = []

		p = subprocess.Popen(['pandoc', '-f', 'html', '-t', 'mediawiki'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
		out, err = p.communicate(input=post.get('post_content').encode('utf-8'))
		post_content_wikitext = out.decode('utf-8')
	
		post_formatted = """
=== %(post_date)s: %(post_title)s ===
%(post_content)s

[%(url)s Read more...]""" % {
	"post_date": d.strftime('%Y-%m-%d'),
	"post_title": post.get('post_title'),
	"post_content": post_content_wikitext.strip(),
	"url": post.get('guid')
}

		output_dict[date_fmt][post_tag].append(post_formatted)

	for date_fmt in output_dict:
		page = pywikibot.Page(site, "%s/%s" % (META_PAGE_PREFIX, date_fmt))
		if page.exists():
			continue # do not overwrite pages
	
		text = "{{User:Wikimedia Czech Republic's bot/Reports/Header|title=%s|subtitle=Report}}\n\n" % date_fmt

		for tag in output_dict[date_fmt]:
			text += "== %s ==\n" % tag
			for post in output_dict[date_fmt][tag]:
				text += post + "\n"
		
		page.text = text
		page.save("Bot: Prepare WMCZ's monthly report")
