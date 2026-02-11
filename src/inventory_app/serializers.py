from inventory_app.models import (
    InventoryItemCategory,
    InventoryItem,
    IncomingShipment,
    IncomingShipmentLine,
)
from auth_app.serializers import UserSerializer
from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField


class InventoryItemCategoryIOSerializer(ModelSerializer):
    class Meta:
        model = InventoryItemCategory
        fields = "__all__"


class InventoryItemInputSerializer(ModelSerializer):
    class Meta:
        model = InventoryItem
        fields = "__all__"


class InventoryItemOutputSerializer(ModelSerializer):
    category = InventoryItemCategoryIOSerializer(read_only=True)

    class Meta:
        model = InventoryItem
        fields = "__all__"


class IncomingShipmentLineInputSerializer(ModelSerializer):
    class Meta:
        model = IncomingShipmentLine
        fields = [
            "item",
            "shipment",
            "quantity",
            "unit_cost",
            "batch_number",
            "expiry_date",
        ]


class IncomingShipmentLineOutputSerializer(ModelSerializer):
    item = InventoryItemOutputSerializer(read_only=True)
    shipment = PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = IncomingShipmentLine
        fields = [
            "id",
            "item",
            "shipment",
            "quantity",
            "unit_cost",
            "batch_number",
            "expiry_date",
        ]


class IncomingShipmentInputSerializer(ModelSerializer):
    class Meta:
        model = IncomingShipment
        fields = "__all__"


class IncomingShipmentOutputSerializer(ModelSerializer):
    received_by = UserSerializer(read_only=True)
    lines = IncomingShipmentLineOutputSerializer(many=True, read_only=True)

    class Meta:
        model = IncomingShipment
        fields = [
            "id",
            "reference",
            "supplier_name",
            "invoice_and_documents",
            "received_on",
            "received_by",
            "notes",
            "lines",
        ]
