#!/usr/bin/env python
'''
excel_import_test.py
parsing data exported from mozambique
usage:
    $ python excel_import_test.py /path/to/data.xls
'''
import sys

import xlrd


workbook = xlrd.open_workbook(sys.argv[1])
sheet = workbook.sheet_by_index(0)

for row_number in range(sheet.nrows):
    print sheet.row_values(row_number)



