from inventory_app.models import InventoryItemCategory, InventoryItem, IncomingShipment, IncomingShipmentLine
from auth_app.serializers import UserSerializer
from rest_framework.serializers import ModelSerializer

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



# IncomingShipmentLineInputSerializer should not include shipment, as the model does not have a shipment FK anymore
class IncomingShipmentLineInputSerializer(ModelSerializer):
    class Meta:
        model = IncomingShipmentLine
        exclude = ("shipments",) if hasattr(IncomingShipmentLine, "shipments") else ()


class IncomingShipmentLineOutputSerializer(ModelSerializer):
    item = InventoryItemOutputSerializer(read_only=True)

    class Meta:
        model = IncomingShipmentLine
        exclude = ("shipments",) if hasattr(IncomingShipmentLine, "shipments") else ()



class IncomingShipmentInputSerializer(ModelSerializer):
    class Meta:
        model = IncomingShipment
        fields = "__all__"


class IncomingShipmentOutputSerializer(ModelSerializer):
    received_by = UserSerializer(read_only=True)
    items = IncomingShipmentLineOutputSerializer(many=True, read_only=True)

    class Meta:
        model = IncomingShipment
        fields = "__all__"