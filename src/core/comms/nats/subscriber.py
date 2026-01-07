# subscriber.py
import json
from typing import Callable, Any, Dict
from .qos_manager import QoSLevel

class NatsSubscriber:
    def __init__(self, client):
        """
        Subscriber wrapper for NATS.
        :param client: An already connected NATS client (from client.py).
        """
        self.client = client

    async def subscribe(
        self,
        subject: str,
        callback: Callable[[Dict[str, Any]], Any],
        qos: QoSLevel = QoSLevel.AT_MOST_ONCE,
        durable: str = None,
        stream: str = None,
    ):
        """
        Subscribe to a subject with QoS semantics.
        :param subject: NATS subject to subscribe.
        :param callback: Coroutine to call with decoded message.
        :param qos: QoS level.
        :param durable: Durable consumer name (for QoS >= 1).
        :param stream: JetStream stream (for QoS >= 1).
        """

        async def _on_message(msg):
            payload = json.loads(msg.data.decode("utf-8"))
            await callback(payload)

        if qos == QoSLevel.AT_MOST_ONCE:
            # vanilla subscription
            await self.client.subscribe(subject, cb=_on_message)

        elif qos in (QoSLevel.AT_LEAST_ONCE, QoSLevel.EXACTLY_ONCE):
            if not stream or not durable:
                raise ValueError("Stream + durable required for QoS >= 1")

            # JetStream consumer
            await self.client.js_subscribe(
                stream=stream,
                subject=subject,
                durable=durable,
                cb=_on_message,
                manual_ack=True,
            )
