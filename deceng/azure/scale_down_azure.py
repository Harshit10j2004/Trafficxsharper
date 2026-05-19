from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
import os
import logging
from deceng.setting.loggers import LoggerFactory
from deceng.setting.conifg import settings

logger = LoggerFactory.get_logger(
    name="azure_down",
    log_file=settings.LOG_FILE_AZURE_D,
    level=logging.INFO
)

class Azure_down():

        @staticmethod
        async def removing_instance_azure(id, client_id, req_id):
            try:

                credential = DefaultAzureCredential()
                subscription_id = os.getenv("SUB_ID")

                resource_client = ResourceManagementClient(credential, subscription_id)

                vm_resource_id = f"/subscriptions/{subscription_id}/resourceGroups/providers/Microsoft.Compute/virtualMachines/{id}"

                poller = resource_client.resources.begin_delete_by_id(
                    resource_id=vm_resource_id
                )

                poller.wait()
            except Exception:
                logger.exception(
                    "Issue raised during terminating the vm from azure",
                    extra={"req_id": req_id, "client_id": client_id}
                )


