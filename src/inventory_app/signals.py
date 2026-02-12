from django.db.models.signals import post_save, pre_save, pre_delete
from inventory_app.models import (
    InventoryItem,
    InventoryItemCategory,
    IncomingShipment,
    IncomingShipmentLine,
)
from inventory_app import logger


class InventoryItemCategorySignalHandler:
    MODEL = InventoryItemCategory

    @classmethod
    def create(cls, sender, instance: InventoryItemCategory, created, **kwargs):
        if created:
            logger.info(f"InventoryItemCategory created: {instance.name}")

    @classmethod
    def update(cls, sender, instance: InventoryItemCategory, created, **kwargs):
        if not created:
            logger.info(f"InventoryItemCategory updated: {instance.name}")

    @classmethod
    def delete(cls, sender, instance: InventoryItemCategory, **kwargs):
        logger.info(f"InventoryItemCategory deleted: {instance.name}")


post_save.connect(
    InventoryItemCategorySignalHandler.create,
    sender=InventoryItemCategorySignalHandler.MODEL,
)
post_save.connect(
    InventoryItemCategorySignalHandler.update,
    sender=InventoryItemCategorySignalHandler.MODEL,
)
pre_delete.connect(
    InventoryItemCategorySignalHandler.delete,
    sender=InventoryItemCategorySignalHandler.MODEL,
)


class InventoryItemSignalHandler:
    MODEL = InventoryItem

    @classmethod
    def create(cls, sender, instance: InventoryItem, created, **kwargs):
        if created:
            logger.info(f"InventoryItem created: {instance.name}")

    @classmethod
    def update(cls, sender, instance: InventoryItem, created, **kwargs):
        if not created:
            logger.info(f"InventoryItem updated: {instance.name}")

    @classmethod
    def delete(cls, sender, instance: InventoryItem, **kwargs):
        if IncomingShipmentLine.objects.filter(item=instance).exists():
            logger.error(
                f"Cannot delete InventoryItem '{instance.name}': referenced by IncomingShipmentLine."
            )
            raise Exception(
                f"Cannot delete InventoryItem '{instance.name}': referenced by IncomingShipmentLine."
            )
        logger.info(f"InventoryItem deleted: {instance.name}")

    @classmethod
    def update(cls, sender, instance: InventoryItem, created, **kwargs):
        if not created:
            logger.info(f"InventoryItem updated: {instance.name}")
            # Low stock alert
            LOW_STOCK_THRESHOLD = 10
            if (
                instance.quantity is not None
                and instance.quantity < LOW_STOCK_THRESHOLD
            ):
                logger.warning(
                    f"InventoryItem '{instance.name}' is low on stock: {instance.quantity}"
                )


post_save.connect(
    InventoryItemSignalHandler.create, sender=InventoryItemSignalHandler.MODEL
)
post_save.connect(
    InventoryItemSignalHandler.update, sender=InventoryItemSignalHandler.MODEL
)
pre_delete.connect(
    InventoryItemSignalHandler.delete, sender=InventoryItemSignalHandler.MODEL
)


class IncomingShipmentSignalHandler:
    MODEL = IncomingShipment

    @classmethod
    def create(cls, sender, instance: IncomingShipment, created, **kwargs):
        if created:
            logger.info(f"IncomingShipment created: {instance.id}")

    @classmethod
    def update(cls, sender, instance: IncomingShipment, created, **kwargs):
        if not created:
            logger.info(f"IncomingShipment updated: {instance.id}")

    @classmethod
    def delete(cls, sender, instance: IncomingShipment, **kwargs):
        logger.info(f"IncomingShipment deleted: {instance.id}")


post_save.connect(
    IncomingShipmentSignalHandler.create, sender=IncomingShipmentSignalHandler.MODEL
)
post_save.connect(
    IncomingShipmentSignalHandler.update, sender=IncomingShipmentSignalHandler.MODEL
)
pre_delete.connect(
    IncomingShipmentSignalHandler.delete, sender=IncomingShipmentSignalHandler.MODEL
)


class IncomingShipmentLineSignalHandler:
    MODEL = IncomingShipmentLine

    @classmethod
    def create(cls, sender, instance: IncomingShipmentLine, created, **kwargs):
        if created:
            logger.info(f"IncomingShipmentLine created: {instance.id}")

    @classmethod
    def update(cls, sender, instance: IncomingShipmentLine, created, **kwargs):
        if not created:
            logger.info(f"IncomingShipmentLine updated: {instance.id}")

    @classmethod
    def delete(cls, sender, instance: IncomingShipmentLine, **kwargs):
        logger.info(f"IncomingShipmentLine deleted: {instance.id}")


post_save.connect(
    IncomingShipmentLineSignalHandler.create,
    sender=IncomingShipmentLineSignalHandler.MODEL,
)
post_save.connect(
    IncomingShipmentLineSignalHandler.update,
    sender=IncomingShipmentLineSignalHandler.MODEL,
)
pre_delete.connect(
    IncomingShipmentLineSignalHandler.delete,
    sender=IncomingShipmentLineSignalHandler.MODEL,
)
