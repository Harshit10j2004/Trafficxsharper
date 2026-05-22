class Window():

    @staticmethod
    async def increasing_window(cur_value, last_value, total):
        if (
                cur_value > last_value
        ):
            total = total + 1

        else:

            total = max(0, total - 1)

        return total
