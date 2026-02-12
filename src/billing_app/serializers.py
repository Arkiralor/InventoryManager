
from rest_framework.serializers import ModelSerializer
from billing_app.models import ItemTax, Bill, BillItem
from inventory_app.serializers import InventoryItemOutputSerializer

# ItemTax: single serializer (no FK)
class ItemTaxSerializer(ModelSerializer):
	class Meta:
		model = ItemTax
		fields = "__all__"

# BillItem serializers
class BillItemInputSerializer(ModelSerializer):
	class Meta:
		model = BillItem
		fields = "__all__"

class BillItemOutputSerializer(ModelSerializer):
	item = InventoryItemOutputSerializer(read_only=True)
	taxes = ItemTaxSerializer(many=True, read_only=True)

	class Meta:
		model = BillItem
		fields = "__all__"

# Bill serializers
class BillInputSerializer(ModelSerializer):
	class Meta:
		model = Bill
		fields = "__all__"

class BillOutputSerializer(ModelSerializer):
	bill_items = BillItemOutputSerializer(many=True, read_only=True)

	class Meta:
		model = Bill
		fields = "__all__"
