# -*- coding: utf-8 -*-
#!python -m json.tool
import xlwt
import xlrd
from datetime import datetime
import json
xlrd.Book.encoding = "utf-8"
wb = xlrd.open_workbook(u'运营汇总.xlsx')
table0 = wb.sheet_by_name(u'分区名字')
ZONENAME = {}

for x in xrange(4, table0.nrows):

	ZONENAME[int(table0.cell(x, 0).value)] = table0.cell(x, 2).value

print 'ZONENAME =', json.dumps(ZONENAME, sort_keys=True, indent=2, separators=(',', ': '), ensure_ascii=False)

