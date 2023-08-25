#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#
import threading
from queue import Empty, Queue

from airbyte_cdk.models import SyncMode
from airbyte_cdk.sources.concurrent.stream_partition import StreamPartition

_SENTINEL = ("SENTINEL", "SENTINEL")


class QueueConsumer:
    def __init__(self, name: str):
        self._name = name

    def consume_from_queue(self, queue: Queue[StreamPartition]):
        current_thread = threading.current_thread().ident
        print(f"consume from queue {self._name} from {current_thread}")
        cursor_field = None  # FIXME!
        records_and_streams = []
        while True:
            try:
                stream_partition = queue.get(timeout=2)
                if stream_partition == _SENTINEL:
                    print(f"found sentinel for {self._name} from {current_thread}")
                    return records_and_streams
                else:
                    print(f"partition_and_stream for {self._name}: {stream_partition} from {current_thread}")
                    for record in stream_partition.stream.read_records(
                        stream_slice=stream_partition.slice, sync_mode=SyncMode.full_refresh, cursor_field=cursor_field
                    ):
                        records_and_streams.append((record, stream_partition.stream))  # FIXME: I think this should include the partition...
                    print(f"{self._name} done reading partition {stream_partition} from {current_thread}")
            except Empty:
                print(f"queue {self._name} is empty from {current_thread}")
