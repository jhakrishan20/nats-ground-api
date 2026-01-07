# subjects_factory.py
from config import ConfigLoader


class SubjectFactory:
    """
    Factory to generate standardized subjects.

    Base form:
        {source}.{source_id}.{topic}.{subtopic}

    Publishing form (directed):
        {source}.{source_id}.{topic}.{subtopic}.{remote_client_id}

    Subscribing form (generic):
        {source}.{source_id}.{topic}.{subtopic}
    """

    def __init__(self):
        self.topics_map = ConfigLoader().get("topic.yaml")["Topics"]

    def create(
        self,
        source: str,
        source_id: str,
        topic: str,
        subtopic: str = None,
        *,
        mode: str = "sub",
        remote_client_id: str | None = None,
    ) -> str:
        """
        Create a subject string.

        Args:
            source: "uav" | "ground"
            source_id: local client id (can be "*")
            topic: logical topic (search, telemetry, etc.)
            subtopic: request | response | imu | etc.
            mode: "pub" or "sub"
            remote_client_id: required when mode="pub"

        Examples:
            SUB:
                ground.*.search.response.airunit-001
            PUB:
                ground.gcs-01.search.response.airunit-001
        """

        if topic not in self.topics_map:
            raise ValueError(f"Unknown topic: {topic}")

        if subtopic:
            if subtopic not in self.topics_map[topic]:
                raise ValueError(
                    f"Invalid subtopic '{subtopic}' for topic '{topic}'"
                )

        parts = [source, source_id, topic]
        if subtopic:
            parts.append(subtopic)

        # ---- publishing requires a target ----
        if mode == "pub":
            if not remote_client_id:
                raise ValueError(
                    "remote_client_id is required when mode='pub'"
                )
            parts.append(remote_client_id)

        return ".".join(parts)
