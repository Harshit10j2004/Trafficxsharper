from datetime import datetime,timezone
from fastapi import HTTPException,status

class TimeCheck():

    @staticmethod
    async def time_check(timestamp):

        client_ts = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = abs((now - client_ts).total_seconds())

        ALLOWED_SKEW = 60

        if delta > ALLOWED_SKEW:

            return False

        return True
