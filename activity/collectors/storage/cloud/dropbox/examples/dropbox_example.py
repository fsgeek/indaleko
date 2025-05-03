"""
Example of using the Dropbox storage activity collector and recorder.

This example demonstrates how to use the Dropbox storage activity
collector and recorder to monitor and store file system activities.

Project Indaleko
Copyright (C) 2024-2025 Tony Mason

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
"""

import argparse
import logging
import os
import sys
import time

if os.environ.get("INDALEKO_ROOT") is None:
    current_path = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(current_path, "Indaleko.py")):
        current_path = os.path.dirname(current_path)
    os.environ["INDALEKO_ROOT"] = current_path
    sys.path.append(current_path)

# pylint: disable=wrong-import-position
from activity.collectors.storage.data_models.storage_activity_data_model import (
    StorageActivityType,
)
from activity.collectors.storage.cloud.dropbox.dropbox_collector import (
    DropboxStorageActivityCollector,
)
from activity.recorders.storage.dropbox.dropbox_recorder import (
    DropboxStorageActivityRecorder,
)

# pylint: enable=wrong-import-position


def main():
    """Main function for the Dropbox storage activity example."""
    parser = argparse.ArgumentParser(description="Dropbox Storage Activity Example")
    parser.add_argument(
        "--duration",
        type=int,
        default=300,
        help="Duration to monitor in seconds",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=60,
        help="How often to poll for changes (seconds)",
    )
    parser.add_argument(
        "--filter-types",
        type=str,
        default="",
        help="Comma-separated list of activity types to include",
    )
    parser.add_argument(
        "--shared-only",
        action="store_true",
        help="Only show activities for shared files",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("DropboxExample")

    # Parse activity types to filter
    activity_types = []
    if args.filter_types:
        type_names = [t.strip().upper() for t in args.filter_types.split(",")]
        for type_name in type_names:
            try:
                activity_types.append(StorageActivityType[type_name])
            except KeyError:
                logger.warning(f"Unknown activity type: {type_name}")

    # Create collector
    logger.info("Creating Dropbox collector")
    collector = DropboxStorageActivityCollector(
        monitor_interval=args.poll_interval,
        auto_start=False,
        debug=args.debug,
    )

    # Create recorder
    logger.info("Creating Dropbox recorder")
    recorder = DropboxStorageActivityRecorder(collector=collector, debug=args.debug)

    try:
        # Start monitoring
        logger.info(f"Starting monitoring for {args.duration} seconds")
        collector.start_monitoring()

        # Display progress
        start_time = time.time()
        end_time = start_time + args.duration

        while time.time() < end_time:
            # Get current activity count
            activities = collector.get_activities()
            activity_count = len(activities)

            # Print status update
            elapsed = time.time() - start_time
            remaining = args.duration - elapsed
            logger.info(
                f"Collected {activity_count} activities in {elapsed:.1f} seconds. {remaining:.1f} seconds remaining.",
            )

            # Sleep for a bit
            time.sleep(min(30, args.poll_interval))

        # Get final activities
        logger.info("Collecting final activities")
        activities = collector.get_activities()

        # Filter by activity type if specified
        if activity_types:
            logger.info(f"Filtering activities to types: {activity_types}")
            activities = [a for a in activities if a.activity_type in activity_types]

        # Filter by shared status if requested
        if args.shared_only:
            logger.info("Filtering to only show shared file activities")
            activities = [a for a in activities if getattr(a, "shared_folder_id", None) is not None]

        # Display activity summary
        logger.info(f"Total activities collected: {len(activities)}")

        # Group by activity type
        by_type = {}
        for activity in activities:
            activity_type = activity.activity_type
            if activity_type not in by_type:
                by_type[activity_type] = 0
            by_type[activity_type] += 1

        logger.info("Activities by type:")
        for activity_type, count in sorted(
            by_type.items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            logger.info(f"  {activity_type}: {count}")

        # Group by item type
        by_item_type = {}
        for activity in activities:
            item_type = activity.item_type
            if item_type not in by_item_type:
                by_item_type[item_type] = 0
            by_item_type[item_type] += 1

        logger.info("Activities by item type:")
        for item_type, count in sorted(
            by_item_type.items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            logger.info(f"  {item_type}: {count}")

        # Count shared vs non-shared
        shared_count = len(
            [a for a in activities if getattr(a, "shared_folder_id", None) is not None],
        )
        logger.info(
            f"Shared file activities: {shared_count} ({shared_count/len(activities)*100:.1f}% if len(activities) > 0 else 0)%)",
        )

        # Store activities
        logger.info("Storing activities in database")
        activity_ids = recorder.store_activities(activities)
        logger.info(f"Stored {len(activity_ids)} activities")

        # Get statistics from recorder
        logger.info("Getting activity statistics from database")
        stats = recorder.get_dropbox_specific_statistics()

        logger.info("Database statistics:")
        for key, value in stats.items():
            # Skip complex values for cleaner output
            if isinstance(value, dict) and len(value) > 5:
                logger.info(f"  {key}: {len(value)} items")
            else:
                logger.info(f"  {key}: {value}")

    except KeyboardInterrupt:
        logger.info("Monitoring interrupted by user")
    except Exception as e:
        logger.exception(f"Error during monitoring: {e}")
    finally:
        # Stop monitoring
        logger.info("Stopping monitoring")
        recorder.stop_monitoring()

    logger.info("Example complete")


if __name__ == "__main__":
    main()
