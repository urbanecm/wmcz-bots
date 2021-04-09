#!/usr/bin/env python

import pywikibot
from pywikibot import pagegenerators
from datetime import datetime
from collections import OrderedDict

site = pywikibot.Site()
genFactory = pagegenerators.GeneratorFactory(site)
genFactory.handle_arg('-search:prefix:"Wikimedia Czech Republic/Reports/"')
generator = genFactory.getCombinedGenerator()

reports_years = {}
for page in generator:
	if page.title() == "User:Wikimedia Czech Republic's bot/Reports/Header":
		continue
	month = page.title().replace("Wikimedia Czech Republic/Reports/", "")
	d = datetime.strptime(month, '%B %Y')
	if d.year not in reports_years:
		reports_years[d.year] = {}
	reports_years[d.year][d] = page

reports_years_sorted = OrderedDict(sorted(reports_years.items(), key=lambda t: t[0]))
output = "== Wikimedia Czech Republic's monthly reports ==\n"
for year, reports_year in reports_years_sorted.items():
	reports_month = OrderedDict(sorted(reports_year.items(), key=lambda t: t[0]))

	output += "; %s\n" % str(year)
	year_arr = []
	for month, report in reports_month.items():
		year_arr.append("[[%s|%s]]" % (report.title(), month.strftime('%B %Y')))
	
	output += " · ".join(year_arr) + "\n"

page = pywikibot.Page(site, "Wikimedia Czech Republic/Reports")
page.text = output
page.save('Bot: Update list of Wikimedia Czech Republic\'s reports')
