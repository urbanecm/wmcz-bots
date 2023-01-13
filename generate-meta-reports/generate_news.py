#!/usr/bin/env python

import subprocess
from subprocess import PIPE
import requests
import json
from datetime import datetime, timedelta
import pywikibot
import pymysql
import os
import sys
import urllib.parse

TAGS = {
	'komunita-a-multimedia': 'community',
	'community-and-multimedia': 'community',
	'wikidata': 'partnership-wikidata'
}

site = pywikibot.Site('meta', 'meta')

class WordPress():
	def __init__(self):
		self.conn = pymysql.connect(
			database='s53887__wmcz_website_p',
			host='tools-db',
			read_default_file=os.path.expanduser("~/replica.my.cnf"),
			charset='utf8mb4'
		)
	
	def get_posts(self, category=None, date_prefix=None):
		params = []
		conds = []

		if category is not None:
			conds.append('ID IN (SELECT post_id FROM news_category WHERE slug=%s)')
			params.append(category)

		if date_prefix is not None:
			conds.append('post_date_gmt LIKE %s')
			params.append('%s-%%' % date_prefix)

		# never generate this months posts, as they are guaranteed to be incomplete
		conds.append('post_date_gmt < %s')
		d = datetime.today() - timedelta(days=30)
		params.append(d.strftime('%Y-%m-%d'))

		with self.conn.cursor(pymysql.cursors.DictCursor) as cur:
			if len(conds) == 0:
				cur.execute('SELECT * FROM news_web')
			else:
				cur.execute('SELECT * FROM news_web WHERE %s' % ' AND '.join(conds), tuple(params))
			data = cur.fetchall()

		return data
	
	def get_post_tags(self, post_id):
		with self.conn.cursor() as cur:
			cur.execute('SELECT slug FROM news_tags WHERE post_id=%s', (post_id, ))
			data = cur.fetchall()
		return [x[0].replace('-en', '') for x in data]

def translate_tag(tag_name_raw):
	tag_name = tag_name_raw.replace('-en', '')
	tag_name = TAGS.get(tag_name, tag_name)
	return "{{User:Wikimedia Czech Republic's bot/program-en|%s}}" % tag_name

if __name__ == "__main__":
	wp = WordPress()

	date_prefix = None
	if len(sys.argv) == 2:
		date_prefix = sys.argv[1]

	posts = wp.get_posts(category="nezarazene-en", date_prefix=date_prefix)

	output_dict = {}
	META_PAGE_PREFIX = "Wikimedia Czech Republic/Reports"
	ERROR_PAGE_TITLE = "User:Wikimedia Czech Republic's bot/Reports/Errors"
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

		post_tag = translate_tag(post_tag)

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

		processed_tags = list(output_dict[date_fmt].keys())
		processed_tags.sort()

		# ensure other is the end, if present
		other_translated = translate_tag('other')
		if other_translated in processed_tags:
			processed_tags.pop(processed_tags.index(other_translated))
			processed_tags.append(other_translated)

		for tag in processed_tags:
			text += "== %s ==\n" % tag
			for post in output_dict[date_fmt][tag]:
				text += post + "\n"

		f = open('/data/project/wmcz/public_html/.wmcz_meta_reports/%s.txt' % date_fmt, 'w')
		f.write(text)
		f.close()

		page.text = text
		try:
			page.save("Bot: Prepare WMCZ's monthly report")
		except pywikibot.exceptions.SpamblacklistError:
			print('ERROR: SpamblacklistError, reporting to meta')
			errorPage = pywikibot.Page(site, ERROR_PAGE_TITLE)
			backupUrl = 'https://wmcz.toolforge.org/.wmcz_meta_reports/%s.txt' % urllib.parse.quote(date_fmt)
			errorPage.text += '\n* [[Wikimedia Czech Republic/Reports/%s|%s]]: spam blacklist hit ([%s content available])' % (date_fmt, date_fmt, backupUrl)
			errorPage.save('Bot: Report an error')
