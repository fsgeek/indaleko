'''
This module handles metadata collection from local Linux file systems.

Indaleko Linux Local Collector
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
import uuid
import os
import sys

if os.environ.get('INDALEKO_ROOT') is None:
    current_path = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(current_path, 'Indaleko.py')):
        current_path = os.path.dirname(current_path)
    os.environ['INDALEKO_ROOT'] = current_path
    sys.path.append(current_path)

# pylint: disable=wrong-import-position
# from Indaleko import Indaleko
from storage.collectors.base import BaseStorageCollector
from platforms.linux.machine_config import IndalekoLinuxMachineConfig
from utils.i_logging import IndalekoLogging
from db.service_manager import IndalekoServiceManager
import utils.misc.directory_management
import utils.misc.file_name_management
# pylint: enable=wrong-import-position



class IndalekoLinuxLocalCollector(BaseStorageCollector):
    '''
    This is the class that collects metadata from Linux local file systems.
    '''
    linux_platform = 'Linux'
    linux_local_collector_name = 'fs_collector'

    indaleko_linux_local_collector_uuid = 'bef019bf-b762-4297-bbe2-bf79a65027ae'
    indaleko_linux_local_collector_service_name = 'Linux Local Collector'
    indaleko_linux_local_collector_service_description = 'This service collects local filesystem metadata of a Linux machine.'
    indaleko_linux_local_collector_service_version = '1.0'
    indaleko_linux_local_collector_service_type = IndalekoServiceManager.service_type_storage_collector

    indaleko_linux_local_collector_service ={
        'service_name' : indaleko_linux_local_collector_service_name,
        'service_description' : indaleko_linux_local_collector_service_description,
        'service_version' : indaleko_linux_local_collector_service_version,
        'service_type' : indaleko_linux_local_collector_service_type,
        'service_identifier' : indaleko_linux_local_collector_uuid,
    }

    def __init__(self, **kwargs):
        assert 'machine_config' in kwargs, 'machine_config must be specified'
        self.machine_config = kwargs['machine_config']
        if 'machine_id' not in kwargs:
            kwargs['machine_id'] = self.machine_config.machine_id
        self.offline = False
        if 'offline' in kwargs:
            self.offline = kwargs['offline']
            del self.offline
        super().__init__(**kwargs,
                         platform=IndalekoLinuxLocalCollector.linux_platform,
                         collector_name=IndalekoLinuxLocalCollector.linux_local_collector_name,
                         **IndalekoLinuxLocalCollector.indaleko_linux_local_collector_service
        )

    @staticmethod
    def generate_linux_collector_file_name(**kwargs) -> str:
        '''Generate a file name for the Linux local collector'''
        if 'platform' not in kwargs:
            kwargs['platform'] = IndalekoLinuxLocalCollector.linux_platform
        if 'collector_name' not in kwargs:
            kwargs['collector_name'] = IndalekoLinuxLocalCollector.linux_local_collector_name
        assert 'machine_id' in kwargs, 'machine_id must be specified'
        return BaseStorageCollector.generate_collector_file_name(**kwargs)


def main():
    '''This is the main handler for the Indaleko Linux Local Collector
    service.'''
    logging_levels = IndalekoLogging.get_logging_levels()
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    # Step 1: find the machine configuration file & set up logging
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument('--configdir',
                            help='Path to the config directory',
                            default=utils.misc.directory_management.indaleko_default_config_dir)
    pre_parser.add_argument('--logdir', '-l',
                            help='Path to the log directory',
                            default=utils.misc.directory_management.indaleko_default_log_dir)
    pre_parser.add_argument('--loglevel',
                            type=int,
                            default=logging.DEBUG,
                            choices=logging_levels,
                            help='Logging level to use (lower number = more logging)')
    pre_args, _ = pre_parser.parse_known_args()
    config_files = IndalekoLinuxMachineConfig.find_config_files(pre_args.configdir)
    default_config_file = IndalekoLinuxMachineConfig.get_most_recent_config_file(pre_args.configdir)
    config_file_metadata = utils.misc.file_name_management.extract_keys_from_file_name(default_config_file)
    config_platform = IndalekoLinuxLocalCollector.linux_platform
    if 'platform' in config_file_metadata:
        config_platform = config_file_metadata['platform']
    log_file_name = IndalekoLinuxLocalCollector.generate_linux_collector_file_name(
        platform=config_platform,
        collector_name=IndalekoLinuxLocalCollector.linux_local_collector_name,
        machine_id = config_file_metadata['machine'],
        target_dir=pre_args.logdir,
        timestamp=timestamp,
        suffix='log')
    logging.basicConfig(
        filename=log_file_name,
        level=pre_args.loglevel,
        format='%(asctime)s - %(levelname)s - %(message)s',
        force=True
    )
    # Step 2: figure out the default config file
    pre_parser = argparse.ArgumentParser(add_help=False, parents=[pre_parser])
    pre_parser.add_argument('--config', choices=config_files, default=default_config_file)
    pre_parser.add_argument('--path', help='Path to the directory from which to collect metadata', type=str,
                            default=os.path.expanduser('~'))
    pre_parser.add_argument('--datadir', '-d',
                            help='Path to the data directory',
                            default=utils.misc.directory_management.indaleko_default_data_dir)
    pre_parser.add_argument('--offline',
                        help='Do not require live database access',
                        default=False,
                        action='store_true')
    pre_args, _ = pre_parser.parse_known_args()

    # Step 3: now we can load the machine configuration
    machine_config = IndalekoLinuxMachineConfig.load_config_from_file(config_file=pre_args.config, offline=pre_args.offline)

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    collector = IndalekoLinuxLocalCollector(
        machine_config=machine_config,
        timestamp=timestamp,
        path=pre_args.path,
        offline=pre_args.offline
    )
    output_file = IndalekoLinuxLocalCollector.generate_linux_collector_file_name(
        platform=config_platform,
        collector_name=IndalekoLinuxLocalCollector.linux_local_collector_name,
        machine_id = config_file_metadata['machine'],
        target_dir=pre_args.datadir,
        suffix='jsonl')
    parser= argparse.ArgumentParser(parents=[pre_parser])
    parser.add_argument('--output', '-o',
                        help='name to assign to output file',
                        default=output_file)
    args = parser.parse_args()
    output_file = args.output
    logging.info('Collecting metadata from %s ' , pre_args.path)
    logging.info('Output file %s ' , output_file)
    data = collector.collect()
    collector.write_data_to_file(data, output_file)
    for count_type, count_value in collector.get_counts().items():
        logging.info('%s: %d', count_type, count_value)
    logging.info('Done')

if __name__ == '__main__':
    main()
