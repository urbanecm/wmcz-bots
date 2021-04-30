#!/bin/bash

set -e

mkdir /tmp/$$
echo /tmp/$$
wget -O /tmp/$$/wmcz_web_posts_p.sql.gz https://files.wikimedia.cz/datasets/web-posts/wmcz_web_posts_p.sql.gz
gzip -d /tmp/$$/wmcz_web_posts_p.sql.gz
mysql -h tools-db s53887__benes_reports_p < /tmp/$$/wmcz_web_posts_p.sql
rm -rf /tmp/$$
