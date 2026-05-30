class Redis_data():

    @staticmethod
    def redis_packet(timestamp, cpu, cpu_idle, totalram, ramused, diskusage, networkin, networkout, live_connections, client_id,
           server_expected, server_responded, missing_server_count, rps,conn_rate,queue_pressure,rps_per_node,missing_server):
        used_percent = 0
        if totalram:
            used_percent = round((ramused / totalram) * 100, 2)

        for_redis = {
            "type": "metrics",
            "timestamp": timestamp,
            "client_id": client_id,

            "cpu": {
                "usage_percent": cpu,
                "idle_percent": cpu_idle,
            },

            "memory": {
                "total_mb": totalram,
                "used_mb": ramused,
                "used_percent": used_percent,
            },

            "disk": {
                "usage_percent": diskusage,
            },

            "network": {
                "in": networkin,
                "out": networkout,
            },

            "connections": {
                "live": live_connections,
                "rps": rps,
                "conn_rate": conn_rate,
                "queue_pressure": queue_pressure,
                "rps_per_node": rps_per_node,
            },

            "cluster": {
                "server_expected": server_expected,
                "server_responded": server_responded,
                "missing_server_count": missing_server_count,
                "missing_servers": missing_server,
            },
        }

        return for_redis