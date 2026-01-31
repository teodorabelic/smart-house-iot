import threading
import time
from queue import Queue, Empty
from typing import Any, Dict, List
from .client import MqttClient

class BatchSender:
    """
    Daemon nit koja šalje merenja u batch-evima.
    Senzorski thread-ovi samo rade queue.put(event) -> minimalno zaključavanje.
    """

    def __init__(self, mqtt_client: MqttClient, qos: int, max_batch_size: int = 20, flush_interval_sec: float = 2.0):
        self.q = Queue()
        self.mqtt = mqtt_client
        self.qos = qos
        self.max_batch_size = max_batch_size
        self.flush_interval_sec = flush_interval_sec
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()

    def join(self, timeout: float = 2.0):
        self._thread.join(timeout=timeout)

    def enqueue(self, item: Dict[str, Any]):
        topic = item.get("_topic", "")
        if "/actuators/" in topic:
            return  # ignoriši aktuatore
        self.q.put(item)

    def _flush(self, batch: List[Dict[str, Any]]):
        # publish jedan po jedan, ali batching je u tome što šalje daemon nit i šalje grupisano
        for evt in batch:
            topic = evt.pop("_topic")
            self.mqtt.publish_json(topic, evt, qos=self.qos, retain=False)

    def _run(self):
        batch: List[Dict[str, Any]] = []
        batch_start = None

        while not self._stop.is_set():
            try:
                item = self.q.get(timeout=0.2)
                if batch_start is None:
                    batch_start = time.time()
                batch.append(item)

                if len(batch) >= self.max_batch_size:
                    self._flush(batch)
                    batch.clear()
                    batch_start = None

            except Empty:
                if batch and batch_start is not None and (time.time() - batch_start) >= self.flush_interval_sec:
                    self._flush(batch)
                    batch.clear()
                    batch_start = None

        if batch:
            self._flush(batch)
