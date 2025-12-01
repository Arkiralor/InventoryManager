from collections import OrderedDict

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.utils.serializer_helpers import ReturnDict

from core import logger


class Resp:
    """
    Wrapper class to make sharing method responses between different modules and APIs, more standardised.
    """
    error: str = None
    message: str = None
    data: any = None
    status_code: int = None

    def __init__(self, error: str = None, message: str = None, data: any = None, status_code: int = None) -> None:
        if error:
            self.error = error
        if message:
            self.message = message
        if data:
            self.data = data
        if status_code:
            self.status_code = status_code

    def to_dict(self):
        """
        Returns the `data` attribute in an objects into a dictionary if there is not error; otherwise returns the error as a dictionary.
        """
        ## (prithoo): We don't exactly need this statement anymore, but I am too afraid to remove it even though I know 100% what exactly it does.
        # if self.error:
        #     logger.warning(self.to_text())

        if (isinstance(self.data, dict) or isinstance(self.data, OrderedDict) or isinstance(self.data, ReturnDict) or isinstance(self.data, list)) and not self.error:
            return self.data

        else:
            return {
                "error": self.error,
                "message": self.to_text(),
                "data": self.data
            }

    def to_text(self):
        """
        Converts the error and message into a single line of text for logging purposes.
        """
        return f"{self.error.upper()+': ' if self.error else ''}{self.message}"

    def to_response(self):
        """
        Returns an HTTP response constructed from the contents of an object.
        """
        return Response(
            self.to_dict(),
            status=self.status_code if self.status_code else status.HTTP_200_OK
        )

    def to_exception(self):
        """
        Throws an API Exception constructed from the contents of the object.
        """
        logger.warning(self.to_text())

        return APIException(
            detail=self.to_text(),
            code=self.error
        )