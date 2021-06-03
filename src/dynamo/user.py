from datetime import datetime

from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

from . import TABLE
from ..common.config import logger


class User:
    @property
    def is_registered(self):
        response = TABLE.get_item(
            Key={"username": self.username, "event": "REGISTERED"}
        )
        exists = bool(response.get("Item"))
        logger.info(f"{exists=}")
        return exists

    def _register_user(self):
        failed_check = False
        for process in (self._put_connection_list, self._put_registered):
            try:
                process()
            except ValueError as e:
                failed_check = True

        if failed_check:
            raise ValueError(e)

    def __init__(self, username: str):
        self.username = username

        if not self.is_registered:
            self._register_user()

    def add_connection(self, connection_id: str) -> dict:
        try:
            response = TABLE.update_item(
                Key={"username": self.username, "event": "CONNECTIONS"},
                UpdateExpression="""\
                SET connections = list_append(connections,":new_conn)\
                SET info.updated = :updated""",
                ReturnValues="UPDATED_NEW",
                # TODO check (info.updated) update
                ExpressionAttributeValues={
                    ":new_conn": [connection_id],
                    ":updated": int(datetime.now().timestamp()),
                },
                ConditionExpression=~Attr("connections").contains(
                    connection_id
                ),
            )
        except ClientError as e:
            if (
                e.response["Error"]["Code"]
                == "ConditionalCheckFailedException"
            ):
                logger.exception(e.response["Error"]["Message"])
                raise ValueError("connection already exists")
            else:
                raise
        else:
            return response

    def send_message(self, message: str, message_type: str):
        return TABLE.put_item(
            Item={
                "username": self.username,
                "event": "MESSAGES",
                "content": message,
                "info.message_type": message_type,
                "info.updated": int(datetime.now().timestamp()),
            },
            ReturnValues="NONE",
        )

    def _put_connection_list(self):
        try:
            response = TABLE.put_item(
                Item={
                    "username": self.username,
                    "event": "CONNECTIONS",
                    "content": [],
                    "info.updated": int(datetime.now().timestamp()),
                },
                ConditionExpression=Attr("event").not_exists(),
                ReturnValues="NONE",
            )
        except ClientError as e:
            if (
                e.response["Error"]["Code"]
                == "ConditionalCheckFailedException"
            ):
                logger.exception(e.response["Error"]["Message"])
                raise ValueError("user already exists")
            else:
                raise
        else:
            return response

    def _put_registered(self):
        try:
            response = TABLE.put_item(
                Item={
                    "username": self.username,
                    "event": "REGISTERED",
                    "info.updated": int(datetime.now().timestamp()),
                },
                ConditionExpression=Attr("username").not_exists(),
                ReturnValues="NONE",
            )
        except ClientError as e:
            if (
                e.response["Error"]["Code"]
                == "ConditionalCheckFailedException"
            ):
                logger.exception(e.response["Error"]["Message"])
                raise ValueError("user already exists")
            else:
                raise
        else:
            return response

    def __str__(self):
        return str(self.username)

    def __dict__(self):
        return {"username": self.username}
