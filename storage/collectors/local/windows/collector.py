'''
This module handles gathering metadata from Windows local file systems.

Indaleko Windows Local Collector
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
from data_models import IndalekoSourceIdentifierDataModel
from db import IndalekoServiceManager
from utils.i_logging import IndalekoLogging
import utils.misc.file_name_management
import utils.misc.directory_management
from storage.collectors.base import BaseStorageCollector
from platforms.windows.machine_config import IndalekoWindowsMachineConfig
from perf.perf_collector import IndalekoPerformanceDataCollector
from perf.perf_recorder import IndalekoPerformanceDataRecorder
# pylint: enable=wrong-import-position


class IndalekoWindowsLocalCollector(BaseStorageCollector):
    '''
    This is the class that collects metadata from Windows local file systems.
    '''
    windows_platform = 'Windows'
    windows_local_collector_name = 'fs_collector'

    indaleko_windows_local_collector_uuid = '0793b4d5-e549-4cb6-8177-020a738b66b7'
    indaleko_windows_local_collector_service_name = 'Windows Local collector'
    indaleko_windows_local_collector_service_description = 'This service collects metadata from the local filesystems of a Windows machine.'
    indaleko_windows_local_collector_service_version = '1.0'
    indaleko_windows_local_collector_service_type = IndalekoServiceManager.service_type_storage_collector

    indaleko_windows_local_collector_service ={
        'service_name' : indaleko_windows_local_collector_service_name,
        'service_description' : indaleko_windows_local_collector_service_description,
        'service_version' : indaleko_windows_local_collector_service_version,
        'service_type' : indaleko_windows_local_collector_service_type,
        'service_identifier' : indaleko_windows_local_collector_uuid,
    }

    @staticmethod
    def windows_to_posix(filename):
        """
        Convert a Win32 filename to a POSIX-compliant one.
        """
        # Define a mapping of Win32 reserved characters to POSIX-friendly characters
        win32_to_posix = {
            '<': '_lt_', '>': '_gt_', ':': '_cln_', '"': '_qt_',
            '/': '_sl_', '\\': '_bsl_', '|': '_bar_', '?': '_qm_', '*': '_ast_'
        }
        for win32_char, posix_char in win32_to_posix.items():
            filename = filename.replace(win32_char, posix_char)
        return filename

    @staticmethod
    def posix_to_windows(filename):
        """
        Convert a POSIX-compliant filename to a Win32 one.
        """
        # Define a mapping of POSIX-friendly characters back to Win32 reserved characters
        posix_to_win32 = {
            '_lt_': '<', '_gt_': '>', '_cln_': ':', '_qt_': '"',
            '_sl_': '/', '_bsl_': '\\', '_bar_': '|', '_qm_': '?', '_ast_': '*'
        }
        for posix_char, win32_char in posix_to_win32.items():
            filename = filename.replace(posix_char, win32_char)
        return filename


    def __init__(self, **kwargs):
        assert 'machine_config' in kwargs, 'machine_config must be specified'
        self.machine_config = kwargs['machine_config']
        if 'machine_id' not in kwargs:
            kwargs['machine_id'] = self.machine_config.machine_id
        for key, value in self.indaleko_windows_local_collector_service.items():
            if key not in kwargs:
                kwargs[key] = value
        if 'platform' not in kwargs:
            kwargs['platform'] = IndalekoWindowsLocalCollector.windows_platform
        if 'collector_name' not in kwargs:
            kwargs['collector_name'] = IndalekoWindowsLocalCollector.windows_local_collector_name
        super().__init__(**kwargs)

    def generate_windows_collector_file_name(self, **kwargs) -> str:
        if 'platform' not in kwargs:
            kwargs['platform'] = IndalekoWindowsLocalCollector.windows_platform
        if 'collector_name' not in kwargs:
            kwargs['collector_name'] = IndalekoWindowsLocalCollector.windows_local_collector_name
        if 'machine_id' not in kwargs:
            kwargs['machine_id'] = uuid.UUID(self.machine_config.machine_id).hex
        return BaseStorageCollector.generate_collector_file_name(**kwargs)

    def convert_windows_path_to_guid_uri(self, path : str) -> str:
        '''This method handles converting a Windows path to a volume GUID based URI.'''
        drive = os.path.splitdrive(path)[0][0].upper()
        uri = '\\\\?\\' + drive + ':' # default format for lettered drives without GUIDs
        mapped_guid = self.machine_config.map_drive_letter_to_volume_guid(drive)
        if mapped_guid is not None:
            uri = '\\\\?\\Volume{' + mapped_guid + '}\\'
        else:
            print(f'Ugh, cannot map {drive} to a GUID')
            uri = '\\\\?\\' + drive + ':'
        return uri


    def build_stat_dict(self, name: str, root : str, last_uri = None, last_drive = None) -> tuple:
        '''
        Given a file name and a root directory, this will return a dict
        constructed from the file system metadata ("stat") for that file.
        Note: on error this returns an empty dictionary.  If the full path to
        the file does not exist, this returns None.
        '''
        file_path = os.path.join(root, name)
        if not os.path.exists(file_path):
            if name in os.listdir(root):
                if os.path.lexists(file_path):
                    logging.warning('File %s is an invalid link', file_path)
                else:
                    logging.warning('File %s exists in directory %s but not accessible', name, root)
            else:
                logging.warning('File %s does not exist in directory %s', file_path, root)
            return None
        if last_uri is None:
            last_uri = file_path
        lstat_data = None
        try:
            lstat_data = os.lstat(file_path)
            stat_data = os.stat(file_path)
        except Exception as e: # pylint: disable=broad-except
            # at least for now, we log and skip errors
            logging.warning('Unable to stat %s : %s', file_path, e)
            self.error_count += 1
            if lstat_data is not None:
                self.bad_symlink_count += 1
            return None

        if stat_data.st_ino != lstat_data.st_ino:
            logging.info('File %s is a symlink, collecting symlink metadata', file_path)
            self.good_symlink_count += 1
            stat_data = lstat_data
        stat_dict = {key : getattr(stat_data, key) \
                     for key in dir(stat_data) if key.startswith('st_')}
        stat_dict['Name'] = name
        stat_dict['Path'] = root
        if last_drive != os.path.splitdrive(root)[0][0].upper():
            last_drive = os.path.splitdrive(root)[0][0].upper()
            last_uri = self.convert_windows_path_to_guid_uri(root)
            assert last_uri.startswith('\\\\?\\Volume{'), \
                f'last_uri {last_uri} does not start with \\\\?\\Volume{{'
        stat_dict['URI'] = os.path.join(last_uri, os.path.splitdrive(root)[1], name)
        stat_dict['Collector'] = self.service_identifier
        assert last_uri.startswith('\\\\?\\Volume{')
        if last_uri.startswith('\\\\?\\Volume{'):
            stat_dict['Volume GUID'] = last_uri[11:-2]
        stat_dict['ObjectIdentifier'] = str(uuid.uuid4())
        return (stat_dict, last_uri, last_drive)


    def collect(self) -> list:
        data = []
        last_drive = None
        last_uri = None
        for root, dirs, files in os.walk(self.path):
            for name in dirs + files:
                entry = self.build_stat_dict(name, root, last_uri, last_drive)
                if entry is None:
                    self.not_found_count += 1
                    continue
                if len(entry) == 0:
                    self.error_count += 1
                    continue
                if name in dirs:
                    self.dir_count += 1
                else:
                    self.file_count += 1
                data.append(entry[0])
                last_uri = entry[1]
                last_drive = entry[2]
        return data



def main():
    '''This is the main handler for the Indaleko Windows Local Collector
    service.'''
    logging_levels = IndalekoLogging.get_logging_levels()

    # Step 1: find the machine configuration file
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument('--configdir',
                            help='Path to the config directory',
                            default=utils.misc.directory_management.indaleko_default_config_dir)
    pre_args, _ = pre_parser.parse_known_args()
    config_files = IndalekoWindowsMachineConfig.find_config_files(pre_args.configdir)
    default_config_file = IndalekoWindowsMachineConfig.get_most_recent_config_file(pre_args.configdir)
    # Step 2: figure out the default config file
    pre_parser = argparse.ArgumentParser(add_help=False, parents=[pre_parser])
    pre_parser.add_argument('--config', choices=config_files, default=default_config_file)
    pre_parser.add_argument('--path', help='Path to the directory to scan', type=str,
                            default=os.path.expanduser('~'))
    pre_args, _ = pre_parser.parse_known_args()

    # Step 3: now we can compute the machine config and drive GUID
    machine_config = IndalekoWindowsMachineConfig.load_config_from_file(config_file=pre_args.config)

    drive = os.path.splitdrive(pre_args.path)[0][0].upper()
    drive_guid = machine_config.map_drive_letter_to_volume_guid(drive)
    if drive_guid is None:
        drive_guid = uuid.uuid4().hex
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    collector = IndalekoWindowsLocalCollector(machine_config=machine_config,
                                          timestamp=timestamp)
    output_file = collector.generate_windows_collector_file_name(storage_description=drive_guid)
    parser= argparse.ArgumentParser(parents=[pre_parser])
    parser.add_argument('--datadir', '-d',
                        help='Path to the data directory',
                        default=utils.misc.directory_management.indaleko_default_data_dir)
    parser.add_argument('--output', '-o',
                        help='name to assign to output directory',
                        default=output_file)
    parser.add_argument('--logdir', '-l',
                        help='Path to the log directory',
                        default=utils.misc.directory_management.indaleko_default_log_dir)
    parser.add_argument('--loglevel',
                        type=int,
                        default=logging.DEBUG,
                        choices=logging_levels,
                        help='Logging level to use (lower number = more logging)')
    parser.add_argument('--performance_file',
                        default=False,
                        action='store_true',
                        help='Record performance data to a file')
    parser.add_argument('--performance_db',
                        default=False,
                        action='store_true',
                        help='Record performance data to the database')
    args = parser.parse_args()
    collector = IndalekoWindowsLocalCollector(timestamp=timestamp,
                                          path=args.path,
                                          machine_config=machine_config,
                                          storage_description=drive_guid)
    output_file = args.output
    log_file_name = collector.generate_windows_collector_file_name(target_dir=args.logdir, suffix='log')
    logging.basicConfig(filename=os.path.join(log_file_name),
                                level=args.loglevel,
                                format='%(asctime)s - %(levelname)s - %(message)s',
                                force=True)
    logging.info('Indexing %s ' , pre_args.path)
    logging.info('Output file %s ' , output_file)
    perf_file_name = os.path.join(
        args.datadir,
        IndalekoPerformanceDataRecorder().generate_perf_file_name(
            platform=collector.platform,
            service=collector.collector_name,
            machine=uuid.UUID(machine_config.machine_id)
        )
    )
    def extract_counters(**kwargs):
        ic(kwargs)
        collector = kwargs.get('collector')
        if collector:
            return ic(collector.get_counts())
        else:
            return {}
    def collect(collector):
        data = collector.collect()
        collector.write_data_to_file(data, output_file)
    perf_data = IndalekoPerformanceDataCollector.measure_performance(
        collect,
        source=IndalekoSourceIdentifierDataModel(
            Identifier=collector.service_identifier,
            Version = collector.service_version,
            Description=collector.service_description),
        description=collector.service_description,
        MachineIdentifier=uuid.UUID(machine_config.machine_id),
        process_results_func=extract_counters,
        input_file_name=None,
        output_file_name=output_file,
        collector=collector
    )
    if args.performance_db or args.performance_file:
        perf_recorder = IndalekoPerformanceDataRecorder()
        if args.performance_file:
            perf_recorder.add_data_to_file(perf_file_name, perf_data)
            ic('Performance data written to ', perf_file_name)
        if args.performance_db:
            perf_recorder.add_data_to_db(perf_data)
            ic('Performance data written to the database')
    counts = collector.get_counts()
    for count_type, count_value in counts.items():
        logging.info('%s: %d', count_type, count_value)
    logging.info('Done')

if __name__ == '__main__':
    main()
