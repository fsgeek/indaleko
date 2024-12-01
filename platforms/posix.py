'''
Project Indaleko
Copyright (C) 2024 Tony Mason

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
import argparse

class IndalekoPosix:
    """This class defines the Posix-specific attributes of a file."""

    FILE_ATTRIBUTES = {
        'S_IFSOCK' : 0o140000, # socket
        'S_IFLNK' : 0o120000, # symbolic link
        'S_IFREG' : 0o100000, # regular file
        'S_IFBLK' : 0o060000, # block device
        'S_IFDIR' : 0o040000, # directory
        'S_IFCHR' : 0o020000, # character device
        'S_IFIFO' : 0o010000, # FIFO
    }

    @staticmethod
    def map_file_attributes(attributes : int):
        """This function maps the file attributes to the string representation."""
        file_attributes = []
        for attr in IndalekoPosix.FILE_ATTRIBUTES.items():
            if attributes & IndalekoPosix.FILE_ATTRIBUTES[attr[0]] == \
                IndalekoPosix.FILE_ATTRIBUTES[attr[0]]:
                file_attributes.append(attr[0])
        return ' | '.join(file_attributes)

def main():
    """Test code for IndalekoPosix class."""
    parser = argparse.ArgumentParser(description='Indaleko Posix test logic')
    parser.add_argument('--attr',
                        '-a',
                        default = 0xFF,
                        type = int,
                        help = 'file attribute bits to test')
    args = parser.parse_args()

    if args.attr == 0xFF:
        print('Testing all attributes')
        for attributes in IndalekoPosix.FILE_ATTRIBUTES.items():
            print(f'{attributes} = {IndalekoPosix.FILE_ATTRIBUTES[attributes[0]]}')
            print(f'{attributes} = \
                  {IndalekoPosix.map_file_attributes(IndalekoPosix.FILE_ATTRIBUTES[attributes[0]])}')
    else:
        print(f'{args.attr} = {IndalekoPosix.map_file_attributes(args.attr)}')

if __name__ == '__main__':
    main()
