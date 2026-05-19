import logging
import os
from fastapi import HTTPException, status
from deceng.aws.helper import get_ec2
from deceng.setting.loggers import LoggerFactory
from deceng.setting.conifg import settings

logger = LoggerFactory.get_logger(
    name="aws_up",
    log_file=settings.LOG_FILE_AWS_U,
    level=logging.INFO
)

class AWS_up():

    @staticmethod
    async def start_instance(ami, total_instances, server_type, pending_file, req_id, client_id, security_group,
                             joining_token):
        try:

            userdata_template = """#!/bin/bash

            LOCAL_IP=$(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)

            until systemctl is-active --quiet docker; do sleep 3; done

            docker swarm join \\
              --token {joining_token} \\
              --advertise-addr "${{LOCAL_IP}}" \\
              --data-path-addr "${{LOCAL_IP}}" \\
              3.109.123.199:2377 || echo "Join failed" >&2
            """

            security_group_main = [security_group]

            userdata = userdata_template.format(joining_token=joining_token)

            response = get_ec2().run_instances(
                ImageId=ami,
                MinCount=1,
                MaxCount=total_instances,
                InstanceType=server_type,
                KeyName=settings.KEY,
                SecurityGroupIds=security_group_main,
                SubnetId=settings.SUBID,
                UserData=userdata,
                TagSpecifications=[
                    {
                        "ResourceType": "instance",
                        "Tags": [
                            {"Key": "Name", "Value": f"tsx-worker-{client_id}"},

                        ]
                    }
                ]
            )

            instance_ids = [i["InstanceId"] for i in response["Instances"]]

            os.makedirs(os.path.dirname(pending_file), exist_ok=True)
            with open(pending_file, "a") as f:
                for iid in instance_ids:
                    f.write(iid + "\n")

            return instance_ids


        except Exception:

            logger.exception(
                "AWS caused issue during starting the server",
                extra={"Req_id": req_id, "client_id": client_id}
            )

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="aws have issue during starting servers "
            )





    @staticmethod
    async def health_check(instance_id, req_id, client_id):
        try:

            waiter = get_ec2().get_waiter("instance_status_ok")
            waiter.wait(
                InstanceIds=[instance_id],
                WaiterConfig={
                    "Delay": 10,
                    "MaxAttempts": 30
                }
            )

            return "healthy"
        except Exception:

            logger.exception("EC2 waiting time caused error",
                              extra={"Req_id": req_id, "client_id": client_id}
                              )
            raise

