from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from inventory_app.helpers import (
    InventoryItemCategoryHelpers,
    InventoryItemHelpers,
    IncomingShipmentLineHelpers,
    IncomingShipmentHelpers,
)
from inventory_app import logger
from rest_framework.permissions import IsAuthenticated, IsAdminUser


class InventoryItemCategoryAPI(APIView):
    permmission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        resp = InventoryItemCategoryHelpers._list()
        return resp.to_response()

    def post(self, request: Request) -> Response:
        resp = InventoryItemCategoryHelpers.create(request.data)
        return resp.to_response()


class InventoryItemCategoryManagementAPI(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        _id = request.query_params.get("id")
        name = request.query_params.get("name")
        resp = InventoryItemCategoryHelpers.get(_id=_id, name=name)
        return resp.to_response()

    def put(self, request: Request) -> Response:
        _id = request.data.get("id")
        resp = InventoryItemCategoryHelpers.update(
            user=request.user, _id=_id, data=request.data
        )
        return resp.to_response()

    def delete(self, request: Request) -> Response:
        _id = request.data.get("id")
        resp = InventoryItemCategoryHelpers.delete(user=request.user, _id=_id)
        return resp.to_response()
    

class InventoryItemAPI(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        resp = InventoryItemHelpers.search(
            query=request.query_params.get("query"),
        )
        return resp.to_response()

    def post(self, request: Request) -> Response:
        resp = InventoryItemHelpers.create(data=request.data)
        return resp.to_response()
    
class InventoryItemManagementAPI(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        _id = request.query_params.get("id")
        name = request.query_params.get("name")
        resp = InventoryItemHelpers.get(_id=_id, name=name)
        return resp.to_response()

    def put(self, request: Request) -> Response:
        _id = request.data.get("id")
        resp = InventoryItemHelpers.update(
            user=request.user, _id=_id, data=request.data
        )
        return resp.to_response()

    def delete(self, request: Request) -> Response:
        resp = InventoryItemHelpers.delete()
        return resp.to_response()
