import datetime


class Check():

    @staticmethod
    async def red_check(queue_increasing,rps_increasing):

        try:

            app_red_zone = False

            if (queue_increasing >= 3 and rps_increasing >= 3):
                app_red_zone = True
                return True

            return False

        except Exception:
            pass

    @staticmethod

    async def grey_check(threshold,buffer_lower,cpu,buffer_z):

        try:

            in_gray_zone = False

            if(threshold - buffer_lower) <= cpu < (threshold + buffer_z):

                in_gray_zone = True
                return True

            return False


        except Exception:
            pass

    @staticmethod
    async def cooldown(last_scale_up_time):

        try:
            
            cur_time = int(datetime.utcnow().timestamp())

            D_COOLDOWN = 240
            COOLDOWN = 300
            in_cooldown = False
            in_d_cooldown = False
            if last_scale_up_time:
                if cur_time - int(last_scale_up_time) < COOLDOWN:
                    in_cooldown = True

        except Exception:
            pass

