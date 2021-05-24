# coding=utf-8
import boto3
from os import environ

REGION = environ["AWS_REGION"] or environ.get("AWS_DEFAULT_REGION")


def _create(domain_name: str, stage: str):
    ENDPOINT = "https://{domain_name}/{stage}"
    endpoint = ENDPOINT.format(domain_name=domain_name, stage=stage)
    return boto3.client(
        "apigatewaymanagementapi", endpoint_url=endpoint, region_name=REGION
    )


def send(domain_name: str, stage: str, connection_id: str, message: str):
    ws = _create(domain_name, stage)
    return ws.post_to_connection(Data=message, ConnectionId=connection_id)
