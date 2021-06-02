from datetime import datetime
from decimal import Decimal
from typing import Any


import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

from .config import logger


class WebSocketUsers:
    client: Any
    RES = boto3.resource("dynamodb")
    ConditionalCheckFailedException = (
        RES.meta.client.exceptions.ConditionalCheckFailedException
    )
    TABLE = RES.Table("WebSocketUsers")

    @classmethod
    def register_user(cls, username: str):
        PAYLOAD = {
            "username": username,
            "event": "registered",
            "info.registered_since": int(datetime.now().timestamp()),
        }
        try:
            response = cls.TABLE.put_item(
                Item=PAYLOAD, ConditionExpression=Attr("username").not_exists()
            )
        except cls.ConditionalCheckFailedException:
            raise ValueError("username already exists")
        return response

    @classmethod
    def update_user(cls, username: str, connected: bool):
        try:
            response = cls.TABLE.update_item(
                Key={
                    "username": username,
                    "event": "connection",
                },
                UpdateExpression="""
                set info.is_connected=:is_connected,
                info.connected_since=:connected_since""",
                ExpressionAttributeValues={
                    ":is_connected": connected,
                    ":connected_since": datetime.now().timestamp(),
                },
                ReturnValues="UPDATED_NEW",
            )
        except ClientError as e:
            if (
                e.response["Error"]["Code"]
                == "ConditionalCheckFailedException"
            ):
                logger.exception(e.response["Error"]["Message"])
            else:
                raise
        else:
            return response

    @classmethod
    def send_message(
        cls,
        username: str,
        message: str,  # message or video
        message_type: str,  # message or video
    ):
        try:
            response = cls.TABLE.update_item(
                Key={
                    "username": username,
                    "event": message_type,
                },
                UpdateExpression="""
                set info.send_date=:send_date,
                info.content=:message""",
                ExpressionAttributeValues={
                    ":send_date": datetime.now().timestamp(),
                    ":message": message,
                },
                ReturnValues="UPDATED_NEW",
            )
        except ClientError as e:
            if (
                e.response["Error"]["Code"]
                == "ConditionalCheckFailedException"
            ):
                logger.exception(e.response["Error"]["Message"])
            else:
                raise
        else:
            return response