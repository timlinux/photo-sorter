"""Given a directory, find all the photos and refile them.

Photos will be filed in  folders in the scheme:

/yyyy/MM/dd

Any image with no exif tag will be ignored

"""

#!python

import sys
import os
import stat
import types
import fnmatch
import shutil
import hashlib
from pyexif import ExifEditor



# Next two functions from http://stackoverflow.com/a/13046184

def get_checksum(current_file_name, check_type='sha512', first_block=False):
    """Computes the hash for the given file. If first_block is True,
  only the first block of size size_block is hashed."""
    size_block = 1024 * 1024 # The first N bytes (1KB)

    d = {'sha1': hashlib.sha1, 'md5': hashlib.md5, 'sha512': hashlib.sha512}

    if (not d.has_key(check_type)):
        raise Exception("Unknown checksum method")

    file_size = os.stat(current_file_name)[stat.ST_SIZE]
    with file(current_file_name, 'rb') as f:
        key = d[check_type].__call__()
        while True:
            s = f.read(size_block)
            key.update(s)
            file_size -= size_block
            if (len(s) < size_block or first_block):
                break
    return key.hexdigest().upper()


def find_duplicates(files):
    """Find duplicates among a set of files.
    The implementation uses two types of hashes:
    - A small and fast one one the first block of the file (first 1KB),
    - and in case of collision a complete hash on the file. The complete hash
    is not computed twice.
    It flushes the files that seems to have the same content
    (according to the hash method) at the end.
    """

    print 'Analyzing', len(files), 'files'

    # this dictionary will receive small hashes
    d = {}
    # this dictionary will receive full hashes. It is filled
    # only in case of collision on the small hash (contains at least two
    # elements)
    duplicates = {}

    for f in files:

        # small hash to be fast
        check = get_checksum(f, first_block=True, check_type='sha1')

        if not d.has_key(check):
            # d[check] is a list of files that have the same small hash
            d[check] = [(f, None)]
        else:
            l = d[check]
            l.append((f, None))

            for index, (ff, checkfull) in enumerate(l):

                if checkfull is None:
                    # computes the full hash in case of collision
                    checkfull = get_checksum(ff, first_block=False)
                    l[index] = (ff, checkfull)

                # for each new full hash computed, check if their is
                # a collision in the duplicate dictionary.
                if not duplicates.has_key(checkfull):
                    duplicates[checkfull] = [ff]
                else:
                    duplicates[checkfull].append(ff)

            # prints the detected duplicates
            if len(duplicates) != 0:
                print
            print "The following files have the same sha512 hash"

            for h, lf in duplicates.items():
                if len(lf) == 1:
                    continue
            print 'Hash value', h
            for f in lf:
                print '\t', f.encode('unicode_escape') if \
                    type(f) is types.UnicodeType else f
    return duplicates


def __main__():
    in_dir = '/home/timlinux/Pictures'
    out_dir = '/home/timlinux/PhotosSorted/'

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    matches = []
    for root, dirnames, filenames in os.walk(in_dir):
        for filename in fnmatch.filter(filenames, '*.jpg'):
            matches.append(os.path.join(root, filename))
        for filename in fnmatch.filter(filenames, '*.jpeg'):
            matches.append(os.path.join(root, filename))
        for filename in fnmatch.filter(filenames, '*.JPG'):
            matches.append(os.path.join(root, filename))
        for filename in fnmatch.filter(filenames, '*.JPEG'):
            matches.append(os.path.join(root, filename))

            #for filename in fnmatch.filter(filenames, '*.png'):
            #    matches.append(os.path.join(root, filename))
            #for filename in fnmatch.filter(filenames, '*.PNG'):
            #    matches.append(os.path.join(root, filename))

    image_count = 0
    for filename in matches:
        image_count += 1
        editor = ExifEditor(filename)
        image_date = str(editor.getModificationDateTime())
        date_part, time_part = image_date.split(' ')
        year, month, day = date_part.split('-')
        hours, minutes, seconds = time_part.split(':')
        #print '%s : %s' % (image_date, filename)
        path = os.path.abspath(os.path.join(
            out_dir, year, month, day
        ))
        try:
            os.makedirs(path)
        except OSError:
            pass
        new_filename = '-'.join([
            year, month, day, hours, minutes, seconds, str(image_count)])
        new_filename += '.jpg'
        new_path = os.path.join(out_dir, path, new_filename)
        print 'mv %s %s' % (filename, new_path)
        shutil.move(filename, new_path)

    print '%s photos sorted' % image_count

    files = []
    for root, dirnames, filenames in os.walk(out_dir):
        for filename in fnmatch.filter(filenames, '*.jpg'):
            files.append(os.path.join(root, filename))

    duplicates = find_duplicates(files)
    for key, value in duplicates:
        # get rid of one filename from the list
        #  so at least one copy is not deleted
        value.pop()
        for filename in value:
            os.remove(filename)



