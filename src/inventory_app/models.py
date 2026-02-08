from django.conf import settings as django_settings
from django.db import models

from core.boilerplate.base_model import BaseModel

from inventory_app import logger


class InventoryItemCategory(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.clean_text_attribute('name', lower=True)
        if self.description:
            self.description = self.clean_text_attribute('description')
        super(InventoryItemCategory, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Inventory Item Category"
        verbose_name_plural = "Inventory Item Categories"
        indexes = (
            models.Index(fields=('name',)),
        )


class InventoryItem(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    sku = models.CharField(max_length=100)
    category = models.ForeignKey(
        InventoryItemCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='item_category')
    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.clean_text_attribute('name', lower=True)
        if self.description:
            self.description = self.clean_text_attribute('description')
        if self.sku:
            self.sku = self.clean_text_attribute('sku', lower=True)
            
        super(InventoryItem, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Inventory Item"
        verbose_name_plural = "Inventory Items"
        unique_together = ('name', 'sku')

        indexes = (
            models.Index(fields=('name',)),
        )


class IncomingShipment(BaseModel):
    """
    Represents an incoming shipment of inventory items. Contains details such as reference number, supplier name, associated documents, received date, and the user who received it.
    """

    reference = models.CharField(max_length=100, blank=True, null=True)
    supplier_name = models.CharField(max_length=200, blank=True, null=True)
    invoice_and_documents = models.FileField(
        upload_to='documents/shipments/invoices/', blank=True, null=True)
    received_on = models.DateTimeField(null=True, blank=True)
    received_by = models.ForeignKey(
        django_settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    items = models.ManyToManyField("IncomingShipmentLine", related_name='shipments')
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"IncomingShipment {self.reference or self.id} - {self.supplier_name or 'unknown'}"

    def save(self, *args, **kwargs):
        if self.reference:
            self.reference = self.clean_text_attribute('reference', lower=True)
        if self.supplier_name:
            self.supplier_name = self.clean_text_attribute('supplier_name')
        super(IncomingShipment, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Incoming Shipment"
        verbose_name_plural = "Incoming Shipments"
        unique_together = ('reference', 'supplier_name')
        indexes = (
            models.Index(fields=('reference',)),
            models.Index(fields=('received_on',)),
        )


class IncomingShipmentLine(BaseModel):
    """
    Represents a line item in an incoming shipment, linking to the inventory item, its quantity, unit cost, and other relevant details.
    """
    item = models.ForeignKey(
        InventoryItem, on_delete=models.PROTECT, related_name='incoming_lines')
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    batch_number = models.CharField(max_length=200, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.item.sku} x{self.quantity} (Shipment {self.shipment.reference or self.shipment.id})"

    def save(self, *args, **kwargs):
        if self.batch_number:
            self.batch_number = self.clean_text_attribute(
                'batch_number', lower=True)

        if self.item and self.quantity:
            self.item.quantity += self.quantity
            self.item.save(update_fields=['quantity'])
        super(IncomingShipmentLine, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Incoming Shipment Line"
        verbose_name_plural = "Incoming Shipment Lines"
        unique_together = ('shipment', 'item')
        indexes = (
            models.Index(fields=('shipment', 'item')),
        )
