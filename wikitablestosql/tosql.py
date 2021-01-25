
import sqlite3
import re


row_regexp = re.compile(r'(^|\s)rowspan *=\D*(\d+)\D?')
col_regexp = re.compile(r'(^|\s)colspan *=\D*(\d+)\D?')


def extract_col_and_row_span(attrib):
    """
    Get column and row span from table cell attribute.

    :param attrib: attribute as string
    :return: span information as dict
    """

    span = {'rowspan': '', 'colspan': ''}

    r = row_regexp.search(attrib)
    c = col_regexp.search(attrib)

    # Extract row span and col span if possible
    if r is not None:
        span['rowspan'] = int(r.group(2))
    else:
        span['rowspan'] = 1
    if c is not None:
        span['colspan'] = int(c.group(2))
    else:
        span['colspan'] = 1
    return span


# Create the two tables
def sql_table_creation(database):
    """Create sql tables"""

    sql_connection = sqlite3.connect(database)
    sql_cursor = sql_connection.cursor()

    # Table of table information creation
    sql_form = 'CREATE TABLE WikitableInformation ' \
               '( page_name text, table_name text, table_attributes text, caption text, ' \
               'caption_attributes text)'
    sql_cursor.execute(sql_form)

    # Table of tabular data creation
    sql_form = 'CREATE TABLE WikitableData ' \
               '( table_name text, row int, col int, cell_data text, cell_attributes text, ' \
               'is_header integer, row_span integer, col_span integer)'
    sql_cursor.execute(sql_form)

    sql_connection.commit()
    sql_connection.close()


def wikitable_data_to_sql(wikitabledata, sql_cursor):
    """
    Insertion of wikitable information and cell data into sql database via given cursor.

    :param wikitabledata: wikitable data as dict
    :param sql_cursor: sqlite3 cursor object
    :return:
    """

    # Insertion of data in WikitableInformation
    table_info_form = 'INSERT INTO WikitableInformation VALUES (?, ?, ?, ?, ?)'
    table_name = wikitabledata['pagename'] + '_' + str(wikitabledata['tablecount'])
    sql_cursor.execute(table_info_form, (wikitabledata['pagename'],
                                         table_name,
                                         wikitabledata['tableattribute'],
                                         wikitabledata['caption']['name'],
                                         wikitabledata['caption']['attribute']))

    # Insertion of data in WikitableData
    data_form = 'INSERT INTO WikitableData VALUES (?, ?, ?, ?, ?, ?, ?, ?)'

    for i, row in enumerate(wikitabledata['rows']):
        for j, el in enumerate(row):
            row_span = extract_col_and_row_span(el['fullattribute'])['rowspan']
            col_span = extract_col_and_row_span(el['fullattribute'])['colspan']
            sql_cursor.execute(data_form, (table_name, i, j, el['celldata'], el['fullattribute'],
                                           int(el['isheader']), row_span, col_span))


def process_many_wikitables_into_sql_database(wikitabledata_list, database):
    """
    Process list of wikitables into sqlite3 database.

    :param wikitabledata_list: list of wikitabledata (each wikitabledata is a dict)
    :param database: path as string
    :return:
    """

    sql_connection = sqlite3.connect(database)
    sql_cursor = sql_connection.cursor()

    for i in wikitabledata_list:
        wikitable_data_to_sql(i, sql_cursor)

    sql_connection.commit()
    sql_connection.close()
