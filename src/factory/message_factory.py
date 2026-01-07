# services/message_factory.py

import uuid
from datetime import datetime
from config import ConfigLoader
from data.models import telemetry, discovery, heartbeat


class MessageFactory:
    """
    Factory to create full message payloads (header + body)
    using schema models and YAML-defined parameters.
    """

    schema_map = {
        "telemetry": telemetry.TelemetryModel,
        "discovery": discovery.DiscoveryModel,
        "heartbeat": heartbeat.HeartbeatModel,
    }

    @classmethod
    def create(cls, msg_type: str):
        """
        Create a full message payload from the given msg_type.
        Loads configuration from message.yaml and validates body using the model schema.
        """
        # Load YAML config
        config = ConfigLoader().get("message.yaml")[msg_type]

        # Extract parts
        header_cfg = config.get("header", {})
        body_cfg = config.get("body", {})

        # Validate message type
        if msg_type not in cls.schema_map:
            raise ValueError(f"Unknown message type: {msg_type}")

        # Build body from schema
        SchemaModel = cls.schema_map[msg_type]
        body = SchemaModel(**body_cfg).model_dump()

        # Build header (ensure runtime values are unique/fresh)
        header = {
            "msg_type": header_cfg.get("msg_type", msg_type),
            "msg_id": str(uuid.uuid4()),
            "qos": header_cfg.get("qos", "AT_MOST_ONCE"),
            "stream": header_cfg.get("stream", None),
            "timestamp": datetime.utcnow().isoformat(),
            "source": header_cfg.get("source", "Air-Unit"),
        }

        return {"header": header, "body": body}
