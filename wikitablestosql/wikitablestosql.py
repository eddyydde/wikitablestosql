
import os
import sys
import argparse
import multiprocessing
import threading
import functools
import time

from . import wikitableprocessing
from . import multistreamfilehandling
from . import tosql


# Progress bar code
def progress_animator(indicators, symbol_loop=('--', "\\", '|', '/'), suffix='', 
                      task='Processing files ... ', interval=0.1):
    """Progress indicator"""
           
    state = 0
    message = ''
    while not indicators['end']:
        length = len(message)
        state = (state + 1) % len(symbol_loop)
        time.sleep(interval)
        prefix = task + '[' + str(indicators['done']) + '/' + str(indicators['total']) + '] '
        message = prefix + symbol_loop[state] + suffix
        print(length * ' ', end='\r')
        print(message, end='\r')
    print('')

    if indicators['terminate']:
        print('Process Terminated')
        sys.exit(0)
    else:
        print('DONE!')


def associate_to_index(data_directory):
    """
    Associate each multistream file to its corresponding index.

    :param data_directory: path as string
    :return: list of associations where each association is of the form:
            [multistream_filename, index_filename]
    """

    parsed_filenames = [n.split('-') for n in os.listdir(data_directory) if
                        os.path.isfile(os.path.join(data_directory, n)) and
                        os.path.splitext(os.path.join(data_directory, n))[1] == '.bz2']

    to_process = []
    for p in parsed_filenames:
        if p[-2].split('.')[-1] == 'xml':
            for j in parsed_filenames:
                if p[-1] == j[-1] and j[-2].split('.')[-1] == 'txt':
                    # form: (data, index)
                    to_process.append(('-'.join(p), '-'.join(j)))
    return to_process


# Full part processing
def process_part(part_file, parts_directory, last_part_name, parts_decompression_directory, database):
    """Process one part of one multistream file into an sql database."""

    # decompress part file
    decompressed_part_file = multistreamfilehandling.decompress_part(parts_directory, part_file,
                                                                     parts_decompression_directory)
    if part_file == last_part_name:
        wikitableprocessing.prepend_file(os.path.join(parts_decompression_directory, decompressed_part_file))
    # extract wikitables and parse to lists
    parsed = wikitableprocessing.parse_wikitables_from_file(os.path.join(parts_decompression_directory,
                                                                         decompressed_part_file))
    # process into sql database
    tosql.process_many_wikitables_into_sql_database(parsed, database)


def prompt_continue(name):
    """Prompt for required user intervention."""

    print(name + " already exists. " + "Data will be added to " + name + " if you continue. ")
    prompt = "Do you want to continue? (y/n): "
    inp = input(prompt).strip().lower()
    if inp not in ['y', 'n']:
        print(inp + " is not a valid option, please try again...")
        return prompt_continue(name)
    return inp == 'y'


def cleanup(files_dict):
    """
    Removal of intermediate files.
    """

    if os.path.exists(files_dict['decompressed_index_filename']):
        os.remove(files_dict['decompressed_index_filename'])
    for f in os.listdir(files_dict['parts_directory']):
        os.remove(os.path.join(files_dict['parts_directory'], f))
    os.rmdir(files_dict['parts_directory'])
    for f in os.listdir(files_dict['parts_decompression_directory']):
        os.remove(os.path.join(files_dict['parts_decompression_directory'], f))
    os.rmdir(files_dict['parts_decompression_directory'])


def get_database_filename(data_directory):
    """
    Determine database filename.

    :param data_directory: path as string
    :return: filename as string
    """

    base = os.path.commonprefix(os.listdir(data_directory))
    return base + '.db'


def main():
    remove_intermediate_files = True

    parser = argparse.ArgumentParser(description='Extract wikitables from multistream wikipedia database dump '
                                                 'and process them into a sqlite3 database.')
    parser.add_argument('path', metavar='folder', type=str, nargs=1,
                        help='wikipedia multistream folder path')
    args = parser.parse_args()
    wiki_path = args.path[0]
    
    indicators = {}
    indicators['done'] = 0
    indicators['end'] = False
    indicators['terminate'] = False

    data_index_pairs = associate_to_index(wiki_path)
    indicators['total'] = len(data_index_pairs)
    database_filename = get_database_filename(wiki_path)

    progress = threading.Thread(target=progress_animator, args=(indicators,))
    
    # Check if database exists
    if os.path.exists(database_filename):
        indicators['terminate'] = not prompt_continue(database_filename)
        if indicators['terminate']:
            print("Process Terminated.")
            sys.exit(0)
    else:
        tosql.sql_table_creation(database_filename)
        
    print("Database filename: ", database_filename)
        
    progress.start()
    
    for i in data_index_pairs:
        files_info = multistreamfilehandling.prepare_parts_using_index(wiki_path, i[0], i[1], indicators['done'])
        process_part_directory_set = \
            functools.partial(process_part, parts_directory=files_info['parts_directory'],
                              last_part_name=files_info['last_part_name'],
                              parts_decompression_directory=files_info['parts_decompression_directory'],
                              database=database_filename)
        parts = os.listdir(files_info['parts_directory'])
        
        # main multiprocessing loop (by batch of 100 pages)
        with multiprocessing.Pool() as pool:
            pool.map(process_part_directory_set, parts)

        if remove_intermediate_files:
            cleanup(files_info)

        indicators['done'] += 1
    indicators['end'] = True


if __name__ == '__main__':
    main()
