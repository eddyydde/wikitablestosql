
from importlib import util

from . import wikitableparser


defused_check = util.find_spec('defusedxml')
if defused_check is not None:
    import defusedxml.ElementTree as Et
else:
    import xml.etree.ElementTree as Et


# Get wikitables
def get_wikitables_from_string(string):
    """
    Get raw wikitables from "unstructured" string

    :param string:
    :return: list of raw wikitables
    """

    last = ''
    in_table = False
    newline = False
    waiting = False
    temp_string = ''
    table_count = 0
    list_of_tables = []
    table_nest_level = 0

    for i in string:
        if in_table:
            temp_string += i
        if i == '\n':
            newline = True
        elif newline:
            if i == '{' or i == '|':
                waiting = True
                newline = False
            elif i != '\n':
                newline = False
        elif waiting:
            if last == '{' and i == '|':
                if table_nest_level == 0:
                    in_table = True
                    temp_string += '{|'
                table_nest_level += 1
            elif last == '|' and i == '}':
                if in_table:
                    table_nest_level += -1
                    if table_nest_level == 0:
                        in_table = False
                        list_of_tables.append([table_count, temp_string])
                        temp_string = ''
                        table_count += 1
        last = i

    return list_of_tables


def extract_wikitables_from_file(file):
    """
    Extract wikitables from xml file

    :param file: path as string
    :return: list of wikitabledata elements (list of dict)
    """

    wikitabledata_list = []
    
    with open(file, mode='r', encoding='UTF-8') as f:
        data = f.read()
    
    data_rooted = '<root>' + data + '</root>'
    parsed = Et.fromstring(data_rooted)
    pages = parsed.findall('page')

    # For last decompressed part
    mediawiki = parsed.find('mediawiki')
    if mediawiki is not None:
        m_pages = mediawiki.findall('page')
    else:
        m_pages = []
    if len(pages) == 0 and len(m_pages) != 0:
        pages = m_pages
    ###

    for i in pages:
        s = Et.tostring(i)
        temp_page_table_data = get_wikitables_from_string(s.decode('UTF-8'))
        for j in temp_page_table_data:
            wikitabledata = {
                'PageName': (i.find('title')).text,
                'PageId': (i.find('id')).text,
                'TableId': j[0],
                'WikitableData': j[1]}
            wikitabledata_list.append(wikitabledata)
    
    return wikitabledata_list


# For last decompressed part (add mediawiki tag then parse pages)
def prepend_file(file, prepended_text='<mediawiki>\n'):
    """
    Prepend file (with '<mediawiki>\n' by default)

    :param file: path as string
    :param prepended_text: string
    :return:
    """

    with open(file, mode='r', encoding='UTF-8') as f:
        original = f.read()
    with open(file, mode='w', encoding='UTF-8') as g:
        g.write(prepended_text + original)


def parse_wikitables_from_file(file):
    """
    Parse all raw wikitables from file

    :param file: path as string
    :return: list of parsed wikitables (each element is a dict)
    """

    raw_wikitables = extract_wikitables_from_file(file)
    parsed = []

    for i in raw_wikitables:
        parsed.append(wikitableparser.wikitable_parser(i['WikitableData'], i['PageName'], i['TableId']))

    return parsed
