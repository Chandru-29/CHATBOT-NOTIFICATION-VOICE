# DOMAIN: 0. Global & Shared System Entities

TYPE: context
INTENT: Manage universal cross-cutting entities including user identity resolution, authentication credentials, system-wide audit trails, and real-time weighbridge hardware telemetry.
TARGET TABLES: user, log, gatewaylogs
DESCRIPTION: Core administrative and telemetry layer providing centralized access to user profiles, endpoint event logs, and automated weighbridge gateway metrics required for cross-domain operational tracking.

### TABLE: user

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

### TABLE: log

COLUMNS:
id (PK)
email
role
endPoint
event
method
createdAt
USAGE: System audit trails and endpoint tracking.

### TABLE: gatewayLogs

COLUMNS:
id (PK)
topic
GrossWeight
NetWeight
TareWeight
cd
USAGE: Hardware weighbridge gateway logs.



# DOMAIN: 1. Picklist & Warehouse Picking Management

TYPE: schema_domain
INTENT: Manage warehouse order picking workflows, picklist lifecycles, line-item quantities, supervisors, and FEFO override exception rules.
TARGET TABLES: SS_PICKLIST, SS_PICKLISTVIEW, SS_PICKLISTITEM, SS_PICKLISTSTAGEMAP, SS_PIVALLOCATION, SS_SULOCATION, SS_SUPERSEDEFEFOMAPPING, SS_DOCUMENTTR, pickuplist, pickuplistmapping
DESCRIPTION: Covers all operational tables, statuses, and query patterns associated with warehouse picking and fulfillment execution.

### TABLE: SS_PICKLIST

COLUMNS:
picklistId (PK, UNIQUE)
picklistCode (UNIQUE)
documentTypeId → SS_DOCUMENT.documentId
documentNumber
mvtId → SS_MVT.mvtId
status
picklistTypeStatus
assignedUser → user.userId
transactionId → SS_TRANSACTIONM.transactionId
pivHeaderId → pivHeaders.id
pivPhaseId → pivphases.id
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

- If status = 5 (Completed) → completion date = ud (Updated Date)
- "completion date" ALWAYS maps to SS_PICKLIST.ud

DOCUMENT TYPE DEFINITIONS:
1 → GRN
21 → Work Order
16 → Transfer Order

DEFAULT OUTPUT:
picklistCode, status

### TABLE: SS_PICKLISTVIEW

COLUMNS:
picklistViewId (PK)
picklistId → SS_PICKLIST.picklistId
itemId → item.id
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

### TABLE: SS_PICKLISTITEM

COLUMNS:
picklistItemId (PK)
picklistId → SS_PICKLIST.picklistId
itemId → item.id
qty
allocatedQty
pickedQty
status
isDeleted
cd
ud
USAGE: Line-item breakdown of materials requested per picklist.

### TABLE: SS_PICKLISTSTAGEMAP

COLUMNS:
stageMapId (PK)
picklistId → SS_PICKLIST.picklistId
itemId → item.id
stageId
stageCode
status
isDeleted
cd
ud
USAGE: Maps picklist items to their assigned picking stages.

### TABLE: SS_PIVALLOCATION

COLUMNS:
allocationId (PK)
picklistId → SS_PICKLIST.picklistId
itemId → item.id
qty
allocatedQty
status
isDeleted
cd
ud
USAGE: PIV-level allocation records linked to picklists and items.

### TABLE: SS_DOCUMENTTR

COLUMNS:
transactionRefId (PK)
documentTypeId → SS_DOCUMENT.documentId
itemId → item.id
qty
transactionType
status
cd
ud
USAGE: Document transaction reference records linking document types and items.

### TABLE: pickuplist

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

### TABLE: pickupListMapping

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

### TABLE: SS_SUPERSEDEFEFOMAPPING

COLUMNS:
supersedaFefoMapId (PK)
picklistId → SS_PICKLIST.picklistId
reason
userId → user.userId
isDeleted
cd
ud
cdBy
udBy

## DOMAIN CORE RELATIONSHIPS & JOINS (Picklist):

- `SS_PICKLIST.picklistId → SS_PICKLISTVIEW.picklistId`
- `SS_PICKLIST.picklistId → SS_PICKLISTITEM.picklistId`
- `SS_PICKLIST.picklistId → SS_PICKLISTSTAGEMAP.picklistId`
- `SS_PICKLIST.picklistId → SS_PIVALLOCATION.picklistId`
- `SS_PICKLIST.picklistId → SS_SULOCATION.picklistId`
- `SS_PICKLIST.picklistId → SS_SUPERSEDEFEFOMAPPING.picklistId`
- `SS_PICKLISTVIEW.picklistViewId → SS_SUIDCHARGINGMAPPING.picklistViewId`
- `item.id → SS_DOCUMENTTR.itemId`
- `item.id → SS_PICKLISTITEM.itemId`
- `item.id → SS_PICKLISTSTAGEMAP.itemId`
- `item.id → SS_PICKLISTVIEW.itemId`
- `item.id → SS_PIVALLOCATION.itemId`
- `SS_DOCUMENT.documentId → SS_DOCUMENTTR.documentTypeId`
- `SS_DOCUMENT.documentId → SS_PICKLIST.documentTypeId`
- `SS_MVT.mvtId → SS_PICKLIST.mvtId`
- `SS_TRANSACTIONM.transactionId → SS_PICKLIST.transactionId`
- `pivHeaders.id → SS_PICKLIST.pivHeaderId`
- `pivphases.id → SS_PICKLIST.pivPhaseId`
- `SS_PICKLIST.pivPhaseId → pivphases.id`
- `pickuplist.pickupListCode → pickuplistmapping.pickupListCode`
- `SS_PICKLIST.assignedUser → user.userId`
- `pickuplistmapping.sku → store.sku` OR `pickuplistmapping.sku → SS_SULOCATION.suid` (polymorphic SUID/SKU link)
- `pickuplist.documentNumber = pivphases.poNumber AND pickuplist.lineNumber = pivphases.phaseNumber AND pickuplist.srNo = pivphases.srNo`

## QUERY PATTERNS (PICKLIST):

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

OPEN SS PICKLISTS:
```SQL
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
```SQL

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

PICKLIST OUT OF UPPER / LOWER TOLERANCE LIMITS:
```SQL
SELECT
  pl.picklistCode,
  pli.qty,
  pp.upperLimit,
  pp.lowerLimit,
  pli.pickedQty
FROM SS_PICKLIST pl
INNER JOIN SS_PICKLISTITEM pli ON pli.picklistId = pl.picklistId
INNER JOIN pivPhases pp ON pp.id = pl.pivPhaseId
WHERE pli.pickedQty > 0
  AND (
    pli.pickedQty > pp.upperLimit
    OR pli.pickedQty < pp.lowerLimit
  )
  AND pl.cd >= NOW() - INTERVAL 5 DAY;
  ```

PICKED SUIDS AGAINST PICKLIST:
```SQL
SELECT
  plv.suid
FROM SS_PICKLIST pl
INNER JOIN SS_PICKLISTVIEW plv ON plv.picklistId = pl.picklistId
WHERE pl.picklistCode = '{picklistCode}';
```

---

# DOMAIN: 2. Inventory, Store & Stock Management

TYPE: schema_domain
INTENT: Track raw material master data, warehouse inventory ledger balances, SUID storage units, and physical storage bin structures.
TARGET TABLES: item, store, SS_SULOCATION, location, SS_LOCATION, warehouse, SS_WAREHOUSE, SS_WHLOCCMAP, SS_WHTYPEMAP, SS_ITEMCATEGORY, SS_ITEMCATEGORYMAP, SS_RELATIONALALLLTYPE, ss_relationalLocType, SS_ITEMLOCACNMAP, ss_itemMinMaxAndSectionMap, sapStockStatus, pivallocation
DESCRIPTION: Comprehensive inventory and storage management rules to handle stock availability, bin mappings, and plant layouts.

### TABLE: item
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

### TABLE: store
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
userId → user.userId
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

### TABLE: SS_SULOCATION
COLUMNS:
suidId (PK)
suid (UNIQUE)
skuId → store.id
qty
packSize
locationId → SS_LOCATION.locationId
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

### TABLE: location
COLUMNS:
id (PK)
locationName
warehouseId → warehouse.id
zoneId
isEmpty
isDeleted
cd
ud
USAGE: Legacy physical warehouse storage bin definitions.

### TABLE: SS_LOCATION
COLUMNS:
locationId (PK)
locationCode (UNIQUE)
locationName
parentId
parentCode
isLocation
rltId → SS_RELATIONALALLLTYPE.rltId
status
isEmpty
isDeleted
cd
ud
USAGE: Smart storage location hierarchy entity.

### TABLE: warehouse
COLUMNS:
id (PK)
warehouseCode (UNIQUE)
warehouseName
plant
isDeleted
cd
ud
USAGE: Physical warehouse facility definitions.

### TABLE: SS_WAREHOUSE
COLUMNS:
warehouseId (PK)
warehouseCode (UNIQUE)
warehouseName
plantCode
status
isDeleted
cd
ud
USAGE: Smart storage warehouse definitions.

### TABLE: ss_whlocmap
COLUMNS:
id (PK)
warehouseId → SS_WAREHOUSE.warehouseId
locationId → SS_LOCATION.locationId
isDeleted
cd
ud
USAGE: Mapping table linking warehouses to location hierarchies.

### TABLE: SS_WHTYPEMAP
COLUMNS:
id (PK)
warehouseId → SS_WAREHOUSE.warehouseId
typeId
isDeleted
cd
ud
USAGE: Warehouse type classification mapping table.

### TABLE: SS_ITEMCATEGORY
COLUMNS:
categoryId (PK)
categoryCode (UNIQUE)
categoryName
description
cd
USAGE: Master item category definitions.

### TABLE: SS_RELATIONALALLLTYPE
COLUMNS:
rltId (PK)
rltCode (UNIQUE)
rltName
description
cd
USAGE: Relation allocation type master definitions.

### TABLE: SS_ITEMLOCACNMAP
COLUMNS:
id (PK)
itemId → item.id
locationId → SS_LOCATION.locationId
isDeleted
cd
USAGE: Item to location association mapping table.

### TABLE: SS_ITEMCATEGORYMAP
COLUMNS:
id (PK)
itemId → item.id
categoryId → SS_ITEMCATEGORY.categoryId
isDeleted
cd
USAGE: Maps items to their assigned item categories.

### TABLE: ss_itemMinMaxAndSectionMap
COLUMNS:
id (PK)
itemId → item.id
sectionId → SS_LOCATION.locationId
rltId → ss_relationalLocType.rltId
minQty
maxQty
cd
ud
USAGE: Defines min/max stock thresholds for items per storage section.

### TABLE: sapStockStatus
COLUMNS:
id (PK)
itemId → item.id
stockStatus
plant
cd
ud
USAGE: SAP-synchronized stock status records per item.

### TABLE: ss_relationalLocType
COLUMNS:
rltId (PK)
rltCode (UNIQUE)
rltName
description
cd
USAGE: Relational location type master used to classify location hierarchies and item-section mappings.

### TABLE: SS_WHRLTMAP
COLUMNS:
id (PK)
warehouseId → SS_WAREHOUSE.warehouseId
rltId
isDeleted
cd
ud
USAGE: Maps warehouses to their relational location types.

## DOMAIN CORE RELATIONSHIPS & JOINS (Inventory):

- `item.materialCode → store.materialCode`

- `item.id → SS_ITEMCATEGORYMAP.itemId`

- `item.id → sapStockStatus.itemId`

- `item.id → ss_itemMinMaxAndSectionMap.itemId`

- `store.id → SS_SULOCATION.skuId`

- `warehouse.id → location.warehouseId`

- `SS_WAREHOUSE.warehouseId → SS_WHLOCCMAP.warehouseId`

- `SS_WAREHOUSE.warehouseId → SS_WHRLTMAP.warehouseId`

- `SS_LOCATION.locationId → SS_WHLOCCMAP.locationId`

- `SS_LOCATION.locationId → SS_SULOCATION.locationId`

- `SS_LOCATION.locationId → ss_itemMinMaxAndSectionMap.sectionId`

- `SS_LOCATION.rltId → SS_RELATIONALALLLTYPE.rltId`

- `SS_ITEMCATEGORY.categoryId → SS_ITEMCATEGORYMAP.categoryId`

- `ss_relationalLocType.rltId → ss_itemMinMaxAndSectionMap.rltId`

- `SS_ITEMLOCACNMAP.itemId → item.id`

- `SS_ITEMLOCACNMAP.locationId → SS_LOCATION.locationId`

## QUERY PATTERNS (INVENTORY):

TOTAL STOCK BY MATERIAL:
```SQL
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
PELLETIZED BUT NOT PUTAWAY SKUS:
```SQL

SELECT sku 
FROM store 
WHERE palletId IS NOT NULL 
  AND isPutaway = 0;
```
STORING LOCATION WISE TOTAL QUANTITY:

```SQL
SELECT
  materialCode,
  storingLocation,
  SUM(totalQty) AS totalQty
FROM store
WHERE materialCode = '{materialCode}'
  AND isPutaway = 1
GROUP BY materialCode, storingLocation;
```
EXPIRING GRNS WITHIN NEXT N DAYS:

```SQL
SELECT DISTINCT 
  grnNumber, 
  grnLineNumber
FROM store
WHERE shelfLife >= NOW()
  AND shelfLife <= NOW() + INTERVAL 5 DAY;
```

### DOMAIN: 3. Production Orders & PIV Management
TYPE: schema_domain
INTENT: Handle shop-floor manufacturing process orders, batch schedules, production phase definitions, and material issuance slips.
TARGET TABLES: pivHeaders, pivphases, pivmaterialissueslip, pivallocation
DESCRIPTION: Covers process order scheduling and allocation details linked via production order numbers (poNumber).

### TABLE: pivHeaders
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

### TABLE: pivPhases
COLUMNS:
id (PK)
poNumber → pivHeaders.poNumber
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

STATUS:
0 = Material Issuance
1 = Material Issuance
2 = Store Issuance
3 = Store Issuance
4 = Production Allocation
5 = Production Process

### TABLE: pivMaterialIssueSlip
COLUMNS:
id (PK)
poNumber → pivHeaders.poNumber
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

### TABLE: pivAllocation
COLUMNS:
id (PK)
documentType
documentNumber → pivHeaders.poNumber
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
assignedUser → user.userId
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

### DOMAIN CORE RELATIONSHIPS & JOINS (Production):

- `pivHeaders.poNumber → pivallocation.documentNumber`

- `pivHeaders.poNumber → pivphases.poNumber`

- `pivHeaders.poNumber → pivmaterialissueslip.poNumber`

- `pickuplist.documentNumber → pivHeaders.poNumber`

- `pivHeaders.id → SS_PICKLIST.pivHeaderId`

- `pivphases.id → SS_PICKLIST.pivPhaseId`

### QUERY PATTERNS (PRODUCTION / PIV):
## PIV PO ALLOCATION DETAILS:

```SQL
SELECT
  ph.poNumber,
  ph.finalMaterialCode,
  ph.batchNumber,
  pa.materialCode,
  pa.qty,
  pa.actualWeight,
  pa.status
FROM pivHeaders ph
JOIN pivallocation pa ON ph.poNumber = pa.documentNumber
WHERE ph.poNumber = '{poNumber}'
  AND pa.isDeleted = 0;
``` 
AVAILABLE FOR STORE ISSUANCE:

```SQL
SELECT
  ph.poNumber,
  pp.phaseNumber,
  pp.srNo,
  pp.materialCode
FROM pivPhases pp
INNER JOIN pivHeaders ph ON ph.poNumber = pp.poNumber AND ph.isPoClosed = 0
WHERE pp.status = 3;
```
PICKLISTS ALLOCATED IN RECENT HOURS:

```SQL
SELECT
  pl.picklistCode
FROM SS_PICKLIST pl
INNER JOIN SS_PIVALLOCATION pa ON pa.picklistId = pl.picklistId
INNER JOIN pivPhases pp ON pp.id = pl.pivPhaseId
WHERE pp.status = 5
  AND pa.cd >= NOW() - INTERVAL 8 HOUR;
```
# DOMAIN: 4. Material Movement & Transfers

TYPE: schema_domain
INTENT: Track inter-location material transfers, movement document headers, line items, movement pickup lists, SUID mappings, and document-movement type cross-references.
TARGET TABLES: movementheaders, movementlineitems, movementpickuplist, movementsuidmapping, movementtypes, ss_mvt, SS_DOCUMENT, SS_DOCMVTMAP
DESCRIPTION: Manages material movement lifecycles and document-based transfers across warehouse locations.

### TABLE: movementHeaders
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

### TABLE: movementLineItems
COLUMNS:
id (PK)
plant
materialCode
documentNumber → movementheaders.documentNumber
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

### TABLE: movementPickupList
COLUMNS:
id (PK)
plant
pickupListCode (UNIQUE)
movementType
tCode
documentNumber → movementheaders.documentNumber
lineNumber
materialCode
qty
uom
source
destination
status
assignedUser → user.userId
cd
movementStartTime
movementEndTime
expiryDate
USAGE: Pickup lists generated specifically for material transfers.

### TABLE: movementSuidMapping
COLUMNS:
id (PK)
documentNumber → movementheaders.documentNumber
pickupListCode → movementpickuplist.pickupListCode
materialCode
suId → ss_sulocation.suid
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

### TABLE: movementTypes
COLUMNS:
id (PK)
movementTypeCode (UNIQUE)
movementTypeName
description
cd
USAGE: Reference table defining movement type classifications.

### TABLE: SS_MVT
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

### TABLE: SS_DOCUMENT
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

### TABLE: SS_DOCMVTMAP
COLUMNS:
id (PK)
documentId → SS_DOCUMENT.documentId
mvtId → SS_MVT.mvtId
isDeleted
cd
ud
USAGE: Mapping table linking document types to allowed movement types.

## DOMAIN CORE RELATIONSHIPS & JOINS (Movement):
- `movementheaders.documentNumber → movementlineitems.documentNumber`

- `movementlineitems.documentNumber → movementpickuplist.documentNumber`

- `movementpickuplist.pickupListCode → movementsuidmapping.pickupListCode`

- `SS_DOCUMENT.documentId → SS_DOCMVTMAP.documentId`

- `SS_MVT.mvtId → SS_DOCMVTMAP.mvtId`

- `SS_MVT.mvtId → SS_PICKLIST.mvtId`

# DOMAIN: 5. Roles, Permissions & Assets

TYPE: schema_domain
INTENT: Manage user roles, access control modules, physical pallets, asset records, network printers, quality inspector credentials, resource zone mappings, and approval workflows.
TARGET TABLES: accesses, action, submodules, department, qualityinspector, assetmaster, palletBinMapping, pallet, tempassetmapping, resource, SS_RESOURCEZONEMAPPING, printer, rejmaterialdetails, revalidation, updateqistatuslog, reqtypes, approvalRequests, operationMaster, operationTimeMapping, SS_SUIDCHARGINGMAPPING
DESCRIPTION: Handles administrative security permissions, plant assets, resource-zone mappings, operation time planning, approval workflows, and quality inspection logging tables.

### TABLE: accesses
COLUMNS:
id (PK)
roleId
subModuleId
actionId
cd
USAGE: Role-based access permissions mapping.

### TABLE: action
COLUMNS:
actionId (PK)
actionName
subModuleId → submodules.subModuleId
cd
USAGE: System action definitions linked to submodules.

### TABLE: submodules
COLUMNS:
subModuleId (PK)
subModuleName
moduleId
cd
USAGE: System feature sub-modules.

### TABLE: department
COLUMNS:
id (PK)
departmentName
cd
USAGE: Plant organizational department list.

### TABLE: QualityInspector
COLUMNS:
id (PK)
employeeId (UNIQUE)
Name
userName (UNIQUE)
email
role
cd
USAGE: Authorized quality inspector credentials and profiles.

### TABLE: rejMaterialDetails
COLUMNS:
id (PK)
materialCode
batchNumber
rejectedQty
reason
inspectorId → qualityinspector.employeeId
cd
USAGE: Logs of materials rejected during quality inspection.

### TABLE: revalidation
COLUMNS:
id (PK)
skuId → store.id
materialCode
batchNumber
status
revalidatedDate
inspectorId
cd
USAGE: Material shelf-life and quality revalidation logs.

### TABLE: updateQIStatusLog
COLUMNS:
id (PK)
skuId → store.id
oldStatus
newStatus
updatedBy
cd
USAGE: Audit trail for quality inspector status updates.

### TABLE: reqTypes
COLUMNS:
reqTypeId (PK)
typeCode (UNIQUE)
typeName
description
cd
USAGE: Request type classification definitions.

### TABLE: approvalRequests
COLUMNS:
id (PK)
reqTypeId → reqtypes.reqTypeId
requestData
status
requestedBy
approvedBy
cd
ud
USAGE: Approval workflow requests categorized by request type.

### TABLE: assetMaster
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

### TABLE: palletBinMapping
COLUMNS:
id (PK)
binPalletId → assetmaster.id
binAId → assetmaster.id
binBId → assetmaster.id
binCId → assetmaster.id
binDId → assetmaster.id
cd
ud
USAGE: Maps pallet-level bins (A/B/C/D) to physical asset records.

### TABLE: pallet
COLUMNS:
palletId (PK)
palletCode (UNIQUE)
capacity
status
isDeleted
cd
ud
USAGE: Physical storage pallet inventory.

### TABLE: tempAssetMapping
COLUMNS:
id (PK)
tempAssetId
realAssetId
suid
cd
USAGE: Temporary asset to permanent asset mapping ledger.

### TABLE: resource
COLUMNS:
id (PK)
resourceCode (UNIQUE)
resourceName
plant
status
cd
USAGE: Machine, equipment, and work-center resources.

### TABLE: SS_RESOURCEZONEMAPPING
COLUMNS:
id (PK)
resourceId → resource.id
zoneId
zoneCode
status
isDeleted
cd
ud
USAGE: Maps resources (machines/work-centers) to warehouse zones.

### TABLE: operationMaster
COLUMNS:
opId (PK)
opCode (UNIQUE)
opName
description
status
cd
USAGE: Master list of plant operations and processes.

### TABLE: operationTimeMapping
COLUMNS:
id (PK)
opId → operationMaster.opId
standardTime
uom
plant
cd
ud
USAGE: Standard time allocations per operation for scheduling and capacity planning.

### TABLE: SS_SUIDCHARGINGMAPPING
COLUMNS:
id (PK)
picklistViewId → SS_PICKLISTVIEW.picklistViewId
chargedQty
chargedStatus
chargedTime
cd
ud
USAGE: Tracks SUID charging events linked to picklist view line items.

### TABLE: printer
COLUMNS:
id (PK)
printerName
ipAddress
plant
isDefault
cd
USAGE: Network barcode and document printer configurations.

## DOMAIN CORE RELATIONSHIPS & JOINS (Assets):
- `store.palletId → assetmaster.id`

- `store.palletId → pallet.palletId`

- `action.subModuleId → submodules.subModuleId`

- `assetmaster.id → palletBinMapping.binPalletId`

- `assetmaster.id → palletBinMapping.binAId`

- `assetmaster.id → palletBinMapping.binBId`

- `assetmaster.id → palletBinMapping.binCId`

- `assetmaster.id → palletBinMapping.binDId`

- `resource.id → SS_RESOURCEZONEMAPPING.resourceId`

- `reqtypes.reqTypeId → approvalRequests.reqTypeId`

- `operationMaster.opId → operationTimeMapping.opId`

- `SS_PICKLISTVIEW.picklistViewId → SS_SUIDCHARGINGMAPPING.picklistViewId`

# DOMAIN: 6. Filling & Weight Operations

TYPE: schema_domain
INTENT: Record intermediate filling processes, production filling quantities, batch balances, and manual stainer scale logs.
TARGET TABLES: intermediatefilling, intermediatefillinggrn, productionfilling, stainersmanualweightlogs, gatewaylogs
DESCRIPTION: Manages shop-floor filling operations and weight verification logs.

### TABLE: intermediateFilling
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

### TABLE: intermediateFillingGrn
COLUMNS:
id (PK)
grnNumber
poNumber
materialCode
batchNumber
totalQty
cd
USAGE: GRN records for intermediate filled stock.

### TABLE: productionFilling
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

### TABLE: stainersManualWeightlogs
COLUMNS:
id (PK)
uId
weight
userId → user.userId
scannedOfficer
cd
USAGE: Manual stainer scale weighing logs.

### TABLE: gatewaylogs
COLUMNS:
id (PK)
topic
GrossWeight
NetWeight
TareWeight
cd
USAGE: Hardware weighbridge MQTT/Gateway weight events.

## DOMAIN CORE RELATIONSHIPS & JOINS (Filling & Weights):
- `intermediatefilling.materialCode → item.materialCode`

- `productionfilling.pickupListCode → pickuplist.pickupListCode`

- `stainersmanualweightlogs.userId → user.userId`

# DOMAIN: 7. Global Rules, Constraints & Semantic Mappings (always on)

TYPE: global_rule
INTENT: Define global constraints, business term mappings, and natural language intent patterns to ensure precise query generation across all operations.
TARGET TABLES: none
DESCRIPTION: Universal rulebook outlining software generation standards, soft-delete rules, and semantic column mappings.

### BUSINESS TERM MAPPING:
- "material" / "item" → item.materialCode

- "sku" / "store inventory" → store.sku

- "stock" / "available inventory" → store.totalQty / store.actualQty

- "suid" → SS_SULOCATION.suid

- "location" / "bin" → location.locationName / SS_LOCATION.locationId

- "warehouse" → warehouse.warehouseCode / SS_WAREHOUSE.warehouseCode

- "picklist" → pickuplist.pickupListCode / SS_PICKLIST.picklistCode

- "piv order" / "process order" → pivHeaders.poNumber / pivallocation.pickupListCode

- "pallet" → assetmaster.assetId / store.palletId / pallet.palletId

- "movement" → movementheaders / movementpickuplist / movementlineitems

- "grn" → store.grnNumber

- "palletized stock" / "pelletize" → store.palletId IS NOT NULL

- "putaway done" / "stored inventory" → store.isPutaway = 1

- "not putaway" → store.isPutaway = 0

- "picked" → pickupListMapping.isPicked = 1 OR SS_PICKLISTITEM.pickedQty > 0

- "tolerance limits" / "upper limit" / "lower limit" → pivPhases.upperLimit, pivPhases.lowerLimit

- "allocation time" / "allocated in last N hours" → SS_PIVALLOCATION.cd

### INTENT MAPPING & LOGIC:
- "item stock in store" → item + store

- "open pickup lists" → pickuplist WHERE status IN (0, 1, 2) OR SS_PICKLIST WHERE status IN (0, 1, 2, 3, 4)

- "completed picklists" → SS_PICKLIST WHERE status = 5

- "po batch details" → pivHeaders

- "piv order allocation" → pivHeaders + pivallocation

- "piv production phases" → pivHeaders + pivphases

- "available for store issuance" → pivPhases WHERE status IN (2, 3) (or status = 3) AND pivHeaders.isPoClosed = 0

- "material movement by document" → movementheaders + movementlineitems

- "expiration date" / "expiry date" → store.shelfLife (already a DATETIME/DATE column, do NOT calculate via DATE_ADD)

- "expiring in next N days" → store.shelfLife >= NOW() AND store.shelfLife <= NOW() + INTERVAL N DAY

- "pelletize but not putaway" → store WHERE palletId IS NOT NULL AND isPutaway = 0

- "storing location wise stock" → store WHERE isPutaway = 1 GROUP BY materialCode, storingLocation

- "picked suid against picklist" → pickuplist + pickuplistmapping (WHERE isPicked = 1) OR SS_PICKLIST + SS_PICKLISTVIEW

- "picked out of tolerance limits" → SS_PICKLIST + SS_PICKLISTITEM + pivPhases (pli.pickedQty > pp.upperLimit OR pli.pickedQty < pp.lowerLimit)

- "picklists allocated recently" → SS_PICKLIST + SS_PIVALLOCATION + pivPhases (WHERE pa.cd >= NOW() - INTERVAL N HOUR)

### SPECIAL RULES & CONSTRAINTS:
- **formatting**: Present non-empty SQL execution results in a clean Markdown table with business-friendly Title Case column headers (e.g., convert cd to Created Date). Include a brief introductory summary sentence. If 0 rows are returned, provide a clear message (e.g., "No matching records found") instead of rendering an empty table.

- **Soft Delete Rule**: Always filter isDeleted = 0 (or isDeleted = '0') for tables containing the isDeleted column.

- **SQL Dialect**: Target MySQL syntax (Use LIMIT instead of TOP).

- **Join Integrity**: Follow defined joins strictly. Do NOT assume missing relationships.

- **Keywords**: Always wrap table names in backticks (e.g., user, store, location, action, resource) to avoid MySQL syntax errors.

- **Sorting (Latest/Recent)**: Always sort by cd DESC (unless filtering completed records where ud DESC applies for completion date).

- **Multi-Value Filters**: ALWAYS use IN (...) clause for multiple filter values (e.g., WHERE materialCode IN ('MAT01', 'MAT02')).

- **User Resolution**: pickuplist.assignedUser → user.userId or user.userName; Return user.name, user.userName.