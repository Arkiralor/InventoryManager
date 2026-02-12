from django.db import models
from core.boilerplate.base_model import BaseModel
from inventory_app.models import InventoryItem


class ItemTax(BaseModel):
    name = models.CharField(max_length=64)
    category = models.CharField(max_length=64, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        if self.percentage < 0:
            raise ValueError("Tax percentage cannot be negative.")
        self.clean_text_attribute("name", lower=True)
        self.clean_text_attribute("category", lower=True)
        self.clean_text_attribute("description")
        super(ItemTax, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Item Tax"
        verbose_name_plural = "Item Taxes"
        indexes = (
            models.Index(fields=("name", "category")),
            models.Index(fields=("percentage",)),
        )


class Bill(BaseModel):
    additional_discount_percentage = models.DecimalField(
        max_digits=32, decimal_places=2, default=0.00
    )
    total_amount = models.DecimalField(max_digits=32, decimal_places=2, default=0.00)
    paid_amount = models.DecimalField(max_digits=32, decimal_places=2, default=0.00)
    due_amount = models.DecimalField(max_digits=32, decimal_places=2, default=0.00)
    note = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        for item in self.items:
            item.save()
        self.calculate_totals()
        if self.note:
            self.clean_text_attribute("note")
        super(Bill, self).save(*args, **kwargs)

    def calculate_totals(self):
        bill_items = self.items
        total_amount = bill_items.aggregate(total=models.Sum('total'))['total'] or 0
        total_amount -= (total_amount * self.additional_discount_percentage) / 100
        self.total_amount = total_amount
        self.due_amount = self.total_amount - self.paid_amount

    class Meta:
        verbose_name = "Bill"
        verbose_name_plural = "Bills"
        indexes = (
            models.Index(fields=("total_amount",)),
            models.Index(fields=("paid_amount",)),
            models.Index(fields=("due_amount",)),
        )

    @property
    def items(self):
        return BillItem.objects.filter(bill=self).order_by("created_at")

class BillItem(BaseModel):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="bill_items")
    item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT)
    taxes = models.ManyToManyField(ItemTax, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    discount = models.DecimalField(max_digits=16, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=32, decimal_places=2, default=0.00)
    note = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        taxes: list[ItemTax] = self.taxes.all()
        self.total = self.item.price * self.quantity
        for tax in taxes:
            self.total += (self.total * tax.percentage) / 100
        self.total -= self.discount

        if self.note:
            self.clean_text_attribute("note")
        super(BillItem, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Bill Item"
        verbose_name_plural = "Bill Items"
        indexes = (
            models.Index(fields=("item",)),
            models.Index(fields=("quantity",)),
            models.Index(fields=("discount",)),
            models.Index(fields=("total",)),
        )
