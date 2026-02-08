from django.urls import path
from inventory_app.apis import (
    InventoryItemCategoryAPI,
    InventoryItemCategoryManagementAPI,
    InventoryItemAPI,
    InventoryItemManagementAPI,
    IncomingShipmentAPI,
    IncomingShipmentManagementAPI,
    IncomingShipmentLineAPI,
    IncomingShipmentLineManagementAPI,
)


PREFIX = "api/inventory/"

urlpatterns = [
    path(
        "categories/",
        InventoryItemCategoryAPI.as_view(),
        name="inventory-item-category-list-create",
    ),
    path(
        "categories/manage/",
        InventoryItemCategoryManagementAPI.as_view(),
        name="inventory-item-category-manage",
    ),
    path("items/", InventoryItemAPI.as_view(), name="inventory-item-list-create"),
    path(
        "items/manage/",
        InventoryItemManagementAPI.as_view(),
        name="inventory-item-manage",
    ),
    path(
        "shipments/",
        IncomingShipmentAPI.as_view(),
        name="incoming-shipment-list-create",
    ),
    path(
        "shipments/manage/",
        IncomingShipmentManagementAPI.as_view(),
        name="incoming-shipment-manage",
    ),
    path(
        "shipments-lines/",
        IncomingShipmentLineAPI.as_view(),
        name="incoming-shipment-line-list-create",
    ),
    path(
        "shipments-lines/manage/",
        IncomingShipmentLineManagementAPI.as_view(),
        name="incoming-shipment-line-manage",
    ),
]
