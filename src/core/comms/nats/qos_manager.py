from enum import Enum

class QoSLevel(str, Enum):
    AT_MOST_ONCE = "AT_MOST_ONCE"   # Fire-and-forget
    AT_LEAST_ONCE = "AT_LEAST_ONCE" # Guaranteed delivery with ack
    EXACTLY_ONCE = "EXACTLY_ONCE"   # Deduplicated guaranteed delivery