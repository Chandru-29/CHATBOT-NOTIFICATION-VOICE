# GLOBAL RULES, CONSTRAINTS & SEMANTIC MAPPINGS

TYPE: rules

## BUSINESS TERM MAPPING:

- "material" / "item" → item.materialCode
- "sku" / "store inventory" → store.sku
- "stock" / "available inventory" → store.totalQty / store.actualQty
- "suid" → SS_SULOCATION.suid
- "location" / "bin" → location.locationName / SS_LOCATION.locationId
- "warehouse" → warehouse.warehouseCode / SS_WAREHOUSE.warehouseCode
- "picklist" → pickuplist.pickupListCode / SS_PICKLIST.picklistCode
- "piv order" / "process order" → pivHeaders.poNumber / pivAllocation.pickupListCode
- "pallet" → assetmaster.assetId / store.palletId / pallet.palletId
- "movement" → movementHeaders / movementPickuplist / movementLineItems
- "grn" → store.grnNumber

## INTENT MAPPING & LOGIC:

TYPE: logic

- "item stock in store" → item + store
- "open pickup lists" → pickuplist WHERE status IN (0, 1, 2) OR SS_PICKLIST WHERE status IN (0, 1, 2, 3, 4)
- "completed picklists" → SS_PICKLIST WHERE status = 5
- "po batch details" → pivHeaders
- "piv order allocation" → pivHeaders + pivAllocation
- "piv production phases" → pivHeaders + pivPhases
- "material movement by document" → movementHeaders + movementLineItems
- "expiration date" / "expiry date" → store.shelfLife (already a DATETIME/DATE column, do NOT calculate via DATE_ADD)

## SPECIAL RULES & CONSTRAINTS:

- **formatting**: Present non-empty SQL execution results in a clean Markdown table with business-friendly Title Case column headers (e.g., convert `cd` to `Created Date`). Include a brief introductory summary sentence. If 0 rows are returned, provide a clear message (e.g., "No matching records found") instead of rendering an empty table.
- **Soft Delete Rule**: Always filter `isDeleted = 0` (or `isDeleted = '0'`) for tables containing the isDeleted column.
- **SQL Dialect**: Target MySQL syntax (Use `LIMIT` instead of `TOP`).
- **Join Integrity**: Follow defined joins strictly. Do NOT assume missing relationships.
- **Keywords**: Always wrap table names in backticks (e.g., `user`, `store`, `location`, `action`, `resource`) to avoid MySQL syntax errors.
- **Sorting (Latest/Recent)**: Always sort by `cd DESC` (unless filtering completed records where `ud DESC` applies for completion date).
- **Multi-Value Filters**: ALWAYS use `IN (...)` clause for multiple filter values (e.g., `WHERE materialCode IN ('MAT01', 'MAT02')`).
- **User Resolution**: `pickuplist.assignedUser` → `user.userId` or `user.userName`; Return `user.name`, `user.userName`.

# TABLE: user

TYPE: schema


BUSINESS TERMS:
- "user" / "assigned user" / "operator" / "employee" → user.userId / user.userName / user.name
- "email" → user.email
- "role" → user.roleId

COLUMNS:
id (PK)
name
userName (UNIQUE)
userId (UNIQUE)
email (UNIQUE)
password
roleId
firstlogin
isMobileLoggedIn
isDashboardLoggedIn
printerId
isDefaultPrinterSet
isDeleted
cd
ud
USAGE: Central user credentials used across picklists, inventory updates, and material movements.

RELATIONSHIPS:

TYPE: relationship

- `user.userId <-> SS_PICKLIST.assignedUser`
- `user.userId <-> pickuplist.assignedUser`
- `user.userId <-> store.userId`
- `user.userId <-> pivAllocation.assignedUser`
- `user.userId <-> movementPickuplist.assignedUser`
- `user.userId <-> SS_SUPERSEDEFEFOMAPPING.userId`
- `user.userId <-> stainersManualWeightlogs.userId`
- `user.userId <-> approvalRequests.requestedBy`
- `user.userId <-> approvalRequests.approvedBy`

---

# TABLE: log

TYPE: schema

COLUMNS:
id (PK)
email
role
endPoint
event
method
createdAt
USAGE: System audit trails and endpoint tracking.

RELATIONSHIPS:

TYPE: relationship

- `log.email <-> user.email`

---

# TABLE: gatewayLogs

TYPE: schema

COLUMNS:
id (PK)
topic
GrossWeight
NetWeight
TareWeight
cd
USAGE: Hardware weighbridge MQTT/Gateway weight events.

---

# TABLE: SS_PICKLIST

TYPE: schema


BUSINESS TERMS:
- "picklist" / "smart storage picklist" → SS_PICKLIST.picklistCode
- "picklist status" → SS_PICKLIST.status
- "open picklists" → SS_PICKLIST.status IN (0, 1, 2, 3, 4)
- "completed picklists" → SS_PICKLIST.status = 5
- "completion date" → SS_PICKLIST.ud
- "document type" → SS_PICKLIST.documentTypeId
- "assigned user" → SS_PICKLIST.assignedUser

COLUMNS:
picklistId (PK, UNIQUE)
picklistCode (UNIQUE)
documentTypeId
documentNumber
mvtId
status
picklistTypeStatus
assignedUser
transactionId
pivHeaderId
pivPhaseId
supersedeFEFO
isDeleted
cd
ud
cdBy
udBy

STATUS:
0 = Created
1 = Released
2 = Picking Started
3 = Picked
4 = Putaway Started
5 = Completed

COMPLETION LOGIC:

TYPE: logic

- If status = 5 (Completed) → completion date = ud (Updated Date)
- "completion date" ALWAYS maps to SS_PICKLIST.ud

DOCUMENT TYPE DEFINITIONS:
1 → GRN
21 → Work Order
16 → Transfer Order

DEFAULT OUTPUT:
picklistCode, status

RELATIONSHIPS:

TYPE: relationship

- `SS_PICKLIST.picklistId <-> SS_PICKLISTVIEW.picklistId`
- `SS_PICKLIST.picklistId <-> SS_PICKLISTITEM.picklistId`
- `SS_PICKLIST.picklistId <-> SS_PICKLISTSTAGEMAP.picklistId`
- `SS_PICKLIST.picklistId <-> SS_PIVALLOCATION.picklistId`
- `SS_PICKLIST.picklistId <-> SS_SULOCATION.picklistId`
- `SS_PICKLIST.picklistId <-> SS_SUPERSEDEFEFOMAPPING.picklistId`
- `SS_PICKLIST.documentTypeId <-> SS_DOCUMENT.documentId`
- `SS_PICKLIST.mvtId <-> SS_MVT.mvtId`
- `SS_PICKLIST.transactionId <-> SS_TRANSACTIONM.transactionId`
- `SS_PICKLIST.pivHeaderId <-> pivHeaders.id`
- `SS_PICKLIST.pivPhaseId <-> pivPhases.id`
- `SS_PICKLIST.assignedUser <-> user.userId`

QUERY PATTERNS:

TYPE: query

OPEN SS PICKLISTS:

```sql
SELECT
  picklistCode,
  documentNumber,
  status,
  cd
FROM SS_PICKLIST
WHERE status IN (0, 1, 2, 3, 4)
  AND isDeleted = 0
ORDER BY cd DESC
LIMIT 20;
```

COMPLETED PICKLISTS WITH COMPLETION DATE:

```sql
SELECT
  picklistCode,
  documentNumber,
  status,
  ud AS completionDate
FROM SS_PICKLIST
WHERE status = 5
  AND isDeleted = 0
ORDER BY ud DESC
LIMIT 20;
```

---

# TABLE: SS_PICKLISTVIEW

TYPE: schema

COLUMNS:
picklistViewId (PK)
picklistId
itemId
suidId
suid
pickedQty
allocatedQty
sourceLocId
sourcePalletId
sourceBinId
sourceAssetId
status
isDeleted
cd
ud
cdBy
udBy

RELATIONSHIPS:

TYPE: relationship

- `SS_PICKLISTVIEW.itemId <-> item.id`
- `SS_PICKLISTVIEW.picklistViewId <-> SS_SUIDCHARGINGMAPPING.picklistViewId`

---

# TABLE: SS_PICKLISTITEM

TYPE: schema

COLUMNS:
picklistItemId (PK)
picklistId
itemId
qty
allocatedQty
pickedQty
status
isDeleted
cd
ud
USAGE: Line-item breakdown of materials requested per picklist.

RELATIONSHIPS:

TYPE: relationship

- `SS_PICKLISTITEM.itemId <-> item.id`

---

# TABLE: SS_PICKLISTSTAGEMAP

TYPE: schema

COLUMNS:
stageMapId (PK)
picklistId
itemId
stageId
stageCode
status
isDeleted
cd
ud
USAGE: Maps picklist items to their assigned picking stages.

RELATIONSHIPS:

TYPE: relationship

- `SS_PICKLISTSTAGEMAP.itemId <-> item.id`

---

# TABLE: SS_PIVALLOCATION

TYPE: schema

COLUMNS:
allocationId (PK)
picklistId
itemId
qty
allocatedQty
status
isDeleted
cd
ud
USAGE: PIV-level allocation records linked to picklists and items.

RELATIONSHIPS:

TYPE: relationship

- `SS_PIVALLOCATION.itemId <-> item.id`

---

# TABLE: SS_DOCUMENTTR

TYPE: schema

COLUMNS:
transactionRefId (PK)
documentTypeId
itemId
qty
transactionType
status
cd
ud
USAGE: Document transaction reference records linking document types and items.

RELATIONSHIPS:

TYPE: relationship

- `SS_DOCUMENTTR.documentTypeId <-> SS_DOCUMENT.documentId`
- `SS_DOCUMENTTR.itemId <-> item.id`

---

# TABLE: pickuplist

TYPE: schema


BUSINESS TERMS:
- "picklist" / "pickup list" → pickuplist.pickupListCode
- "open pickup lists" → pickuplist.status IN (0, 1, 2)
- "assigned user" → pickuplist.assignedUser
- "order number" / "po number" → pickuplist.documentNumber

COLUMNS:
id (PK)
plant
pickupListCode (UNIQUE)
documentType
documentNumber
lineNumber
srNo
materialCode
qty
uom
source
destination
status
cd
assignedUser
pickupStartTime
pickupEndTime
resourceId
ud
prdKittingStatus
officer
storeUserAllocationTime
materialReturnUser
forceClosed
forceClosedTime

RELATIONSHIPS:

TYPE: relationship

- `pickuplist.pickupListCode <-> pickupListMapping.pickupListCode`
- `pickuplist.documentNumber <-> pivHeaders.poNumber`
- `pickuplist.assignedUser <-> user.userId`

QUERY PATTERNS:

TYPE: query

OPEN PICKUP LISTS:

```sql
SELECT
  p.pickupListCode,
  p.documentNumber,
  p.materialCode,
  p.qty,
  p.status,
  u.name AS assignedUserName
FROM pickuplist p
LEFT JOIN user u ON p.assignedUser = u.userId
WHERE p.status IN (0, 1, 2)
ORDER BY p.cd DESC
LIMIT 50;
```

---

# TABLE: pickupListMapping

TYPE: schema

COLUMNS:
id (PK)
pickupListCode
materialCode
sku
qty
pickedQty
allocatedQty
uom
locationId
palletId
virtualBinId
isPicked
isPutaway
cd
pickupStartTime
pickupEndTime
chargedStatus
chargedTime
resource
operator
chargedQty
ispartial
kittingTime
putawayTime
releaseToShopFloorTime
isMaterialReturned

---

# TABLE: SS_SUPERSEDEFEFOMAPPING

TYPE: schema

COLUMNS:
supersedaFefoMapId (PK)
picklistId
reason
userId
isDeleted
cd
ud
cdBy
udBy

RELATIONSHIPS:

TYPE: relationship

- `SS_SUPERSEDEFEFOMAPPING.userId <-> user.userId`

---

# TABLE: item

TYPE: schema


BUSINESS TERMS:
- "material" / "item" / "raw material" → item.materialCode
- "material description" / "item name" → item.materialDescription
- "material type" → item.materialType / item.materialTypeDesc
- "uom" / "unit of measure" → item.uom
- "storage location" / "sloc" → item.sloc / item.storLoc
- "fefo" → item.isFEFO

COLUMNS:
id (PK)
plant
materialCode (UNIQUE)
materialDescription
materialType
materialTypeDesc
materialGroup
uom
issueType
sloc
sloc2
procurementType
shelfLife
batchIndicator
isFEFO
partialCharging
storLoc
isXBT
cd
USAGE: Item and raw material master reference data

RELATIONSHIPS:

TYPE: relationship

- `item.materialCode <-> store.materialCode`
- `item.id <-> SS_ITEMCATEGORYMAP.itemId`
- `item.id <-> sapStockStatus.itemId`
- `item.id <-> ss_itemMinMaxAndSectionMap.itemId`
- `item.id <-> SS_ITEMLOCACNMAP.itemId`
- `item.id <-> SS_PICKLISTITEM.itemId`
- `item.id <-> SS_PICKLISTVIEW.itemId`
- `item.id <-> SS_DOCUMENTTR.itemId`
- `item.materialCode <-> intermediateFilling.materialCode`

QUERY PATTERNS:

TYPE: query

TOTAL STOCK BY MATERIAL:

```sql
SELECT
  i.materialCode,
  i.materialDescription,
  SUM(s.totalQty) AS totalStock,
  i.uom
FROM item i
JOIN store s ON i.materialCode = s.materialCode
WHERE s.isRejected = 0
GROUP BY i.materialCode, i.materialDescription, i.uom;
```

---

# TABLE: store

TYPE: schema


BUSINESS TERMS:
- "sku" / "store inventory" → store.sku
- "stock" / "available inventory" → store.totalQty / store.actualQty
- "grn" / "grn number" → store.grnNumber
- "expiration date" / "expiry date" / "shelf life" → store.shelfLife
- "batch" / "batch number" → store.batchNumber
- "vendor" / "supplier" → store.vendorCode / store.vendorName
- "pallet" → store.palletId
- "quantity" / "received qty" → store.actualQty / store.invoiceQty

COLUMNS:
id (PK)
sku (UNIQUE)
grnNumber
grnDate
grnLineNumber
asnNumber
invoiceNumber
vendorCode
vendorName
materialCode
materialDescription
mfgDate
shelfLife : shelfLife (stores expiry date timestamp, e.g., 'YYYY-MM-DD')
uom
batchNumber
plant
sourceLocation
storingLocation
locationId
invoiceQty
actualQty
holdQty
packSize
totalPacks
totalQty
printedDate
palletId
isPutaway
isPartFull
putawayStartTime
putawayEndTime
stockType
isRejected
rejectedQty
isBatch
userName
movementRestrictedQty
userId
reValidation
isRestricted
storageCon
isPiv
refDocType
refDoc
poNumber
reprintCount
isMaterialReturned
parentSkuId
USAGE: Primary warehouse storage inventory and inbound SKU ledger

RELATIONSHIPS:

TYPE: relationship

- `store.id <-> SS_SULOCATION.skuId`
- `store.id <-> revalidation.skuId`
- `store.id <-> updateQIStatusLog.skuId`
- `store.palletId <-> pallet.palletId`
- `store.palletId <-> assetMaster.id`
- `store.userId <-> user.userId`

---

# TABLE: SS_SULOCATION

TYPE: schema


BUSINESS TERMS:
- "suid" / "storage unit" / "storage unit id" → SS_SULOCATION.suid
- "bin" / "bin location" → SS_SULOCATION.locationId / SS_SULOCATION.binId
- "pallet" → SS_SULOCATION.palletId
- "unit quantity" → SS_SULOCATION.qty

COLUMNS:
suidId (PK)
suid (UNIQUE)
skuId
qty
packSize
locationId
isGrouped
grnLineNumber
serialNumber
status
palletId
binId
tempAssetId
inTransit
onHold
picklistId
isAllocated
rejectionReason
documentId
kittingType
isDeleted
cd
ud
cdBy
udBy
RULE: Unit storage tracking for picklist fulfillment and bin location mapping

RELATIONSHIPS:

TYPE: relationship

- `SS_SULOCATION.locationId <-> SS_LOCATION.locationId`
- `SS_SULOCATION.picklistId <-> SS_PICKLIST.picklistId`
- `SS_SULOCATION.suid <-> movementSuidMapping.suId`

---

# TABLE: location

TYPE: schema


BUSINESS TERMS:
- "location" / "bin" / "physical bin" → location.locationName
- "warehouse zone" → location.zoneId

COLUMNS:
id (PK)
locationName
warehouseId
zoneId
isEmpty
isDeleted
cd
ud
USAGE: Legacy physical warehouse storage bin definitions.

RELATIONSHIPS:

TYPE: relationship

- `location.warehouseId <-> warehouse.id`

---

# TABLE: SS_LOCATION

TYPE: schema


BUSINESS TERMS:
- "smart storage location" / "location code" / "bin" → SS_LOCATION.locationCode / SS_LOCATION.locationName
- "parent location" → SS_LOCATION.parentCode / SS_LOCATION.parentId

COLUMNS:
locationId (PK)
locationCode (UNIQUE)
locationName
parentId
parentCode
isLocation
rltId
status
isEmpty
isDeleted
cd
ud
USAGE: Smart storage location hierarchy entity.

RELATIONSHIPS:

TYPE: relationship

- `SS_LOCATION.locationId <-> ss_whlocmap.locationId`
- `SS_LOCATION.locationId <-> ss_itemMinMaxAndSectionMap.sectionId`
- `SS_LOCATION.locationId <-> SS_ITEMLOCACNMAP.locationId`
- `SS_LOCATION.rltId <-> SS_RELATIONALALLLTYPE.rltId`
- `SS_LOCATION.parentId <-> SS_LOCATION.locationId`

---

# TABLE: warehouse

TYPE: schema


BUSINESS TERMS:
- "warehouse" / "warehouse code" → warehouse.warehouseCode / warehouse.warehouseName
- "plant" → warehouse.plant

COLUMNS:
id (PK)
warehouseCode (UNIQUE)
warehouseName
plant
isDeleted
cd
ud
USAGE: Physical warehouse facility definitions.

---

# TABLE: SS_WAREHOUSE

TYPE: schema


BUSINESS TERMS:
- "smart warehouse" / "warehouse code" → SS_WAREHOUSE.warehouseCode / SS_WAREHOUSE.warehouseName

COLUMNS:
warehouseId (PK)
warehouseCode (UNIQUE)
warehouseName
warehouseTypeId
plantId
acnId
isActive
isDeleted
cd
ud
cdBy
udBy
USAGE: Smart storage warehouse definitions.

RELATIONSHIPS:

TYPE: relationship

- `SS_WAREHOUSE.warehouseId <-> ss_whlocmap.warehouseId`
- `SS_WAREHOUSE.warehouseId <-> SS_WHTYPEMAP.warehouseId`
- `SS_WAREHOUSE.warehouseId <-> SS_WHRLTMAP.warehouseId`

---

# TABLE: ss_whlocmap

TYPE: schema

COLUMNS:
id (PK)
warehouseId
locationId
isDeleted
cd
ud
USAGE: Mapping table linking warehouses to location hierarchies.

---

# TABLE: SS_WHTYPEMAP

TYPE: schema

COLUMNS:
id (PK)
warehouseId
typeId
isDeleted
cd
ud
USAGE: Warehouse type classification mapping table.

---

# TABLE: SS_ITEMCATEGORY

TYPE: schema

COLUMNS:
categoryId (PK)
categoryCode (UNIQUE)
categoryName
description
cd
USAGE: Master item category definitions.

RELATIONSHIPS:

TYPE: relationship

- `SS_ITEMCATEGORY.categoryId <-> SS_ITEMCATEGORYMAP.categoryId`

---

# TABLE: SS_RELATIONALALLLTYPE

TYPE: schema

COLUMNS:
rltId (PK)
rltCode (UNIQUE)
rltName
description
cd
USAGE: Relation allocation type master definitions.

---

# TABLE: SS_ITEMLOCACNMAP

TYPE: schema

COLUMNS:
id (PK)
itemId
locationId
isDeleted
cd
USAGE: Item to location association mapping table.

---

# TABLE: SS_ITEMCATEGORYMAP

TYPE: schema

COLUMNS:
id (PK)
itemId
categoryId
isDeleted
cd
USAGE: Maps items to their assigned item categories.

---

# TABLE: ss_itemMinMaxAndSectionMap

TYPE: schema

COLUMNS:
id (PK)
itemId
sectionId
rltId
minQty
maxQty
cd
ud
USAGE: Defines min/max stock thresholds for items per storage section.

---

# TABLE: sapStockStatus

TYPE: schema

COLUMNS:
id (PK)
itemId
stockStatus
plant
cd
ud
USAGE: SAP-synchronized stock status records per item.

---

# TABLE: ss_relationalLocType

TYPE: schema

COLUMNS:
rltId (PK)
rltCode (UNIQUE)
rltName
description
cd
USAGE: Relational location type master used to classify location hierarchies and item-section mappings.

RELATIONSHIPS:

TYPE: relationship

- `ss_relationalLocType.rltId <-> ss_itemMinMaxAndSectionMap.rltId`

---

# TABLE: SS_WHRLTMAP

TYPE: schema

COLUMNS:
id (PK)
warehouseId
rltId
isDeleted
cd
ud
USAGE: Maps warehouses to their relational location types.

---

# TABLE: pivHeaders

TYPE: schema


BUSINESS TERMS:
- "piv order" / "process order" / "production order" / "po" → pivHeaders.poNumber
- "po batch details" / "batch" → pivHeaders.batchNumber
- "final material" → pivHeaders.finalMaterialCode / pivHeaders.finalMaterialDescription
- "order status" / "closed order" → pivHeaders.isPoClosed

COLUMNS:
id (PK)
plant
date
poNumber (UNIQUE)
orderType
mrpType
prodVer
createdDate
releaseDate
plannedStartDate
plannedEndDate
basicStartDate
basicFinishDate
tecoDate
batchNumber
batchSize
batchUom
batchPercQty
finalMaterialCode
finalMaterialDescription
cd
plantDesc
isPoClosed
poClosedTime
USAGE: Production order headers and PIV batch schedules

RELATIONSHIPS:

TYPE: relationship

- `pivHeaders.poNumber <-> pivAllocation.documentNumber`
- `pivHeaders.poNumber <-> pivPhases.poNumber`
- `pivHeaders.poNumber <-> pivmaterialissueslip.poNumber`
- `pivHeaders.poNumber <-> pickuplist.documentNumber`
- `pivHeaders.id <-> SS_PICKLIST.pivHeaderId`
- `pivHeaders.poNumber <-> intermediateFilling.poNumber`
- `pivHeaders.poNumber <-> intermediateFillingGrn.poNumber`
- `pivHeaders.poNumber <-> productionFilling.poNumber`

QUERY PATTERNS:

TYPE: query

PIV PO ALLOCATION DETAILS:

```sql
SELECT
  ph.poNumber,
  ph.finalMaterialCode,
  ph.batchNumber,
  pa.materialCode,
  pa.qty,
  pa.actualWeight,
  pa.status
FROM pivHeaders ph
JOIN pivAllocation pa ON ph.poNumber = pa.documentNumber
WHERE ph.poNumber = '{poNumber}'
  AND pa.isDeleted = 0;
```

---

# TABLE: pivPhases

TYPE: schema


BUSINESS TERMS:
- "piv production phases" / "process phase" → pivPhases.phaseNumber / pivPhases.phaseDescription
- "phase material quantity" → pivPhases.materialQty

COLUMNS:
id (PK)
poNumber
phaseNumber
phaseDescription
srNo
itemNo
batchNumber
resources
materialCode
materialDescription
materialPercQty
materialQty
upperLimit
lowerLimit
materialUom
phaseProInstruction
gi
sign
status
ctaStatus
ctaTime
officerId
sapRes
isSapPosted
postedDate
cd
matIssuanceDate
proReleaseTime
storeIssuanceDate
releasePickuplistDate
USAGE: Step-by-step production process phase details and material thresholds

RELATIONSHIPS:

TYPE: relationship

- `pivphases.id <-> SS_PICKLIST.pivPhaseId`

---

# TABLE: pivMaterialIssueSlip

TYPE: schema

COLUMNS:
id (PK)
poNumber
pBatchNumber
finalMaterialCode
finalMaterialDescription
orderStartDate
orderQty
phaseDescription
materialCode
materialDescription
formQty
uom
batchNumber
batchQty
storageLoc
cd
USAGE: Material issue slips for shop-floor batch consumption

---

# TABLE: pivAllocation

TYPE: schema


BUSINESS TERMS:
- "piv order allocation" / "batch allocation" → pivAllocation.pickupListCode / pivAllocation.documentNumber
- "gross weight" / "tare weight" / "actual weight" → pivAllocation.grossWeight / pivAllocation.tareWeight / pivAllocation.actualWeight

COLUMNS:
id (PK)
documentType
documentNumber
lineNumber
srNo
materialCode
materialDescription
finalMaterialCode
finalMaterialDescription
qty
pickupListCode (UNIQUE)
destination
grossWeight
tareWeight
actualWeight
balanceBatchQty
assetId
assignedUser
resource
startTime
endTime
status
cd
isDeleted
ud
weightSaved
checker
charged
source
USAGE: Batch material allocations mapped to pickup lists and weighbridges

RELATIONSHIPS:

TYPE: relationship

- `pivAllocation.assignedUser <-> user.userId`
- `pivAllocation.pickupListCode <-> pickuplist.pickupListCode`

---

# TABLE: movementHeaders

TYPE: schema


BUSINESS TERMS:
- "movement" / "material movement" / "transfer order" → movementHeaders.documentNumber
- "movement type" → movementHeaders.movementType

COLUMNS:
id (PK)
documentNumber (UNIQUE)
movementType
tCode
plant
vendorName
vendorCode
cd
udCode
USAGE: Header information for material movement and transfer documents.

RELATIONSHIPS:

TYPE: relationship

- `movementheaders.documentNumber <-> movementLineItems.documentNumber`
- `movementheaders.documentNumber <-> movementPickuplist.documentNumber`
- `movementheaders.documentNumber <-> movementSuidMapping.documentNumber`

---

# TABLE: movementLineItems

TYPE: schema


BUSINESS TERMS:
- "movement line item" / "transferred material" → movementLineItems.materialCode / movementLineItems.qty
- "source" / "destination" → movementLineItems.source / movementLineItems.destination

COLUMNS:
id (PK)
plant
materialCode
documentNumber
movementType
tCode
lineNumber
qty
uom
source
destination
inspectionLotId
batchNumber
grnNumber
grnLineNumber
recvMaterial
recvPlant
recvPlantDescription
recvBatch
status
cd
expiryDate
USAGE: Line items specifying transfer quantities and locations.

RELATIONSHIPS:

TYPE: relationship

- `movementLineItems.documentNumber <-> movementPickuplist.documentNumber`

---

# TABLE: movementPickupList

TYPE: schema


BUSINESS TERMS:
- "movement pickup list" → movementPickupList.pickupListCode
- "movement operator" / "assigned user" → movementPickupList.assignedUser

COLUMNS:
id (PK)
plant
pickupListCode (UNIQUE)
movementType
tCode
documentNumber
lineNumber
materialCode
qty
uom
source
destination
status
assignedUser
cd
movementStartTime
movementEndTime
expiryDate
USAGE: Pickup lists generated specifically for material transfers.

RELATIONSHIPS:

TYPE: relationship

- `movementPickuplist.pickupListCode <-> movementSuidMapping.pickupListCode`
- `movementPickuplist.assignedUser <-> user.userId`

---

# TABLE: movementSuidMapping

TYPE: schema


BUSINESS TERMS:
- "moved suid" / "transferred stock unit" → movementSuidMapping.suId

COLUMNS:
id (PK)
documentNumber
pickupListCode
materialCode
suId
qty
pickedQty
allocatedQty
uom
locationId
palletId
virtualBinId
grnNumber
isPicked
isPutaway
cd
documentType
movedQty
USAGE: SUID-level tracking for picked and moved stock units.

RELATIONSHIPS:

TYPE: relationship

- `movementSuidMapping.suId <-> SS_SULOCATION.suid`

---

# TABLE: movementTypes

TYPE: schema

COLUMNS:
id (PK)
movementTypeCode (UNIQUE)
movementTypeName
description
cd
USAGE: Reference table defining movement type classifications.

RELATIONSHIPS:

TYPE: relationship

- `movementtypes.movementTypeCode <-> movementHeaders.movementType`

---

# TABLE: SS_MVT

TYPE: schema

COLUMNS:
mvtId (PK)
mvtCode (UNIQUE)
mvtName
description
status
isDeleted
cd
ud
USAGE: Standard movement type definitions and codes referenced by picklists.

RELATIONSHIPS:

TYPE: relationship

- `SS_MVT.mvtId <-> SS_DOCMVTMAP.mvtId`
- `SS_MVT.mvtId <-> SS_PICKLIST.mvtId`

---

# TABLE: SS_DOCUMENT

TYPE: schema

COLUMNS:
documentId (PK)
documentCode (UNIQUE)
documentName
description
status
isDeleted
cd
ud
USAGE: Master document type definitions (e.g., GRN, Transfer Order, Work Order) used to classify picklists and movement transactions.

RELATIONSHIPS:

TYPE: relationship

- `SS_DOCUMENT.documentId <-> SS_DOCMVTMAP.documentId`
- `SS_DOCUMENT.documentId <-> SS_DOCUMENTTR.documentTypeId`
- `SS_DOCUMENT.documentId <-> SS_PICKLIST.documentTypeId`

---

# TABLE: SS_DOCMVTMAP

TYPE: schema

COLUMNS:
id (PK)
documentId
mvtId
isDeleted
cd
ud
USAGE: Mapping table linking document types to allowed movement types.

---

# TABLE: accesses

TYPE: schema

COLUMNS:
id (PK)
roleId
subModuleId
actionId
cd
USAGE: Role-based access permissions mapping.

RELATIONSHIPS:

TYPE: relationship

- `accesses.subModuleId <-> submodules.subModuleId`
- `accesses.actionId <-> action.actionId`

---

# TABLE: action

TYPE: schema

COLUMNS:
actionId (PK)
actionName
subModuleId
cd
USAGE: System action definitions linked to submodules.

RELATIONSHIPS:

TYPE: relationship

- `action.subModuleId <-> submodules.subModuleId`

---

# TABLE: submodules

TYPE: schema

COLUMNS:
subModuleId (PK)
subModuleName
moduleId
cd
USAGE: System feature sub-modules.

---

# TABLE: department

TYPE: schema

COLUMNS:
id (PK)
departmentName
cd
USAGE: Plant organizational department list.

---

# TABLE: QualityInspector

TYPE: schema


BUSINESS TERMS:
- "quality inspector" / "qi" / "inspector" → QualityInspector.employeeId / QualityInspector.Name

COLUMNS:
id (PK)
employeeId (UNIQUE)
Name
userName (UNIQUE)
email
role
cd
USAGE: Authorized quality inspector credentials and profiles.

RELATIONSHIPS:

TYPE: relationship

- `QualityInspector.employeeId <-> revalidation.inspectorId`

---

# TABLE: rejMaterialDetails

TYPE: schema


BUSINESS TERMS:
- "rejected material" / "rejected stock" / "quality rejection" → rejMaterialDetails.sku / rejMaterialDetails.qty

COLUMNS:
id (PK)
sku
materialCode
grnNumber
batchNumber
userId
qty
uom
palletId
cd
USAGE: Logs of materials rejected during quality inspection.

---

# TABLE: revalidation

TYPE: schema


BUSINESS TERMS:
- "revalidation" / "shelf life revalidation" → revalidation.revalidatedDate / revalidation.status

COLUMNS:
id (PK)
skuId
materialCode
batchNumber
status
revalidatedDate
inspectorId
cd
USAGE: Material shelf-life and quality revalidation logs.

RELATIONSHIPS:

TYPE: relationship

- `revalidation.skuId <-> store.id`

---

# TABLE: updateQIStatusLog

TYPE: schema

COLUMNS:
id (PK)
skuId
oldStatus
newStatus
updatedBy
cd
USAGE: Audit trail for quality inspector status updates.

RELATIONSHIPS:

TYPE: relationship

- `updateQIStatusLog.skuId <-> store.id`

---

# TABLE: reqTypes

TYPE: schema

COLUMNS:
reqTypeId (PK)
typeCode (UNIQUE)
typeName
description
cd
USAGE: Request type classification definitions.

RELATIONSHIPS:

TYPE: relationship

- `reqTypes.reqTypeId <-> approvalRequests.reqTypeId`

---

# TABLE: approvalRequests

TYPE: schema


BUSINESS TERMS:
- "approval" / "approval request" / "request status" → approvalRequests.status / approvalRequests.requestedBy / approvalRequests.approvedBy

COLUMNS:
id (PK)
reqTypeId
requestData
status
requestedBy
approvedBy
cd
ud
USAGE: Approval workflow requests categorized by request type.

RELATIONSHIPS:

TYPE: relationship

- `approvalRequests.requestedBy <-> user.userId`
- `approvalRequests.approvedBy <-> user.userId`

---

# TABLE: assetMaster

TYPE: schema


BUSINESS TERMS:
- "asset" / "container" / "tote" → assetMaster.assetCode / assetMaster.assetType

COLUMNS:
id (PK)
assetCode (UNIQUE)
assetType
locationId
status
isDeleted
cd
ud
USAGE: Master catalog of plant physical assets and containers.

RELATIONSHIPS:

TYPE: relationship

- `assetMaster.id <-> palletBinMapping.binPalletId`
- `assetMaster.id <-> palletBinMapping.binAId`
- `assetMaster.id <-> palletBinMapping.binBId`
- `assetMaster.id <-> palletBinMapping.binCId`
- `assetMaster.id <-> palletBinMapping.binDId`
- `assetMaster.id <-> store.palletId`

---

# TABLE: palletBinMapping

TYPE: schema

COLUMNS:
id (PK)
binPalletId
binAId
binBId
binCId
binDId
cd
ud
USAGE: Maps pallet-level bins (A/B/C/D) to physical asset records.

---

# TABLE: pallet

TYPE: schema


BUSINESS TERMS:
- "pallet" / "pallet id" / "pallet code" → pallet.palletId / pallet.palletCode
- "pallet capacity" → pallet.capacity

COLUMNS:
palletId (PK)
palletCode (UNIQUE)
capacity
status
isDeleted
cd
ud
USAGE: Physical storage pallet inventory.

RELATIONSHIPS:

TYPE: relationship

- `pallet.palletId <-> store.palletId`

---

# TABLE: tempAssetMapping

TYPE: schema

COLUMNS:
id (PK)
tempAssetId
realAssetId
suid
cd
USAGE: Temporary asset to permanent asset mapping ledger.

---

# TABLE: resource

TYPE: schema

COLUMNS:
id (PK)
resourceCode (UNIQUE)
resourceName
plant
status
cd
USAGE: Machine, equipment, and work-center resources.

RELATIONSHIPS:

TYPE: relationship

- `resource.id <-> SS_RESOURCEZONEMAPPING.resourceId`

---

# TABLE: SS_RESOURCEZONEMAPPING

TYPE: schema

COLUMNS:
id (PK)
resourceId
zoneId
zoneCode
status
isDeleted
cd
ud
USAGE: Maps resources (machines/work-centers) to warehouse zones.

---

# TABLE: operationMaster

TYPE: schema

COLUMNS:
opId (PK)
opCode (UNIQUE)
opName
description
status
cd
USAGE: Master list of plant operations and processes.

RELATIONSHIPS:

TYPE: relationship

- `operationMaster.opId <-> operationTimeMapping.opId`

---

# TABLE: operationTimeMapping

TYPE: schema

COLUMNS:
id (PK)
opId
standardTime
uom
plant
cd
ud
USAGE: Standard time allocations per operation for scheduling and capacity planning.

---

# TABLE: SS_SUIDCHARGINGMAPPING

TYPE: schema

COLUMNS:
id (PK)
picklistViewId
chargedQty
chargedStatus
chargedTime
cd
ud
USAGE: Tracks SUID charging events linked to picklist view line items.

RELATIONSHIPS:

TYPE: relationship

- `SS_SUIDCHARGINGMAPPING.picklistViewId <-> SS_PICKLISTVIEW.picklistViewId`

---

# TABLE: printer

TYPE: schema

COLUMNS:
id (PK)
printerName
ipAddress
plant
isDefault
cd
USAGE: Network barcode and document printer configurations.

---

# TABLE: intermediateFilling

TYPE: schema


BUSINESS TERMS:
- "intermediate filling" / "chemical filling" / "fill weight" → intermediateFilling.netWeight / intermediateFilling.grossWeight

COLUMNS:
id (PK)
poNumber
materialCode
materialDescription
batchNumber
tareWeight
grossWeight
netWeight
filledQty
status
cd
USAGE: Intermediate chemical filling logs.

RELATIONSHIPS:

TYPE: relationship

- `intermediateFilling.materialCode <-> item.materialCode`
- `intermediateFilling.poNumber <-> pivHeaders.poNumber`

---

# TABLE: intermediateFillingGrn

TYPE: schema

COLUMNS:
id (PK)
grnNumber
poNumber
materialCode
batchNumber
totalQty
cd
USAGE: GRN records for intermediate filled stock.

RELATIONSHIPS:

TYPE: relationship

- `intermediateFillingGrn.poNumber <-> pivHeaders.poNumber`

---

# TABLE: productionFilling

TYPE: schema


BUSINESS TERMS:
- "production filling" / "paint filling" / "actual weight" → productionFilling.actualWeight / productionFilling.targetQty

COLUMNS:
id (PK)
pickupListCode
poNumber
materialCode
batchNumber
targetQty
actualWeight
balanceBatchQty
status
cd
USAGE: Final paint production filling weight records.

RELATIONSHIPS:

TYPE: relationship

- `productionFilling.pickupListCode <-> pickuplist.pickupListCode`
- `productionFilling.poNumber <-> pivHeaders.poNumber`
- `productionFilling.materialCode <-> item.materialCode`

---

# TABLE: stainersManualWeightlogs

TYPE: schema

COLUMNS:
id (PK)
uId
weight
userId
scannedOfficer
cd
USAGE: Manual stainer scale weighing logs.

RELATIONSHIPS:

TYPE: relationship

- `stainersManualWeightlogs.userId <-> user.userId`

---
