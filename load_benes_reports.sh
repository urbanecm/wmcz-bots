#!/bin/bash

set -e

mkdir /tmp/$$
echo /tmp/$$
wget -O /tmp/$$/wmcz_reports_p.sql.gz https://files.wikimedia.cz/datasets/wmcz_reports_p.sql.gz
gzip -d /tmp/$$/wmcz_reports_p.sql.gz
mysql -h tools-db s53887__benes_reports_p < /tmp/$$/wmcz_reports_p.sql
rm -rf /tmp/$$
