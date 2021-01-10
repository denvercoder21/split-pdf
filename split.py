#!/usr/bin/env python3

import argparse
import os.path
import qrtools
import shortuuid
import shutil
import tempfile

from datetime import datetime
from pdf2image import convert_from_path
from pdfrw import PdfReader, PdfWriter


QR_DATA = "foobar"


parser = argparse.ArgumentParser(
    allow_abbrev=True,
    description="This program splits a PDF file into multiple files using a QR code page as a delimiter")

parser.add_argument(
    '-i',
    '--input',
    metavar="",
    default=None,
    type=str,
    required=True,
    help="the input file to split")

args = parser.parse_args()
file = args.input


def split_document(input_doc):
    print("splitting " + str(input_doc))
    # check if our file exists
    if not os.path.isfile(input_doc):
        print("file not found")
        return

    # find the qr code page separators and get the total number of pages
    info = find_separator_indices_and_number_total_pages(input_doc)

    # nothing to do if no qr code found or the document has one page or
    # less
    if not info[0] or info[1] <= 1:
        rename_file(input_doc)  # set proper file name
        return

    # create tuples of page ranges so we know where to cut
    page_ranges = create_page_ranges(info[0], info[1])

    # perform the actual cut; save the split files and remove the original
    do_split(input_doc, page_ranges)


def find_separator_indices_and_number_total_pages(pdf):
    separators = list()

    pages = convert_from_path(pdf, 72)
    for i, page in enumerate(pages, start=1):
        if (is_separator_page(page)):
            separators.append(i)

    return (separators, len(pages))


def is_separator_page(page):
    temp_file = tempfile.NamedTemporaryFile(suffix=".png")
    page.save(temp_file.name)

    qr = qrtools.QR()
    qr.decode(temp_file)

    return qr.data == QR_DATA


def create_page_ranges(cuts, num_total_pages):
    pages = list(range(num_total_pages))
    slices = [
        (lhs + 1, rhs)
        for lhs, rhs in zip([0, *cuts], [*cuts, len(pages) + 1])
    ]

    return slices


def do_split(input_doc, ranges):
    pages = PdfReader(input_doc).pages
    for i, part in enumerate(ranges, start=1):
        outdata = PdfWriter(new_document_name(i))
        for pagenum in range(*part):
            outdata.addpage(pages[pagenum - 1])
        outdata.write()

    os.remove(input_doc)


def new_document_name(i):
    today = datetime.today().strftime('%Y-%m-%d')
    id = shortuuid.ShortUUID().random(length=5)
    return f"/home/user/dev/watch/{today}-document-{i:02d}-{id}.pdf"


def rename_file(file):
    dir = os.path.dirname(file) + "/"
    source = dir + os.path.basename(file)
    dest = dir + new_document_name(1)
    os.rename(source, dest)


def move_files_to_outgoing_folder():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    for fname in os.listdir(current_dir):
        if fname.lower().endswith('.pdf'):
            shutil.move(
                os.path.join(
                    current_dir,
                    fname),
                '/home/user/scans-out/')


split_document(file)
move_files_to_outgoing_folder()
