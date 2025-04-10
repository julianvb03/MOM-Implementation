import json
from redis import Redis


def process_log(redis: Redis, raw_log: str):
    """
    Process a log from Redis and update database state accordingly.
    """
    try:
        log = json.loads(raw_log)
        event = log.get("event")
        origin = log.get("origin")
        target = log.get("target")
        topics = log.get("topics")

        if event == "node_down":
            redis.srem("active_moms", origin)
            print(f"[ZK_SYNC] Removed {origin} from active_moms")

        elif event == "replica_up":
            redis.sadd("active_moms", origin)
            print(f"[ZK_SYNC] Added {origin} to active_moms")

        elif event == "failover" and topics:
            # Example: failover of topic T1 to mom-2
            for topic in topics:
                redis.set(f"topic:{topic}:primary", target)
                print(f"[ZK_SYNC] Set topic:{topic}:primary -> {target}")

    except Exception as e:
        print(f"[ZK_SYNC] Failed to process log: {e}")
