
import os
import re
import json
import collections

from ..wikitablestosql import wikitableparser

row_regexp = re.compile(r'(^|\s)rowspan *=\D*(\d+)\D?')
col_regexp = re.compile(r'(^|\s)colspan *=\D*(\d+)\D?')


def extract_col_and_row_span(attrib):
    """
    Extract column span and row span from attribute

    :param attrib: string
    :return: dict
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


def parsed_to_sql_ready(raw_wikitable_with_meta):
    wikitabledata = wikitableparser.wikitable_parser(raw_wikitable_with_meta['WikitableData'],
                                                     raw_wikitable_with_meta['PageName'],
                                                     raw_wikitable_with_meta['TableId'])

    table_name = wikitabledata['pagename'] + '_' + str(wikitabledata['tablecount'])
    table_info = (wikitabledata['pagename'],
                  table_name,
                  wikitabledata['tableattribute'],
                  wikitabledata['caption']['name'],
                  wikitabledata['caption']['attribute'])

    table_data = []
    for i, row in enumerate(wikitabledata['rows']):
        for j, el in enumerate(row):
            row_span = extract_col_and_row_span(el['fullattribute'])['rowspan']
            col_span = extract_col_and_row_span(el['fullattribute'])['colspan']
            table_data.append((table_name, i, j, el['celldata'], el['fullattribute'],
                               int(el['isheader']), row_span, col_span))

    return table_info, table_data


def nested_list_to_nested_tuple(li):
    """
    Transform a nested list to a nested tuple

    :param li: list
    :return: tuple
    """

    t = []
    for i in li:
        if type(i) is list:
            t.append(nested_list_to_nested_tuple(i))
        else:
            t.append(i)

    return tuple(t)


def check_test_file(test_file):
    """
    :param test_file: list of elements of form: { "parsed": [row_of_table_info, list_of_data_rows],
                                                    "raw": raw_with_meta_dict }
    :return: bool
    """

    # Load test_file
    with open(test_file, mode='r', encoding='UTF-8') as f:
        loaded = json.load(f)

    for i in loaded:
        from_file_raw = i['raw']
        from_file_parsed = i['parsed']
        parsed = parsed_to_sql_ready(from_file_raw)

        if collections.Counter(nested_list_to_nested_tuple(from_file_parsed[0])) \
                != collections.Counter(nested_list_to_nested_tuple(parsed[0])):
            return False
        if collections.Counter(nested_list_to_nested_tuple(from_file_parsed[1])) \
                != collections.Counter(nested_list_to_nested_tuple(parsed[1])):
            return False

    return True


if __name__ == "__main__":
    test_file_path = os.path.join('.', 'wikitablestosql', 'tests', 'test_rawtosql_data.json')
    if check_test_file(test_file_path):
        print("Test 'rawtosql' Passed!")
