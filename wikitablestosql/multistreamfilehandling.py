
import os
import csv
import bz2


def prepare_parts_using_index(data_directory, file, index, done=0):
    """
    Prepare parts by cutting multistream file according to index.
    Prepare decompression directory.

    :param data_directory: path as string
    :param file: filename as string
    :param index: index filename as string
    :param done: for naming purposes, as int
    :return: process information as dict
    """

    # decompress index
    decompressed_index_filename = os.path.splitext(index)[0]
    with bz2.open(os.path.join(data_directory, index), mode='rb') as indexf:
        decompressed_index = indexf.read()
        with open(decompressed_index_filename, mode='wb') as decomp_index_file:
            decomp_index_file.write(decompressed_index)

    # parse index
    byte_offsets = []
    with open(decompressed_index_filename, encoding='UTF-8') as csv_file:
        csv_index = csv.reader(csv_file, delimiter=':')
        for row in csv_index:
            if len(byte_offsets) == 0:
                byte_offsets.append(int(row[0]))
            else:
                if int(row[0]) != byte_offsets[-1]:
                    byte_offsets.append(int(row[0]))

    parts_directory = str(done) + 'parts' + '_' + file

    # cut file according to index
    if parts_directory not in os.listdir():
        os.mkdir(parts_directory)
    with open(os.path.join(data_directory, file), mode='rb') as f:
        for i in range(len(byte_offsets)-1):
            with open(os.path.join(parts_directory, 'part' + '_' + str(i+1) + '_' + file), mode='wb') as pf:
                f.seek(byte_offsets[i])
                data_part = f.read(byte_offsets[i+1] - byte_offsets[i])
                pf.write(data_part)
        f.seek(byte_offsets[-1])
        last_part_name = 'part' + '_' + str(len(byte_offsets)) + '_' + file
        with open(os.path.join(parts_directory, last_part_name), mode='wb') as lpf:
            lpf.write(f.read())

    # prepare for decompression
    decompression_directory = 'decompressed' + '_' + parts_directory
    if decompression_directory not in os.listdir():
        os.mkdir(decompression_directory)

    return {'decompressed_index_filename': decompressed_index_filename, 'parts_directory': parts_directory,
            'last_part_name': last_part_name, 'parts_decompression_directory': decompression_directory}


def decompress_part(parts_directory, part_file, parts_decompression_directory):
    """
    Decompress one part file.

    :param parts_directory: path as string
    :param part_file: filename as string
    :param parts_decompression_directory: path as string
    :return: filename as string
    """
    decompressed_filename = 'decompressed' + '_' + os.path.splitext(part_file)[0]
    with bz2.open(os.path.join(parts_directory, part_file), mode='rb') as f:
        with open(os.path.join(parts_decompression_directory, decompressed_filename), mode='wb') as g:
            g.write(f.read())
    return decompressed_filename
