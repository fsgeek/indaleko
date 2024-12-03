'''
This module handles data ingestion into Indaleko from the Linux local data
indexer.

Indaleko Linux Local Ingester
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
import datetime
import logging
import os
import json
import jsonlines
import sys
import uuid

from icecream import ic

if os.environ.get('INDALEKO_ROOT') is None:
    current_path = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(current_path, 'Indaleko.py')):
        current_path = os.path.dirname(current_path)
    os.environ['INDALEKO_ROOT'] = current_path
    sys.path.append(current_path)


# pylint: disable=wrong-import-position
from storage.recorders.base import IndalekoStorageRecorder
from storage.collectors.local.linux.collector import IndalekoLinuxLocalIndexer
from platforms.linux.machine_config import IndalekoLinuxMachineConfig
from platforms.unix import UnixFileAttributes
import utils.misc.directory_management
import utils.misc.file_name_management
import utils.misc.data_management
from utils.i_logging import IndalekoLogging
from IndalekoObject import IndalekoObject
from IndalekoRelationshipContains import IndalekoRelationshipContains
from IndalekoRelationshipContained import IndalekoRelationshipContainedBy
# pylint: enable=wrong-import-position


class IndalekoLinuxLocalIngester(IndalekoStorageRecorder):
    '''
    This class handles ingestion of metadata gathered from
    the local Linux file system.
    '''

    linux_local_ingester_uuid = '14ab60a0-3a5a-456f-8400-07c47a274f4b'
    linux_local_ingester_service = {
        'service_name' : 'Linux Local Ingester',
        'service_description' : 'This service ingests captured index info from the local filesystems of a Linux machine.',
        'service_version' : '1.0',
        'service_type' : 'Ingester',
        'service_identifier' : linux_local_ingester_uuid,
    }

    linux_platform = IndalekoLinuxLocalIndexer.linux_platform
    linux_local_ingester = 'local_fs_ingester'

    def __init__(self: IndalekoStorageRecorder, **kwargs: dict) -> None:
        if 'input_file' not in kwargs:
            raise ValueError('input_file must be specified')
        if 'machine_config' not in kwargs:
            raise ValueError('machine_config must be specified')
        self.machine_config = kwargs['machine_config']
        if 'machine_id' not in kwargs:
            kwargs['machine_id'] = self.machine_config.machine_id
        else:
            kwargs['machine_id'] = self.machine_config.machine_id
            if kwargs['machine_id'] != self.machine_config.machine_id:
                logging.warning('Warning: machine ID of indexer file ' +\
                      f'({kwargs["machine"]}) does not match machine ID of ingester ' +\
                        f'({self.machine_config.machine_id}.)')
        if 'timestamp' not in kwargs:
            kwargs['timestamp'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if 'platform' not in kwargs:
            kwargs['platform'] = IndalekoLinuxLocalIngester.linux_platform
        if 'ingester' not in kwargs:
            kwargs['ingester'] = IndalekoLinuxLocalIngester.linux_local_ingester
        if 'input_file' not in kwargs:
            kwargs['input_file'] = None
        for key, value in self.linux_local_ingester_service.items():
            if key not in kwargs:
                kwargs[key] = value
        super().__init__(**kwargs)
        self.input_file = kwargs['input_file']
        if 'output_file' not in kwargs:
            self.output_file = self.generate_file_name()
        else:
            self.output_file = kwargs['output_file']
        self.indexer_data = []
        self.source = {
            'Identifier' : self.linux_local_ingester_uuid,
            'Version' : '1.0'
        }

    def find_indexer_files(self) -> list:
        '''
        Find the indexer files in the data directory.
        '''
        if self.data_dir is None:
            raise ValueError('data_dir must be specified')
        return [x for x in super().find_indexer_files(self.data_dir)
                if IndalekoLinuxLocalIndexer.linux_platform in x and
                IndalekoLinuxLocalIndexer.linux_local_indexer_name in x]

    def load_indexer_data_from_file(self : 'IndalekoLinuxLocalIngester') -> None:
        '''This function loads the indexer data from the file.'''
        if self.input_file is None:
            raise ValueError('input_file must be specified')
        if self.input_file.endswith('.jsonl'):
            with jsonlines.open(self.input_file) as reader:
                for entry in reader:
                    self.indexer_data.append(entry)
        elif self.input_file.endswith('.json'):
            with open(self.input_file, 'r', encoding='utf-8-sig') as file:
                self.indexer_data = json.load(file)
        else:
            raise ValueError(f'Input file {self.input_file} is an unknown type')
        if not isinstance(self.indexer_data, list):
            raise ValueError('indexer_data is not a list')

    def normalize_index_data(self, data : dict) -> IndalekoObject:
        '''
        Given some metadata, this will create a record that can be inserted into the
        Object collection.
        '''
        if data is None:
            raise ValueError('Data cannot be None')
        if not isinstance(data, dict):
            raise ValueError('Data must be a dictionary')
        if 'ObjectIdentifier' in data:
            oid = data['ObjectIdentifier']
        else:
            oid = str(uuid.uuid4())
        timestamps = []
        if 'st_birthtime' in data:
            timestamps.append({
                'Label' : IndalekoObject.CREATION_TIMESTAMP,
                'Value' : datetime.datetime.fromtimestamp(data['st_birthtime'],
                                                          datetime.timezone.utc).isoformat(),
                'Description' : 'Created',
            })
        if 'st_mtime' in data:
            timestamps.append({
                'Label' : IndalekoObject.MODIFICATION_TIMESTAMP,
                'Value' : datetime.datetime.fromtimestamp(data['st_mtime'],
                                                          datetime.timezone.utc).isoformat(),
                'Description' : 'Modified',
            })
        if 'st_atime' in data:
            timestamps.append({
                'Label' : IndalekoObject.ACCESS_TIMESTAMP,
                'Value' : datetime.datetime.fromtimestamp(data['st_atime'],
                                                          datetime.timezone.utc).isoformat(),
                'Description' : 'Accessed',
            })
        if 'st_ctime' in data:
            timestamps.append({
                'Label' : IndalekoObject.CHANGE_TIMESTAMP,
                'Value' : datetime.datetime.fromtimestamp(data['st_ctime'],
                                                          datetime.timezone.utc).isoformat(),
                'Description' : 'Changed',
            })
        kwargs = {
            'source' : self.source,
            'raw_data' : utils.misc.data_management.encode_binary_data(bytes(json.dumps(data).encode('utf-8'))),
            'URI' : data['URI'],
            'ObjectIdentifier' : oid,
            'Timestamps' : timestamps,
            'Size' : data['st_size'],
            'Attributes' : data,
            'Machine' : self.machine_config.machine_id,
        }
        if 'st_mode' in data:
            kwargs['PosixFileAttributes'] = UnixFileAttributes.map_file_attributes(data['st_mode'])
        if 'timestamp' not in kwargs:
            if isinstance(self.timestamp, str):
                kwargs['timestamp'] = datetime.datetime.fromisoformat(self.timestamp)
            else:
                kwargs['timestamp'] = self.timestamp
        return IndalekoObject(**kwargs)

    def ingest(self) -> None:
        '''
        This function ingests the indexer file and emits the data needed to
        upload to the database.
        '''
        self.load_indexer_data_from_file()
        dir_data = []
        file_data = []
        # Step 1: build the normalized data
        for item in self.indexer_data:
            self.input_count += 1
            try:
                obj = self.normalize_index_data(item)
            except OSError as e:
                logging.error('Error normalizing data: %s', e)
                logging.error('Data: %s', item)
                self.error_count += 1
                continue
            if 'S_IFDIR' in obj.args['UnixFileAttributes']:
                if 'Path' not in obj:
                    logging.warning('Directory object does not have a path: %s', obj.to_json())
                    self.error_count += 1
                    continue # skip
                dir_data.append(obj)
                self.dir_count += 1
            else:
                file_data.append(obj)
                self.file_count += 1
        # Step 2: build a table of paths to directory uuids
        dirmap = {}
        for item in dir_data:
            fqp = os.path.join(item['Path'], item['Name'])
            identifier = item.args['ObjectIdentifier']
            dirmap[fqp] = identifier
        # now, let's build a list of the edges, using our map.
        dir_edges = []
        source = {
            'Identifier' : self.linux_local_ingester_uuid,
            'Version' : '1.0',
        }
        for item in dir_data + file_data:
            parent = item['Path']
            if parent not in dirmap:
                continue
            parent_id = dirmap[parent]
            dir_edge = IndalekoRelationshipContains(
                relationship = \
                    IndalekoRelationshipContains.DIRECTORY_CONTAINS_RELATIONSHIP_UUID_STR,
                object1 = {
                    'collection' : Indaleko.Indaleko_Object_Collection,
                    'object' : parent_id,
                },
                object2 = {
                    'collection' : Indaleko.Indaleko_Object_Collection,
                    'object' : item.args['ObjectIdentifier'],
                },
                source = source
            )
            dir_edges.append(dir_edge)
            self.edge_count += 1
            dir_edge = IndalekoRelationshipContainedBy(
                relationship = \
                    IndalekoRelationshipContainedBy.CONTAINED_BY_DIRECTORY_RELATIONSHIP_UUID_STR,
                object1 = {
                    'collection' : Indaleko.Indaleko_Object_Collection,
                    'object' : item.args['ObjectIdentifier'],
                },
                object2 = {
                    'collection' : Indaleko.Indaleko_Object_Collection,
                    'object' : parent_id,
                },
                source = source
            )
            dir_edges.append(dir_edge)
            self.edge_count += 1
        # Save the data to the ingester output file
        ic(self.output_file)
        self.write_data_to_file(dir_data + file_data, self.output_file)
        kwargs = {
            'machine' : self.machine_id,
            'platform' : self.platform,
            'service' : 'local_ingest',
            'collection' : Indaleko.Indaleko_Relationship_Collection,
            'timestamp' : self.timestamp,
            'output_dir' : self.data_dir,
        }
        if hasattr(self, 'storage_description') and self.storage_description is not None:
            kwargs['storage'] = self.args['storage_description']
        edge_file = self.generate_output_file_name(**kwargs)
        self.write_data_to_file(dir_edges, edge_file)
        ic(edge_file)

    @staticmethod
    def generate_log_file_name(**kwargs) -> str:
        if 'service' not in kwargs:
            kwargs['service'] = 'ingest'
        target_dir = None
        if 'target_dir' in kwargs:
            target_dir = kwargs['target_dir']
            del kwargs['target_dir']
        if 'suffix' not in kwargs:
            kwargs['suffix'] = 'log'
        file_name = utils.misc.file_name_management.generate_file_name(**kwargs)
        if target_dir is not None:
            file_name = os.path.join(target_dir, file_name)
        return file_name


def main():
    '''
    This is the main handler for the Indaleko Linux Local Ingest
    service.
    '''
    logging_levels = IndalekoLogging.get_logging_levels()

    # step 1: find the index file I'm going to use
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument('--configdir',
                            help=f'Path to the config directory (default is {utils.misc.directory_management.indaleko_default_config_dir})',
                            default=utils.misc.directory_management.indaleko_default_config_dir)
    pre_parser.add_argument('--logdir',
                            help=f'Path to the log directory (default is {utils.misc.directory_management.indaleko_default_log_dir})',
                            default=utils.misc.directory_management.indaleko_default_log_dir)
    pre_parser.add_argument('--loglevel',
                        choices=logging_levels,
                        default=logging.DEBUG,
                        help='Logging level to use.')
    pre_parser.add_argument('--datadir',
                            help=f'Path to the data directory (default is {utils.misc.directory_management.indaleko_default_data_dir})',
                            type=str,
                            default=utils.misc.directory_management.indaleko_default_data_dir)
    pre_args, _ = pre_parser.parse_known_args()
    indexer_files = IndalekoLinuxLocalIndexer.find_indexer_files(pre_args.datadir)
    pre_parser.add_argument('--input',
                            choices=indexer_files,
                            default=indexer_files[-1],
                            help='Linux Local Indexer file to ingest.')
    pre_args, _ = pre_parser.parse_known_args()
    indexer_file_metadata = utils.misc.file_name_management.extract_keys_from_file_name(pre_args.input)
    timestamp = indexer_file_metadata.get('timestamp',
                                          datetime.datetime.now(datetime.timezone.utc).isoformat())
    log_file_name = IndalekoLinuxLocalIngester.generate_log_file_name(
        platform=indexer_file_metadata['platform'],
        ingester=IndalekoLinuxLocalIngester.linux_local_ingester,
        machine_id = indexer_file_metadata['machine'],
        target_dir=pre_args.logdir,
        timestamp=timestamp,
        suffix='log')
    if os.path.exists(log_file_name):
        os.remove(log_file_name)
    logging.basicConfig(
        filename=log_file_name,
        level=pre_args.loglevel,
        format='%(asctime)s - %(levelname)s - %(message)s',
        force=True
    )
    logging.critical('Start logging')
    if not os.path.exists(log_file_name):
        print(f'Failed to create log file {log_file_name} - logging disabled.')
    parser = argparse.ArgumentParser(parents=[pre_parser])
    parser.add_argument('--reset', action='store_true', help='Reset the service collection.')
    args = parser.parse_args()
    metadata = IndalekoLinuxLocalIndexer.extract_metadata_from_indexer_file_name(args.input)
    machine_id = metadata['machine']
    if 'platform' in metadata:
        indexer_platform = metadata['platform']
        if indexer_platform != IndalekoLinuxLocalIngester.linux_platform:
            print('Warning: platform of indexer file ' +\
                  f'({indexer_platform}) name does not match platform of ingester ' +\
                    f'({IndalekoLinuxLocalIngester.linux_platform}.)')
    storage = None
    if 'storage' in metadata:
        storage = metadata['storage']
    file_prefix = IndalekoStorageRecorder.default_file_prefix
    if 'file_prefix' in metadata:
        file_prefix = metadata['file_prefix']
    file_suffix = IndalekoStorageRecorder.default_file_suffix
    if 'file_suffix' in metadata:
        file_suffix = metadata['file_suffix']
    input_file = os.path.join(args.datadir, args.input)
    machine_id_hex = uuid.UUID(machine_id).hex
    config_files = [x for x in IndalekoLinuxMachineConfig.find_config_files(args.configdir) if machine_id_hex in x]
    if len(config_files) == 0:
        raise ValueError(f'No configuration files found for machine {machine_id}')
    config_file = os.path.join(args.configdir, config_files[-1])
    machine_config = IndalekoLinuxMachineConfig.load_config_from_file(config_file=config_file)
    ingest_args = {
        'machine_config' : machine_config,
        'machine_id' : machine_id,
        'timestamp' : timestamp,
        'platform' : IndalekoLinuxLocalIndexer.linux_platform,
        'ingester' : IndalekoLinuxLocalIngester.linux_local_ingester,
        'file_prefix' : file_prefix,
        'file_suffix' : file_suffix,
        'data_dir' : args.datadir,
        'input_file' : input_file,
    }
    if storage is not None:
        ingest_args['storage_description'] = storage
    ingester = IndalekoLinuxLocalIngester(**ingest_args)
    logging.info('Ingesting %s ' , args.input)
    ingester.ingest()
    for count_type, count_value in ingester.get_counts().items():
        logging.info('%s: %d', count_type, count_value)
    logging.info('Done')


if __name__ == '__main__':
    main()
