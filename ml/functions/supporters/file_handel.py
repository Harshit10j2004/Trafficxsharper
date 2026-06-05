import os

class File():

    @staticmethod
    async def file_write(logger,cpu, cpu_idle, live_connections,client_file,client_id,req_id):

        if not os.path.exists(client_file):

            os.mkdir(os.path.dirname(client_file))


        try:

            rows = [cpu, cpu_idle, live_connections]

            with open(client_file, "a") as f:
                f.write(",".join(map(str, rows)) + "\n")

        except Exception:

            logger.exception("Error caused during data writing",
                             extra={"client_id": client_id, "req_id": req_id}
                             )

            raise