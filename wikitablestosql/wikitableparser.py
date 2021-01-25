
import copy


def check_in(position, info_pos_line_pairs):
    """
    Check if position corresponds to the starting position of a pair in info_pos_line_pairs
    (return pair if found, empty list otherwise)
    :param position: list
    :param info_pos_line_pairs: list of lists
    :return: list
    """

    # pos_pair form: [info, [in_line_position_1, line_number_1], [in_line_position_2, line_number_2]]
    for i in info_pos_line_pairs:
        if position[0] == i[1][0] and position[1] == i[1][1]:
            return i

    return []


def tag_type_check(tag_buffer, tag_list):
    """
    Check if tag buffer is in or is potentially in tag list

    :param tag_buffer: string
    :param tag_list: list of strings
    :return: indicator as list
    """

    temp = []
    for i in tag_list:
        if i == tag_buffer:
            return [tag_buffer]
        elif i.startswith(tag_buffer):
            temp = ['']

    return temp


def curly_braces_matching(opening_stack_element, closing_stack_element, matches=None):
    """
    Greedily match curly braces by groups of 2 or 3 (priority to groups of 3 when they can be matched)

    :param opening_stack_element: list of lists
    :param closing_stack_element: list of lists
    :param matches: list of lists
    :return: list of lists
    """

    if matches is None:
        matches = []

    if len(closing_stack_element) < 2 or len(opening_stack_element) < 2:
        return [opening_stack_element, closing_stack_element, matches]
    elif len(closing_stack_element) == 2 or len(opening_stack_element) == 2:
        start = opening_stack_element[-2][1:3]
        end = closing_stack_element[1][1:3]

        closing_stack_element = closing_stack_element[2:]
        opening_stack_element = opening_stack_element[:-2]

        matches.append(['template', start, end])

        return curly_braces_matching(opening_stack_element, closing_stack_element, matches)
    else:
        start = opening_stack_element[-3][1:3]
        end = closing_stack_element[2][1:3]

        closing_stack_element = closing_stack_element[3:]
        opening_stack_element = opening_stack_element[:-3]

        matches.append(['tplarg', start, end])

        return curly_braces_matching(opening_stack_element, closing_stack_element, matches)


def square_brackets_matching(opening_stack_element, closing_stack_element, matches=None):
    """
    Match brackets by groups of 2

    :param opening_stack_element: list of lists
    :param closing_stack_element: list of lists
    :param matches: list of lists
    :return: list of lists
    """

    if matches is None:
        matches = []

    if len(closing_stack_element) < 2 or len(opening_stack_element) < 2:
        return [opening_stack_element, closing_stack_element, matches]
    else:
        start = opening_stack_element[-2][1:3]
        end = closing_stack_element[1][1:3]

        closing_stack_element = closing_stack_element[2:]
        opening_stack_element = opening_stack_element[:-2]

        matches.append(['link', start, end])

        return square_brackets_matching(opening_stack_element, closing_stack_element, matches)


def consume_stacks(last_raw_stack, open_stack):
    """
    Consume stacks according to type of brackets

    :param last_raw_stack: list of lists
    :param open_stack: list of lists
    :return: list of lists
    """

    pairs = []

    if last_raw_stack[0][0] == 'closingsquare':
        while len(open_stack) > 0 and open_stack[-1][0][0] == 'openingsquare':
            [opening_stack_element, last_raw_stack, pairs] = square_brackets_matching(open_stack[-1],
                                                                                      last_raw_stack, pairs)
            open_stack.pop()
            if len(opening_stack_element) >= 2:
                open_stack.append(opening_stack_element)
            if len(last_raw_stack) < 2:
                break
    else:
        while len(open_stack) > 0 and open_stack[-1][0][0] == 'openingcurly':
            [opening_stack_element, last_raw_stack, pairs] = curly_braces_matching(open_stack[-1],
                                                                                   last_raw_stack, pairs)
            open_stack.pop()
            if len(opening_stack_element) >= 2:
                open_stack.append(opening_stack_element)
            if len(last_raw_stack) < 2:
                break
    last_raw_stack.clear()

    return pairs


def brackets_proc(i, element, line_number, last_raw_stack, open_stack, last, pairs_list):
    """
    Subroutine for first_pass function. Processes curly and square brackets.

    :param i:
    :param element:
    :param line_number:
    :param last_raw_stack:
    :param open_stack:
    :param last:
    :param pairs_list:
    :return:
    """

    if element != last:
        if len(last_raw_stack) >= 2:
            if last == '[' or last == '{':
                open_stack.append(copy.deepcopy(last_raw_stack))
            else:
                pairs_list.extend(consume_stacks(last_raw_stack, open_stack))
        last_raw_stack.clear()

    if element == '{':
        last_raw_stack.append(['openingcurly', i, line_number])
    elif element == '}':
        last_raw_stack.append(['closingcurly', i, line_number])
    elif element == '[':
        last_raw_stack.append(['openingsquare', i, line_number])
    elif element == ']':
        last_raw_stack.append(['closingsquare', i, line_number])


# First pass parsing
def first_pass(text):
    """
    Find links, comments, escaped (or non wiki-formatted text), templates and template arguments

    :param text:
    :return: list containing 2 lists
                            (first one gives the locations of links, templates and template arguments,
                            second one gives the locations of comments, escaped text and non wiki-formatted text)
    """

    # For templates and template arguments
    template_other_list = []  # list of [begin, end (inclusive), line number]

    last_open_stack = []
    last_raw_stack = []
    last = ''

    # For escape and comments
    escape_comment_pos_list = []  # list of [begin, end (inclusive), line number]

    temp_begin = ''
    tag_buffer = ''
    escape_type = ''

    tag_mode = False
    comment_tag_mode = False
    escape_mode = False
    comment_mode = False

    if text == '':
        return text

    line_number = None
    i = None

    for line_number, line in enumerate(text):
        for i, element in enumerate(line):
            if comment_mode:
                if comment_tag_mode:
                    if element == '>' and tag_buffer == '-':
                        comment_tag_mode = False
                        comment_mode = False
                        tag_buffer = ''
                        escape_comment_pos_list.append([temp_begin, [i, line_number]])
                        temp_begin = ''
                    elif element == '>' and tag_buffer != '-':
                        tag_buffer = ''
                        comment_tag_mode = False
                    elif element == '-':
                        tag_buffer = '-'
                    else:
                        comment_tag_mode = False
                        tag_buffer = ''
                else:
                    if element == '-':
                        comment_tag_mode = True
            elif escape_mode:
                if tag_mode:
                    tag_buffer += element
                    # Check against closing escape tags
                    tag_var = tag_type_check(tag_buffer, ['/' + escape_type + '>'])
                    if tag_var and tag_var[0]:
                        escape_mode = False
                        tag_mode = False
                        escape_type = ''
                        tag_buffer = ''
                        escape_comment_pos_list.append([temp_begin, [i, line_number]])
                        temp_begin = ''
                    elif not tag_var:
                        tag_mode = False
                        tag_buffer = ''
                else:
                    if element == '<':
                        tag_mode = True
            else:
                if tag_mode:
                    tag_buffer += element
                    # Check against escape and comment tags
                    tag_var = tag_type_check(tag_buffer, ['nowiki>', 'pre>', '!--'])
                    if tag_var and tag_var[0]:
                        if tag_var[0] == '!--':
                            comment_mode = True
                        else:
                            escape_mode = True
                            escape_type = tag_buffer[:-1]
                        tag_buffer = ''
                        tag_mode = False
                    elif not tag_var:
                        if element == '<':
                            tag_buffer = ''
                            temp_begin = [i, line_number]
                        else:
                            tag_mode = False
                            tag_buffer = ''
                            temp_begin = ''
                            brackets_proc(i, element, line_number, last_raw_stack, last_open_stack, last,
                                          template_other_list)
                else:
                    if element == '<':
                        tag_mode = True
                        temp_begin = [i, line_number]
                    brackets_proc(i, element, line_number, last_raw_stack, last_open_stack, last, template_other_list)
            last = element

    element = ''
    brackets_proc(i, element, line_number, last_raw_stack, last_open_stack, last, template_other_list)

    return [template_other_list, escape_comment_pos_list]


def table_proc(feed, feed_index, line_number, buffers, table_state, wikitabledata):
    """
    Subroutine for wikitable_parser function

    :param feed:
    :param feed_index:
    :param line_number:
    :param buffers:
    :param table_state:
    :param wikitabledata:
    :return:
    """

    if not buffers['templateindex']:
        buffers['templateindex'] = check_in([feed_index, line_number], buffers['templatesotherpospairs'])
    if not buffers['escapecommentindex']:
        buffers['escapecommentindex'] = check_in([feed_index, line_number], buffers['escapecommentpospairs'])

    if table_state['cellmode']:
        if buffers['templateindex'] or buffers['escapecommentindex']:
            if table_state['pipemode'] and table_state['attributerecorded']:
                table_state['pipemode'] = False
                buffers['tempunit'] += '|'
                buffers['tempunit'] += feed
            elif table_state['pipemode'] and not table_state['attributerecorded']:
                table_state['pipemode'] = False
                table_state['attributerecorded'] = True
                if buffers['tempdata']['rowattribute'] != '':
                    buffers['tempdata']['fullattribute'] = copy.deepcopy(
                        buffers['tempdata']['rowattribute']) + ' ' + copy.deepcopy(buffers['tempunit'])
                else:
                    buffers['tempdata']['fullattribute'] = copy.deepcopy(buffers['tempunit'])
                buffers['tempunit'] = feed
            elif table_state['newlinemode']:
                buffers['tempunit'] += '\n' + feed
            elif table_state['interogmode']:
                table_state['interogmode'] = False
                buffers['tempunit'] += '!'
                buffers['tempunit'] += feed
            else:
                buffers['tempunit'] += feed

            if buffers['templateindex'][0] == 'link' or buffers['templateindex'][0] == 'template':
                table_state['attributerecorded'] = True
                if buffers['tempdata']['fullattribute'] == '':
                    buffers['tempdata']['fullattribute'] = buffers['tempdata']['rowattribute']
        else:
            if table_state['newlinemode']:
                if feed == '|':
                    if table_state['pipemode'] and table_state['attributerecorded']:
                        table_state['pipemode'] = False
                        table_state['attributerecorded'] = False
                        buffers['tempunit'] += '|'
                    elif table_state['pipemode'] and not table_state['attributerecorded']:
                        table_state['pipemode'] = False
                        if buffers['tempdata']['rowattribute'] != '':
                            buffers['tempdata']['fullattribute'] = copy.deepcopy(
                                buffers['tempdata']['rowattribute']) + ' ' + copy.deepcopy(buffers['tempunit'])
                        else:
                            buffers['tempdata']['fullattribute'] = copy.deepcopy(buffers['tempunit'])
                        buffers['tempunit'] = ''
                    # *** STORAGE *** store cell and reset
                    buffers['tempdata']['celldata'] = copy.deepcopy(buffers['tempunit'])
                    if table_state['captionmode']:
                        wikitabledata['caption']['name'] = copy.deepcopy(buffers['tempdata']['celldata'])
                        wikitabledata['caption']['attribute'] = copy.deepcopy(buffers['tempdata']['fullattribute'])
                        table_state['captionmode'] = False
                    else:
                        buffers['temprow'].append(copy.deepcopy(buffers['tempdata']))
                    buffers['tempdata']['fullattribute'] = ''
                    buffers['tempdata']['isheader'] = False
                    buffers['tempdata']['celldata'] = ''
                    buffers['tempunit'] = ''
                    table_state['attributerecorded'] = False

                    table_state['cellmode'] = False
                    table_state['headerrowmode'] = False
                    table_state['startmode'] = True
                elif feed == '!':
                    if table_state['pipemode'] and table_state['attributerecorded']:
                        table_state['pipemode'] = False
                        table_state['attributerecorded'] = False
                        buffers['tempunit'] += '|'
                    elif table_state['pipemode'] and not table_state['attributerecorded']:
                        table_state['pipemode'] = False
                        if buffers['tempdata']['rowattribute'] != '':
                            buffers['tempdata']['fullattribute'] = copy.deepcopy(
                                buffers['tempdata']['rowattribute']) + ' ' + copy.deepcopy(buffers['tempunit'])
                        else:
                            buffers['tempdata']['fullattribute'] = copy.deepcopy(buffers['tempunit'])
                        buffers['tempunit'] = ''
                    # *** STORAGE *** store cell and reset
                    buffers['tempdata']['celldata'] = copy.deepcopy(buffers['tempunit'])
                    if table_state['captionmode']:
                        wikitabledata['caption']['name'] = copy.deepcopy(buffers['tempdata']['celldata'])
                        wikitabledata['caption']['attribute'] = copy.deepcopy(buffers['tempdata']['fullattribute'])
                        table_state['captionmode'] = False
                    else:
                        buffers['temprow'].append(copy.deepcopy(buffers['tempdata']))
                    buffers['tempdata']['fullattribute'] = ''
                    buffers['tempdata']['isheader'] = False
                    buffers['tempdata']['celldata'] = ''
                    buffers['tempunit'] = ''
                    table_state['attributerecorded'] = False

                    table_state['headerrowmode'] = True
                    table_state['newlinemode'] = False
                    table_state['cellmode'] = True
                    buffers['tempdata']['isheader'] = True
                else:
                    if table_state['interogmode']:
                        buffers['tempunit'] += '!'
                        buffers['tempunit'] += '\n' + feed
                        table_state['interogmode'] = False
                    elif table_state['pipemode'] and table_state['attributerecorded']:
                        buffers['tempunit'] += '|'
                        buffers['tempunit'] += '\n' + feed
                        table_state['pipemode'] = False
                    elif table_state['pipemode'] and not table_state['attributerecorded']:
                        if buffers['tempdata']['rowattribute'] != '':
                            buffers['tempdata']['fullattribute'] = copy.deepcopy(
                                buffers['tempdata']['rowattribute']) + ' ' + copy.deepcopy(buffers['tempunit'])
                        else:
                            buffers['tempdata']['fullattribute'] = copy.deepcopy(buffers['tempunit'])
                        buffers['tempunit'] = '\n' + feed
                        table_state['attributerecorded'] = True
                        table_state['pipemode'] = False
                    else:
                        buffers['tempunit'] += '\n' + feed

            elif feed == '[' and buffers['last'] == '[':
                buffers['tempunit'] += feed
                table_state['attributerecorded'] = True
                if buffers['tempdata']['fullattribute'] == '':
                    buffers['tempdata']['fullattribute'] = buffers['tempdata']['rowattribute']
            elif feed == '|':
                if table_state['pipemode']:
                    table_state['pipemode'] = False
                    if table_state['captionmode']:
                        buffers['tempdata']['celldata'] += '\n'
                    else:
                        buffers['tempdata']['celldata'] = copy.deepcopy(buffers['tempunit'])
                        buffers['temprow'].append(copy.deepcopy(buffers['tempdata']))
                        buffers['tempdata']['fullattribute'] = ''
                        buffers['tempdata']['isheader'] = False
                        buffers['tempdata']['celldata'] = ''
                        buffers['tempunit'] = ''
                else:
                    table_state['pipemode'] = True
            elif feed == '!':
                if table_state['headerrowmode'] and table_state['interogmode']:
                    # *** STORAGE ***
                    buffers['tempdata']['celldata'] = copy.deepcopy(buffers['tempunit'])
                    buffers['temprow'].append(copy.deepcopy(buffers['tempdata']))
                    buffers['tempdata']['fullattribute'] = ''
                    buffers['tempdata']['celldata'] = ''
                    buffers['tempunit'] = ''
                    table_state['interogmode'] = False
                elif table_state['headerrowmode'] and not table_state['interogmode']:
                    if table_state['pipemode'] and table_state['attributerecorded']:
                        buffers['tempunit'] += '|'
                        table_state['pipemode'] = False
                    elif table_state['pipemode'] and not table_state['attributerecorded']:
                        if buffers['tempdata']['rowattribute'] != '':
                            buffers['tempdata']['fullattribute'] = copy.deepcopy(
                                buffers['tempdata']['rowattribute']) + ' ' + copy.deepcopy(buffers['tempunit'])
                        else:
                            buffers['tempdata']['fullattribute'] = copy.deepcopy(buffers['tempunit'])
                        buffers['tempunit'] = ''
                        table_state['attributerecorded'] = True
                        table_state['pipemode'] = False
                    table_state['interogmode'] = True
                else:
                    if table_state['pipemode'] and table_state['attributerecorded']:
                        buffers['tempunit'] += '|'
                        buffers['tempunit'] += '!'
                        table_state['pipemode'] = False
                    elif table_state['pipemode'] and not table_state['attributerecorded']:
                        if buffers['tempdata']['rowattribute'] != '':
                            buffers['tempdata']['fullattribute'] = copy.deepcopy(
                                buffers['tempdata']['rowattribute']) + ' ' + copy.deepcopy(buffers['tempunit'])
                        else:
                            buffers['tempdata']['fullattribute'] = copy.deepcopy(buffers['tempunit'])
                        buffers['tempunit'] = '!'
                        table_state['attributerecorded'] = True
                        table_state['pipemode'] = False
                    else:
                        buffers['tempunit'] += '!'
            else:
                if table_state['interogmode']:
                    buffers['tempunit'] += '!'
                    buffers['tempunit'] += feed
                    table_state['interogmode'] = False
                elif table_state['pipemode'] and table_state['attributerecorded']:
                    buffers['tempunit'] += '|'
                    buffers['tempunit'] += feed
                    table_state['pipemode'] = False
                elif table_state['pipemode'] and not table_state['attributerecorded']:
                    if buffers['tempdata']['rowattribute'] != '':
                        buffers['tempdata']['fullattribute'] = copy.deepcopy(
                            buffers['tempdata']['rowattribute']) + ' ' + copy.deepcopy(buffers['tempunit'])
                    else:
                        buffers['tempdata']['fullattribute'] = copy.deepcopy(buffers['tempunit'])
                    buffers['tempunit'] = feed
                    table_state['attributerecorded'] = True
                    table_state['pipemode'] = False
                else:
                    buffers['tempunit'] += feed
    elif table_state['startmode']:
        if table_state['newlinemode']:
            # if feed is '|' dump tempdata and stay in startmode
            if feed == '|':
                buffers['temprow'].append(copy.deepcopy(buffers['tempdata']))
            # if feed is '!' dump tempdata, leave startmode and enter headerrowmode, header attribute and cellmode
            elif feed == '!':
                buffers['temprow'].append(copy.deepcopy(buffers['tempdata']))
                table_state['startmode'] = False
                table_state['headerrowmode'] = True
                table_state['cellmode'] = True
                buffers['tempdata']['isheader'] = True
            # else add feed to tempunit, leave startmode and enter cellmode
            else:
                buffers['tempunit'] += '\n' + feed
                table_state['startmode'] = False
                table_state['cellmode'] = True
        elif feed == '+':
            table_state['captionmode'] = True
            table_state['cellmode'] = True
            table_state['startmode'] = False
        elif feed == '-':
            if len(buffers['temprow']) != 0:
                wikitabledata['rows'].append(copy.deepcopy(buffers['temprow']))
                buffers['temprow'].clear()
            table_state['startmode'] = False
            table_state['newrowmode'] = True
        else:
            table_state['startmode'] = False
            table_state['cellmode'] = True
            if feed != ' ':
                buffers['tempunit'] += feed
    else:
        if table_state['newlinemode']:
            if table_state['newrowmode']:
                buffers['tempdata']['rowattribute'] = copy.deepcopy(buffers['tempunit'])
                buffers['tempunit'] = ''
                table_state['newrowmode'] = False

            if feed == '|':
                table_state['startmode'] = True
            elif feed == '!':
                table_state['headerrowmode'] = True
                buffers['tempdata']['isheader'] = True
                table_state['cellmode'] = True
            else:
                buffers['tempunit'] += '\n' + feed
        else:
            buffers['tempunit'] += feed

    if buffers['templateindex'] and [feed_index, line_number] == buffers['templateindex'][2]:
        buffers['templateindex'] = 0
    if buffers['escapecommentpospairs'] and [feed_index, line_number] == buffers['escapecommentindex'][2]:
        buffers['escapecommentindex'] = 0

    table_state['newlinemode'] = False


def wikitable_parser(raw_wikitable, page_name, table_count):
    """
    Wikitable parser

    :param raw_wikitable: string
    :param page_name: string
    :param table_count: int
    :return: dict
    """

    # Initialize buffers
    buffers = {}
    # table buffers
    buffers['tempunit'] = ''
    buffers['tempdata'] = {}
    buffers['tempdata']['isheader'] = False
    buffers['tempdata']['celldata'] = ''
    buffers['tempdata']['rowattribute'] = ''
    buffers['tempdata']['fullattribute'] = ''
    buffers['temprow'] = []

    # other buffers
    buffers['templatesotherpospairs'] = []
    buffers['escapecommentpospairs'] = []
    buffers['templateindex'] = []
    buffers['escapecommentindex'] = []
    buffers['last'] = ''
    buffers['problem'] = {}

    # Initialize tablestate
    tablestate = {}
    tablestate['problem'] = False
    tablestate['newlinemode'] = True
    tablestate['startmode'] = False
    tablestate['cellmode'] = False
    tablestate['pipemode'] = False
    tablestate['newrowmode'] = False
    tablestate['headerrowmode'] = False
    tablestate['interogmode'] = False
    tablestate['attributerecorded'] = False
    tablestate['captionmode'] = False

    # prepare wikitabledata
    wikitabledata = {'pagename': page_name, 'tablecount': table_count, 'tableattribute': '', 'caption': {}, 'rows': []}
    wikitabledata['caption']['name'] = ''
    wikitabledata['caption']['attribute'] = ''

    wikitabledata['tableattribute'] = raw_wikitable.splitlines()[0][2:]
    tablecontent = raw_wikitable.splitlines()[1:-1]
    [buffers['templatesotherpospairs'], buffers['escapecommentpospairs']] = first_pass(tablecontent)
    for linenumber, line in enumerate(tablecontent):
        tablestate['newlinemode'] = True
        tablestate['headerrowmode'] = False
        for i, feed in enumerate(line):
            table_proc(feed, i, linenumber, buffers, tablestate, wikitabledata)
            if tablestate['problem']:
                buffers['problem']['line-number'] = linenumber
                buffers['problem']['index'] = i
                buffers['problem']['raw'] = tablecontent
                break
        if tablestate['problem']:
            return [{'pagename': page_name, 'tablecount': table_count, 'problem': buffers['problem']}]

    if tablestate['pipemode'] and tablestate['attributerecorded']:
        buffers['tempunit'] += '|'
    elif tablestate['pipemode'] and not tablestate['attributerecorded']:
        if buffers['tempdata']['rowattribute'] == '':
            buffers['tempdata']['fullattribute'] = copy.deepcopy(buffers['tempunit'])
        else:
            buffers['tempdata']['fullattribute'] = copy.deepcopy(
                buffers['tempdata']['rowattribute']) + ' ' + copy.deepcopy(buffers['tempunit'])
        buffers['tempunit'] = ''

    # store cell
    buffers['tempdata']['celldata'] = copy.deepcopy(buffers['tempunit'])
    buffers['temprow'].append(copy.deepcopy(buffers['tempdata']))
    # add last row
    wikitabledata['rows'].append(copy.deepcopy(buffers['temprow']))

    return wikitabledata
