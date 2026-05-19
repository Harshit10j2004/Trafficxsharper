import boto3

ec2_client = None

class get_ec2():

    @staticmethod
    async def get_ec2():
        global ec2_client
        if ec2_client is None:
            ec2_client = boto3.client("ec2", region_name="ap-south-1")
        return ec2_client
