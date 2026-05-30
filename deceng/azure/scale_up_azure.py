from azure.mgmt.compute import ComputeManagementClient
from azure.identity import DefaultAzureCredential
from azure.mgmt.network import NetworkManagementClient
import os
import base64
import logging
import time
from deceng.setting.loggers import LoggerFactory
from deceng.setting.conifg import settings

logger = LoggerFactory.get_logger(
    name="azure_up",
    log_file=settings.LOG_FILE_AZURE_U,
    level=logging.INFO
)

class Azure_up():

    @staticmethod
    async def start_instance_azure(image, total_instances, server_type, pending_file, req_id, client_id, joining_token,
                             security_group_id,manager_ip):
        try:



            userdata_template = """#!/bin/bash

            LOCAL_IP=$(curl -s -H "Metadata:true" "http://169.254.169.254/metadata/instance/network/interface/0/ipv4/ipAddress/0/privateIpAddress?api-version=2021-02-01&format=text")
            PUBLIC_IP=$(curl -s -H "Metadata:true" "http://169.254.169.254/metadata/instance/network/interface/0/ipv4/ipAddress/0/publicIpAddress?api-version=2021-02-01&format=text")

            until systemctl is-active --quiet docker; do sleep 3; done

            docker swarm join \\
              --token {joining_token} \\
              --advertise-addr "${{PUBLIC_IP}}" \\
              --data-path-addr "${{PUBLIC_IP}}" \\
              {manager_ip}:2377 || echo "Join failed" >&2

                """
            userdata = userdata_template.format(joining_token=joining_token, manager_ip=manager_ip)
            custom_data = base64.b64encode(userdata.encode('utf-8')).decode('ascii')

            subscription_id = settings.SUB_ID
            resource_group = settings.RES_GRP
            location = "japaneast"
            subnet_id = settings.SUBNET_ID
            admin_username = "harshit"
            admin_password = settings.ADM_PAS
            vm_name_prefix = "tsx-worker"

            credential = DefaultAzureCredential()
            compute_client = ComputeManagementClient(credential, subscription_id)
            network_client = NetworkManagementClient(credential, subscription_id)

            instance_ids = []

            for i in range(1, total_instances + 1):
                vm_name = f"{vm_name_prefix}-{client_id}-{i:03d}"
                nic_name = f"{vm_name}-nic"
                public_ip_name = f"{vm_name}-pip"

                print(f"Creating Azure VM: {vm_name}")

                public_ip_poller = network_client.public_ip_addresses.begin_create_or_update(
                    resource_group,
                    public_ip_name,
                    {
                        "location": location,
                        "sku": {"name": "Standard"},
                        "public_ip_allocation_method": "Static",
                        "public_ip_address_version": "IPV4"
                    }
                )
                public_ip = public_ip_poller.result()

                nic_params = {
                    "location": location,
                    "ip_configurations": [{
                        "name": "ipconfig1",
                        "subnet": {"id": subnet_id},
                        "public_ip_address": {"id": public_ip.id},
                        "private_ip_allocation_method": "Dynamic"
                    }]
                }

                if security_group_id:
                    nic_params["network_security_group"] = {"id": security_group_id}

                nic_poller = network_client.network_interfaces.begin_create_or_update(
                    resource_group, nic_name, nic_params
                )
                nic = nic_poller.result()

                vm_params = {
                    "location": location,
                    "hardware_profile": {
                        "vm_size": server_type
                    },
                    "storage_profile": {
                        "image_reference": {
                            "id": image
                        },
                        "os_disk": {
                            "create_option": "FromImage",
                            "managed_disk": {"storage_account_type": "Standard_LRS"},
                            "delete_option": "Delete"
                        }
                    },
                    "os_profile": {
                        "computer_name": vm_name,
                        "admin_username": admin_username,
                        "admin_password": admin_password,
                        "custom_data": custom_data
                    },
                    "network_profile": {
                        "network_interfaces": [{
                            "id": nic.id,
                            "primary": True
                        }]
                    },
                    "security_profile": {
                        "security_type": "TrustedLaunch",
                        "uefi_settings": {
                            "secure_boot_enabled": True,
                            "v_tpm_enabled": True
                        }
                    },
                    "tags": {
                        "Name": f"tsx-worker-{client_id}",
                        "ClientId": str(client_id),
                        "RequestId": str(req_id)
                    }
                }

                if "linux" in image.lower():
                    vm_params["os_profile"]["linux_configuration"] = {
                        "disable_password_authentication": False
                    }

                vm_poller = compute_client.virtual_machines.begin_create_or_update(
                    resource_group, vm_name, vm_params
                )
                vm = vm_poller.result()

                print(f"  → Created VM: {vm.name} (ID: {vm.vm_id})")

                instance_ids.append(vm.id)

                time.sleep(1)

                os.makedirs(os.path.dirname(pending_file), exist_ok=True)
                with open(pending_file, "a") as f:
                    for name in instance_ids:
                        f.write(name + "\n")
                time.sleep(2)

            return instance_ids

        except Exception:

            logger.exception("Creating vm in azure caused issue",
                              extra={"client_id": client_id, "req_id": req_id})


