from rest_framework import status
from django.contrib.postgres.search import (
    TrigramSimilarity,
    SearchVector,
    SearchQuery,
    SearchRank,
)
from django.db.models import Q, QuerySet, F, Value
from django.utils import timezone
from inventory_app.models import (
    InventoryItem,
    InventoryItemCategory,
    IncomingShipment,
    IncomingShipmentLine,
)
from inventory_app.serializers import (
    InventoryItemCategoryIOSerializer,
    InventoryItemInputSerializer,
    InventoryItemOutputSerializer,
    IncomingShipmentInputSerializer,
    IncomingShipmentOutputSerializer,
    IncomingShipmentLineInputSerializer,
    IncomingShipmentLineOutputSerializer,
)
from inventory_app import logger
from core.boilerplate.response_template import Resp
from core.globals.constants import TIMESTRING_FORMAT
from auth_app.models import User


class InventoryItemCategoryHelpers:
    EDITABLE_FIELDS = ("name", "description")
    Model = InventoryItemCategory
    Serializer = InventoryItemCategoryIOSerializer

    @classmethod
    def get(
        cls, _id: str, name: str, return_obj: bool = False, *args, **kwargs
    ) -> Resp:
        resp = Resp()
        if _id and not name:
            cat_obj = cls.Model.objects.filter(id=_id).first()
        elif name and not _id:
            cat_obj = cls.Model.objects.filter(name__iexact=name).first()
        else:
            resp.error = "Invalid parameters."
            resp.message = "Provide either 'id' or 'name' to fetch the category."
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.error(resp.to_text())
            return resp

        if not cat_obj:
            resp.error = "Category not found."
            resp.message = f"Category ({_id if _id else name}) not found with the provided parameters."
            resp.status_code = status.HTTP_404_NOT_FOUND

            logger.error(resp.to_text())
            return resp

        resp.message = f"Category ({_id if _id else name}) fetched successfully."
        resp.data = cat_obj if return_obj else cls.Serializer(cat_obj).data
        resp.status_code = status.HTTP_200_OK

        logger.info(resp.to_text())
        return resp

    @classmethod
    def exists(cls, name: str, _id: str = None) -> bool:
        return cls.Model.objects.filter(
            Q(name__iexact=name.strip().lower()) | Q(id=_id)
        ).exists()

    @classmethod
    def create(cls, data: dict, return_obj: bool = False) -> Resp:
        resp = Resp()
        if "id" in data:
            resp.error = "ID field present."
            resp.message = "The 'id' field is auto-generated and should not be included in the request data."
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.error(resp.to_text())
            del data["id"]  # Remove ID if provided to prevent confusion

        if not (name := data.get("name")):
            resp.error = "Name is required."
            resp.message = "The 'name' field is required to create a category."
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.error(resp.to_text())
            return resp

        if cls.exists(name):
            resp.error = "Category already exists."
            resp.message = f"A category with the name '{name}' already exists. Please choose a different name."
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.error(resp.to_text())
            return resp

        serialized = cls.Serializer(data=data)
        if not serialized.is_valid():
            resp.error = "Invalid data."
            resp.message = f"{serialized.errors}"
            resp.data = data
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.error(resp.to_text())
            return resp

        serialized.save()

        resp.message = f"Category '{serialized.instance.name}' created successfully."
        resp.data = serialized.instance if return_obj else serialized.data
        resp.status_code = status.HTTP_201_CREATED

        logger.info(resp.to_text())
        return resp

    @classmethod
    def update(
        cls, user: User, _id: str, data: dict, return_obj: bool = False, *args, **kwargs
    ) -> Resp:
        resp = Resp()
        if not user or not isinstance(user, User):
            resp.error = "Invalid user."
            resp.message = "A valid user must be provided to perform this action."
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.error(resp.to_text())
            return resp

        if not (user.is_superuser or user.is_staff):
            resp.error = "Permission denied."
            resp.message = "You do not have permission to perform this action."
            resp.status_code = status.HTTP_403_FORBIDDEN

            logger.error(resp.to_text())
            return resp

        obj_resp = cls.get(_id=_id, return_obj=True)
        if obj_resp.error:
            return obj_resp

        obj = obj_resp.data
        db_data = cls.Serializer(obj).data
        for field in data:
            if field not in cls.EDITABLE_FIELDS:
                resp.error = "Invalid field."
                resp.message = f"The field '{field}' cannot be updated. Only the following fields can be updated: {', '.join(cls.EDITABLE_FIELDS)}."
                resp.data = data
                resp.status_code = status.HTTP_400_BAD_REQUEST

                logger.error(resp.to_text())
                return resp

        for field in db_data:
            db_data[field] = data.get(field, db_data[field])

        deserialized = cls.Serializer(obj, data=db_data)
        if not deserialized.is_valid():
            resp.error = "Invalid data."
            resp.message = f"{deserialized.errors}"
            resp.data = data
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.error(resp.to_text())
            return resp

        deserialized.save()

        resp.message = f"Category '{deserialized.instance.name}' updated successfully."
        resp.data = deserialized.instance if return_obj else deserialized.data
        resp.status_code = status.HTTP_200_OK

        logger.info(resp.to_text())
        return resp

    @classmethod
    def delete(cls, user: User, _id: str) -> Resp:
        resp = Resp()
        if not user or not isinstance(user, User):
            resp.error = "Invalid user."
            resp.message = "A valid user must be provided to perform this action."
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.error(resp.to_text())
            return resp

        if not (user.is_superuser or user.is_staff):
            resp.error = "Permission denied."
            resp.message = "You do not have permission to perform this action."
            resp.status_code = status.HTTP_403_FORBIDDEN

            logger.error(resp.to_text())
            return resp

        obj_resp = cls.get(_id=_id, return_obj=True)
        if obj_resp.error:
            return obj_resp

        obj = obj_resp.data
        name = obj.name
        obj.delete()

        resp.message = f"Category '{name}' deleted successfully."
        resp.status_code = status.HTTP_200_OK
        logger.info(resp.to_text())
        return resp


class InventoryItemHelpers:
    EDITABLE_FIELDS = ("name", "description", "sku", "category", "quantity", "price")
    INPUT_SERIALIZER = InventoryItemInputSerializer
    OUTPUT_SERIALIZER = InventoryItemOutputSerializer
    Model = InventoryItem

    @classmethod
    def get(
        cls, _id: str, name: str, return_obj: bool = False, *args, **kwargs
    ) -> Resp:
        resp = Resp()
        if _id and not name:
            item_obj = cls.Model.objects.filter(id=_id).first()
        elif name and not _id:
            item_obj = cls.Model.objects.filter(name__iexact=name).first()
        else:
            resp.error = "Invalid parameters."
            resp.message = "Provide either 'id' or 'name' to fetch the inventory item."
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.error(resp.to_text())
            return resp

        if not item_obj:
            resp.error = "Inventory item not found."
            resp.message = f"Inventory item ({_id if _id else name}) not found with the provided parameters."
            resp.status_code = status.HTTP_404_NOT_FOUND

            logger.error(resp.to_text())
            return resp

        resp.message = f"Inventory item ({_id if _id else name}) fetched successfully."
        resp.data = item_obj if return_obj else cls.OUTPUT_SERIALIZER(item_obj).data
        resp.status_code = status.HTTP_200_OK

        logger.info(resp.to_text())
        return resp

    @classmethod
    def search(cls, query: str, return_objs: bool = False) -> Resp:
        resp = Resp()
        if not query:
            resp.error = "Query parameter is required."
            resp.message = "The 'query' parameter is required to perform a search."
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.error(resp.to_text())
            return resp

        items_qs = (
            cls.Model.objects.annotate(
                similarity=5 * TrigramSimilarity("name", query)
                + 3 * TrigramSimilarity("description", query)
                + 1 * TrigramSimilarity("sku", query)
            )
            .filter(similarity__gte=0.25)
            .order_by("-similarity")
        )

        if not items_qs.exists():
            resp.error = "No matching inventory items found."
            resp.message = f"No inventory items found matching the query '{query}'."
            resp.status_code = status.HTTP_404_NOT_FOUND

            logger.error(resp.to_text())
            return resp

        resp.message = (
            f"Inventory items matching the query '{query}' fetched successfully."
        )
        resp.data = (
            list(items_qs)
            if return_objs
            else cls.OUTPUT_SERIALIZER(items_qs, many=True).data
        )
        resp.status_code = status.HTTP_200_OK

        logger.info(resp.to_text())
        return resp

    @classmethod
    def create(cls, data: dict, return_obj: bool = False) -> Resp:
        resp = Resp()
        if "id" in data:
            resp.error = "ID field present."
            resp.message = "The 'id' field is auto-generated and should not be included in the request data."
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.error(resp.to_text())
            del data["id"]  # Remove ID if provided to prevent confusion

        deserialized = cls.INPUT_SERIALIZER(data=data)
        if not deserialized.is_valid():
            resp.error = "Invalid data."
            resp.message = f"{deserialized.errors}"
            resp.data = data
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.error(resp.to_text())
            return resp

        deserialized.save()

        resp.message = (
            f"Inventory item '{deserialized.instance.name}' created successfully."
        )
        resp.data = (
            deserialized.instance
            if return_obj
            else cls.OUTPUT_SERIALIZER(deserialized.instance).data
        )
        resp.status_code = status.HTTP_201_CREATED

        logger.info(resp.to_text())
        return resp

    @classmethod
    def update(
        cls, user: User, _id: str, data: dict, return_obj: bool = False, *args, **kwargs
    ) -> Resp:
        resp = Resp()
        if not user or not isinstance(user, User):
            resp.error = "Invalid user."
            resp.message = "A valid user must be provided to perform this action."
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.error(resp.to_text())
            return resp

        if not (user.is_superuser or user.is_staff):
            resp.error = "Permission denied."
            resp.message = "You do not have permission to perform this action."
            resp.status_code = status.HTTP_403_FORBIDDEN

            logger.error(resp.to_text())
            return resp

        obj_resp = cls.get(_id=_id, return_obj=True)
        if obj_resp.error:
            return obj_resp

        obj = obj_resp.data
        db_data = cls.INPUT_SERIALIZER(obj).data
        for field in data:
            if field not in cls.EDITABLE_FIELDS:
                resp.error = "Invalid field."
                resp.message = f"The field '{field}' cannot be updated. Only the following fields can be updated: {', '.join(cls.EDITABLE_FIELDS)}."
                resp.data = data
                resp.status_code = status.HTTP_400_BAD_REQUEST

                logger.error(resp.to_text())
                return resp

        for field in db_data:
            db_data[field] = data.get(field, db_data[field])

        deserialized = cls.INPUT_SERIALIZER(obj, data=db_data)
        if not deserialized.is_valid():
            resp.error = "Invalid data."
            resp.message = f"{deserialized.errors}"
            resp.data = data
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.error(resp.to_text())
            return resp

        deserialized.save()

        resp.message = (
            f"Inventory item '{deserialized.instance.name}' updated successfully."
        )
        resp.data = (
            deserialized.instance
            if return_obj
            else cls.OUTPUT_SERIALIZER(deserialized.instance).data
        )
        resp.status_code = status.HTTP_200_OK

        logger.info(resp.to_text())
        return resp

    @classmethod
    def delete(cls) -> Resp:
        resp = Resp()
        resp.error = "Not implemented."
        resp.message = (
            "The delete method for InventoryItemHelpers will not be implemented."
        )
        resp.status_code = status.HTTP_501_NOT_IMPLEMENTED

        logger.error(resp.to_text())
        return resp


class IncomingShipmentLineHelpers:
    EDITABLE_FIELDS = ("item", "quantity", "price")
    INPUT_SERIALIZER = IncomingShipmentLineInputSerializer
    OUTPUT_SERIALIZER = IncomingShipmentLineOutputSerializer
    Model = IncomingShipmentLine

    @classmethod
    def get(cls, _id: str, return_obj: bool = False, *args, **kwargs) -> Resp:
        resp = Resp()
        if not _id:
            resp.error = "ID parameter is required."
            resp.message = "The 'id' parameter is required to fetch the shipment line."
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.error(resp.to_text())
            return resp

        line_obj = cls.Model.objects.filter(id=_id).first()
        if not line_obj:
            resp.error = "Shipment line not found."
            resp.message = f"Shipment line with id '{_id}' not found."
            resp.status_code = status.HTTP_404_NOT_FOUND

            logger.error(resp.to_text())
            return resp

        resp.message = f"Shipment line with id '{_id}' fetched successfully."
        resp.data = line_obj if return_obj else cls.OUTPUT_SERIALIZER(line_obj).data
        resp.status_code = status.HTTP_200_OK

        logger.info(resp.to_text())
        return resp

    @classmethod
    def create(cls, data: dict, return_obj: bool = False) -> Resp:
        resp = Resp()
        if "id" in data:
            resp.error = "ID field present."
            resp.message = "The 'id' field is auto-generated and should not be included in the request data."
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.error(resp.to_text())
            del data["id"]  # Remove ID if provided to prevent confusion

        deserialized = cls.INPUT_SERIALIZER(data=data)
        if not deserialized.is_valid():
            resp.error = "Invalid data."
            resp.message = f"{deserialized.errors}"
            resp.data = data
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.error(resp.to_text())
            return resp

        deserialized.save()

        resp.message = f"Shipment line for item '{deserialized.instance.item.name}' created successfully."
        resp.data = (
            deserialized.instance
            if return_obj
            else cls.OUTPUT_SERIALIZER(deserialized.instance).data
        )
        resp.status_code = status.HTTP_201_CREATED

        logger.info(resp.to_text())
        return resp

    @classmethod
    def update(
        cls, user: User, data: dict, _id: str, return_obj: bool = False, *args, **kwargs
    ) -> Resp:
        resp = Resp()
        if not user or not isinstance(user, User):
            resp.error = "Invalid user."
            resp.message = "A valid user must be provided to perform this action."
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.error(resp.to_text())
            return resp

        if not (user.is_superuser or user.is_staff):
            resp.error = "Permission denied."
            resp.message = "You do not have permission to perform this action."
            resp.status_code = status.HTTP_403_FORBIDDEN

            logger.error(resp.to_text())
            return resp

        obj_resp = cls.get(_id=_id, return_obj=True)
        if obj_resp.error:
            return obj_resp

        obj = obj_resp.data
        db_data = cls.INPUT_SERIALIZER(obj).data
        for field in data:
            if field not in cls.EDITABLE_FIELDS:
                resp.error = "Invalid field."
                resp.message = f"The field '{field}' cannot be updated. Only the following fields can be updated: {', '.join(cls.EDITABLE_FIELDS)}."
                resp.data = data
                resp.status_code = status.HTTP_400_BAD_REQUEST

                logger.error(resp.to_text())
                return resp

        for field in db_data:
            db_data[field] = data.get(field, db_data[field])

        deserialized = cls.INPUT_SERIALIZER(obj, data=db_data)
        if not deserialized.is_valid():
            resp.error = "Invalid data."
            resp.message = f"{deserialized.errors}"
            resp.data = data
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.error(resp.to_text())
            return resp

        deserialized.save()

        resp.message = f"Shipment line for item '{deserialized.instance.item.name}' updated successfully."
        resp.data = (
            deserialized.instance
            if return_obj
            else cls.OUTPUT_SERIALIZER(deserialized.instance).data
        )
        resp.status_code = status.HTTP_200_OK

        logger.info(resp.to_text())
        return resp

    @classmethod
    def delete(cls, user: User, _id: str, *args, **kwargs) -> Resp:
        resp = Resp()
        if not user or not isinstance(user, User):
            resp.error = "Invalid user."
            resp.message = "A valid user must be provided to perform this action."
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.error(resp.to_text())
            return resp
        if not (user.is_superuser or user.is_staff):
            resp.error = "Permission denied."
            resp.message = "You do not have permission to perform this action."
            resp.status_code = status.HTTP_403_FORBIDDEN

            logger.error(resp.to_text())
            return resp

        obj_resp = cls.get(_id=_id, return_obj=True)
        if obj_resp.error:
            return obj_resp

        obj = obj_resp.data
        item_name = obj.item.name
        obj.delete()

        resp.message = f"Shipment line for item '{item_name}' deleted successfully."
        resp.status_code = status.HTTP_200_OK

        logger.info(resp.to_text())
        return resp


class IncomingShipmentHelpers:
    EDITABLE_FIELDS = ("reference", "supplier_name", "invoice_and_documents", "notes")
    INPUT_SERIALIZER = IncomingShipmentInputSerializer
    OUTPUT_SERIALIZER = IncomingShipmentOutputSerializer
    Model = IncomingShipment

    @classmethod
    def get(cls, _id: str, return_obj: bool = False, *args, **kwargs) -> Resp:
        resp = Resp()
        if not _id:
            resp.error = "ID parameter is required."
            resp.message = (
                "The 'id' parameter is required to fetch the incoming shipment."
            )
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.error(resp.to_text())
            return resp

        shipment_obj = cls.Model.objects.filter(id=_id).first()
        if not shipment_obj:
            resp.error = "Incoming shipment not found."
            resp.message = f"Incoming shipment with id '{_id}' not found."
            resp.status_code = status.HTTP_404_NOT_FOUND

            logger.error(resp.to_text())
            return resp

        resp.message = f"Incoming shipment with id '{_id}' fetched successfully."
        resp.data = (
            shipment_obj if return_obj else cls.OUTPUT_SERIALIZER(shipment_obj).data
        )
        resp.status_code = status.HTTP_200_OK

        logger.info(resp.to_text())
        return resp

    @classmethod
    def search(cls, query: str, return_objs: bool = False) -> Resp:
        resp = Resp()
        if not query:
            resp.error = "Query parameter is required."
            resp.message = "The 'query' parameter is required to perform a search."
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.error(resp.to_text())
            return resp

        shipments_qs = (
            cls.Model.objects.annotate(
                search=SearchVector("reference", weight="A")
                + SearchVector("supplier_name", weight="B")
                + SearchVector("notes", weight="C")
                + SearchVector(F("received_by__username"), weight="D")
                + SearchVector(F("received_by__first_name"), weight="D")
                + SearchVector(F("received_by__last_name"), weight="D")
            )
            .filter(search=SearchQuery(query))
            .annotate(rank=SearchRank(F("search"), SearchQuery(query)))
            .order_by("-rank")
        )

        if not shipments_qs.exists():
            resp.error = "No matching incoming shipments found."
            resp.message = f"No incoming shipments found matching the query '{query}'."
            resp.status_code = status.HTTP_404_NOT_FOUND

            logger.error(resp.to_text())
            return resp

        resp.message = (
            f"Incoming shipments matching the query '{query}' fetched successfully."
        )
        resp.data = (
            shipments_qs
            if return_objs
            else cls.OUTPUT_SERIALIZER(shipments_qs, many=True).data
        )
        resp.status_code = status.HTTP_200_OK

        logger.info(resp.to_text())
        return resp

    @classmethod
    def create(cls, user: User, data: dict, return_obj: bool = False) -> Resp:
        resp = Resp()
        if "id" in data:
            resp.error = "ID field present."
            resp.message = "The 'id' field is auto-generated and should not be included in the request data."
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.error(resp.to_text())
            del data["id"]  # Remove ID if provided to prevent confusion

        data["received_by"] = (
            user.id
        )  # Set the received_by field to the current user's ID
        data["received_on"] = timezone.now().strftime(
            TIMESTRING_FORMAT
        )  # Set the received_on field to the current timestamp

        deserialized = cls.INPUT_SERIALIZER(data=data)
        if not deserialized.is_valid():
            resp.error = "Invalid data."
            resp.message = f"{deserialized.errors}"
            resp.data = data
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.error(resp.to_text())
            return resp

        deserialized.save()

        resp.message = (
            f"Incoming shipment '{deserialized.instance.pk}' created successfully."
        )
        resp.data = (
            deserialized.instance
            if return_obj
            else cls.OUTPUT_SERIALIZER(deserialized.instance).data
        )
        resp.status_code = status.HTTP_201_CREATED

        logger.info(resp.to_text())
        return resp

    @classmethod
    def update(
        cls, user: User, _id: str, data: dict, return_obj: bool = False, *args, **kwargs
    ) -> Resp:
        resp = Resp()
        if not user or not isinstance(user, User):
            resp.error = "Invalid user."
            resp.message = "A valid user must be provided to perform this action."
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.error(resp.to_text())
            return resp

        if not (user.is_superuser or user.is_staff):
            resp.error = "Permission denied."
            resp.message = "You do not have permission to perform this action."
            resp.status_code = status.HTTP_403_FORBIDDEN

            logger.error(resp.to_text())
            return resp

        obj_resp = cls.get(_id=_id, return_obj=True)
        if obj_resp.error:
            return obj_resp

        obj = obj_resp.data
        db_data = cls.INPUT_SERIALIZER(obj).data
        for field in data:
            if field not in cls.EDITABLE_FIELDS:
                resp.error = "Invalid field."
                resp.message = f"The field '{field}' cannot be updated. Only the following fields can be updated: {', '.join(cls.EDITABLE_FIELDS)}."
                resp.data = data
                resp.status_code = status.HTTP_400_BAD_REQUEST

                logger.error(resp.to_text())
                return resp

        for field in db_data:
            db_data[field] = data.get(field, db_data[field])

        deserialized = cls.INPUT_SERIALIZER(obj, data=db_data)
        if not deserialized.is_valid():
            resp.error = "Invalid data."
            resp.message = f"{deserialized.errors}"
            resp.data = data
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.error(resp.to_text())
            return resp

        deserialized.save()

        resp.message = (
            f"Incoming shipment '{deserialized.instance.pk}' updated successfully."
        )
        resp.data = (
            deserialized.instance
            if return_obj
            else cls.OUTPUT_SERIALIZER(deserialized.instance).data
        )
        resp.status_code = status.HTTP_200_OK
        logger.info(resp.to_text())
        return resp
