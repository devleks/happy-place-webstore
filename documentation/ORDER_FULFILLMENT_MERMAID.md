# Order Fulfillment Workflow - Mermaid Diagrams

**Interactive visual diagrams of the complete fulfillment process**

---

## 🎯 **COMPLETE WORKFLOW - SEQUENCE DIAGRAM**

```mermaid
sequenceDiagram
    participant C as 👤 Customer
    participant O as 📦 Order System
    participant A as 👨‍💼 Admin/Manager
    participant P as 📦 Packer
    participant S as 🚚 Shipper
    participant D as 🚛 Carrier

    Note over C,D: PHASE 1: ORDER CREATION
    C->>O: Place order on website
    O->>O: Create order (status: pending)
    O->>C: Order confirmation
    C->>O: Complete payment
    O->>O: Update status: processing
    O->>C: Payment confirmation

    Note over C,D: PHASE 2: ADMIN ASSIGNMENT
    A->>O: View orders (Admin Portal)
    O->>A: Show processing orders
    A->>O: Click assign (👤 icon)
    O->>A: Show assignment modal
    A->>O: Select Packer (ID: 21)
    O->>O: Create assignment (status: pending)
    O->>P: Notify packer (add to queue)
    O->>A: Assignment success

    Note over C,D: PHASE 3: PACKER WORKFLOW
    P->>O: Login to Employee Portal
    O->>P: Show Packing Station
    P->>O: View packing queue
    O->>P: Show assigned orders
    P->>O: Click "Start Packing"
    O->>O: Update assignment: in_progress
    O->>P: Order moved to "In Progress"
    
    Note over P: Physical Tasks:<br/>- Retrieve items<br/>- Verify order<br/>- Pack items<br/>- Seal box<br/>- Attach slip
    
    P->>O: Click "Complete Packing"
    O->>P: Show completion modal
    P->>O: Submit notes
    O->>O: Update assignment: completed
    O->>O: Update order: packed
    O->>O: Create shipper assignment
    O->>S: Add to shipping queue
    O->>P: Remove from packer queue

    Note over C,D: PHASE 4: SHIPPER WORKFLOW
    S->>O: Login to Employee Portal
    O->>S: Show Shipping Station
    S->>O: View shipping queue
    O->>S: Show packed orders
    S->>O: Click "Start Shipping"
    O->>O: Update assignment: in_progress
    O->>S: Order moved to "In Progress"
    
    Note over S: Physical Tasks:<br/>- Retrieve box<br/>- Weigh package<br/>- Generate label<br/>- Scan barcode<br/>- Stage for pickup
    
    S->>O: Click "Complete Shipping"
    O->>S: Show shipping modal
    S->>O: Submit tracking info
    O->>O: Update assignment: completed
    O->>O: Update order: shipped
    O->>C: Send tracking notification
    O->>S: Remove from shipper queue

    Note over C,D: PHASE 5: DELIVERY
    D->>O: Pickup package
    D->>O: Scan at origin
    D->>O: In transit updates
    D->>O: Out for delivery
    D->>C: Deliver package
    O->>O: Update order: delivered
    O->>C: Delivery confirmation
```

---

## 🔄 **STATE MACHINE - ORDER STATUS**

```mermaid
stateDiagram-v2
    [*] --> Pending: Customer places order
    Pending --> Processing: Payment completed
    Processing --> AssignedToPacking: Admin assigns to packer
    AssignedToPacking --> PackingInProgress: Packer starts
    PackingInProgress --> Packed: Packer completes
    Packed --> AssignedToShipping: Auto-assign to shipper
    AssignedToShipping --> ShippingInProgress: Shipper starts
    ShippingInProgress --> Shipped: Shipper completes
    Shipped --> Delivered: Carrier delivers
    Delivered --> [*]
    
    Processing --> Cancelled: Admin cancels
    Cancelled --> [*]
    
    note right of Pending
        Initial state
        Payment pending
    end note
    
    note right of PackingInProgress
        Packer is actively
        packing the order
    end note
    
    note right of Shipped
        Tracking number
        assigned
    end note
```

---

## 👥 **ACTOR INTERACTIONS - FLOWCHART**

```mermaid
flowchart TD
    Start([Order Created]) --> Payment{Payment<br/>Successful?}
    Payment -->|No| Failed([Order Failed])
    Payment -->|Yes| Processing[Order Status:<br/>Processing]
    
    Processing --> AdminView[Admin Views<br/>Orders Page]
    AdminView --> AdminSelect[Admin Selects<br/>Processing Order]
    AdminSelect --> AdminAssign[Admin Clicks<br/>Assign 👤 Icon]
    AdminAssign --> SelectPacker[Select Role: Packer<br/>Employee: John Packer]
    SelectPacker --> AssignDB[(Create Assignment<br/>in Database)]
    AssignDB --> PackerQueue[Add to<br/>Packer Queue]
    
    PackerQueue --> PackerLogin[Packer Logs In<br/>Employee Portal]
    PackerLogin --> PackerDash[Packing Station<br/>Dashboard]
    PackerDash --> PackerView[View Pending<br/>Orders]
    PackerView --> PackerStart{Packer Clicks<br/>Start Packing}
    PackerStart --> PackerProgress[Status:<br/>In Progress]
    PackerProgress --> PhysicalPack[Physical Packing:<br/>Retrieve, Verify,<br/>Pack, Seal]
    PhysicalPack --> PackerComplete{Packer Clicks<br/>Complete Packing}
    PackerComplete --> PackerNotes[Add Packing<br/>Notes]
    PackerNotes --> UpdatePacked[(Update Order:<br/>Packed)]
    UpdatePacked --> CreateShipper[(Auto-Create<br/>Shipper Assignment)]
    CreateShipper --> ShipperQueue[Add to<br/>Shipper Queue]
    
    ShipperQueue --> ShipperLogin[Shipper Logs In<br/>Employee Portal]
    ShipperLogin --> ShipperDash[Shipping Station<br/>Dashboard]
    ShipperDash --> ShipperView[View Packed<br/>Orders]
    ShipperView --> ShipperStart{Shipper Clicks<br/>Start Shipping}
    ShipperStart --> ShipperProgress[Status:<br/>In Progress]
    ShipperProgress --> PhysicalShip[Physical Shipping:<br/>Weigh, Label,<br/>Scan, Stage]
    PhysicalShip --> ShipperComplete{Shipper Clicks<br/>Complete Shipping}
    ShipperComplete --> ShipperTracking[Enter Tracking<br/>Number & Carrier]
    ShipperTracking --> UpdateShipped[(Update Order:<br/>Shipped)]
    UpdateShipped --> NotifyCustomer[Send Customer<br/>Notification]
    NotifyCustomer --> CarrierPickup[Carrier Picks Up<br/>Package]
    CarrierPickup --> InTransit[In Transit]
    InTransit --> Delivered([Delivered to<br/>Customer])
    
    style Start fill:#90EE90
    style Failed fill:#FFB6C1
    style Delivered fill:#87CEEB
    style AssignDB fill:#FFE4B5
    style UpdatePacked fill:#FFE4B5
    style CreateShipper fill:#FFE4B5
    style UpdateShipped fill:#FFE4B5
```

---

## 🗂️ **QUEUE MANAGEMENT - FLOWCHART**

```mermaid
flowchart LR
    subgraph AdminPortal[Admin Portal]
        A1[View Orders] --> A2[Select Order]
        A2 --> A3[Click Assign 👤]
        A3 --> A4[Choose Packer]
        A4 --> A5[Submit Assignment]
    end
    
    subgraph PackerQueue[Packer Queue]
        direction TB
        P1[Pending Tab] --> P2[In Progress Tab]
        P2 --> P3[Completed Tab]
        
        P1 -.->|Start Packing| P2
        P2 -.->|Complete| P3
    end
    
    subgraph ShipperQueue[Shipper Queue]
        direction TB
        S1[Pending Tab] --> S2[In Progress Tab]
        S2 --> S3[Completed Tab]
        
        S1 -.->|Start Shipping| S2
        S2 -.->|Complete| S3
    end
    
    A5 -->|Assignment Created| P1
    P3 -->|Auto-Assign| S1
    
    style AdminPortal fill:#E6F3FF
    style PackerQueue fill:#FFF4E6
    style ShipperQueue fill:#E6FFE6
```

---

## 🔐 **ROLE-BASED ACCESS - DIAGRAM**

```mermaid
graph TD
    subgraph Portals
        AP[Admin Portal<br/>:3001]
        EP[Employee Portal<br/>:3002]
    end
    
    subgraph Users
        Admin[👨‍💼 Admin]
        Manager[👨‍💼 Manager]
        Packer[📦 Packer]
        Shipper[🚚 Shipper]
        Cashier[💰 Cashier]
    end
    
    subgraph Features
        Orders[📋 Orders]
        Employees[👥 Employees]
        Inventory[📦 Inventory]
        PackQueue[📦 Packing Queue]
        ShipQueue[🚚 Shipping Queue]
        Reports[📊 Reports]
    end
    
    Admin --> AP
    Manager --> AP
    Packer --> EP
    Shipper --> EP
    Cashier --> EP
    
    AP --> Orders
    AP --> Employees
    AP --> Inventory
    AP --> Reports
    
    EP --> PackQueue
    EP --> ShipQueue
    
    Admin -.->|Full Access| Orders
    Admin -.->|Full Access| Employees
    Manager -.->|View/Assign| Orders
    Manager -.->|View Only| Employees
    
    Packer -.->|Process Only| PackQueue
    Shipper -.->|Process Only| ShipQueue
    
    style Admin fill:#FFE4E1
    style Manager fill:#FFE4E1
    style Packer fill:#E1FFE4
    style Shipper fill:#E1FFE4
    style AP fill:#FFE4B5
    style EP fill:#B5E4FF
```

---

## 📊 **DATABASE RELATIONSHIPS - ERD**

```mermaid
erDiagram
    ORDERS ||--o{ ORDER_ASSIGNMENTS : has
    ORDERS {
        int id PK
        string order_number
        int user_id FK
        string status
        decimal total
        string tracking_number
        string carrier
        datetime shipped_at
        datetime created_at
    }
    
    ORDER_ASSIGNMENTS {
        int id PK
        int order_id FK
        int employee_id FK
        string role
        string status
        datetime assigned_at
        datetime started_at
        datetime completed_at
        text notes
    }
    
    EMPLOYEES ||--o{ ORDER_ASSIGNMENTS : assigned_to
    EMPLOYEES {
        int id PK
        string full_name
        string email
        string role
        boolean is_active
    }
    
    ORDER_ASSIGNMENTS }o--|| ORDERS : belongs_to
    ORDER_ASSIGNMENTS }o--|| EMPLOYEES : assigned_to
```

---

## ⏱️ **TIMELINE - GANTT CHART**

```mermaid
gantt
    title Order Fulfillment Timeline
    dateFormat HH:mm
    axisFormat %H:%M
    
    section Customer
    Place Order           :done, c1, 10:00, 10:05
    Receive Tracking      :done, c2, 10:50, 10:51
    Receive Package       :crit, c3, 14:00, 14:05
    
    section Admin
    Review Order          :done, a1, 10:05, 10:08
    Assign to Packer      :done, a2, 10:08, 10:10
    
    section Packer
    View Queue            :done, p1, 10:10, 10:12
    Start Packing         :done, p2, 10:12, 10:13
    Physical Packing      :active, p3, 10:13, 10:28
    Complete Packing      :p4, 10:28, 10:30
    
    section Shipper
    View Queue            :s1, 10:30, 10:32
    Start Shipping        :s2, 10:32, 10:33
    Physical Shipping     :s3, 10:33, 10:48
    Complete Shipping     :s4, 10:48, 10:50
    
    section Carrier
    Pickup                :d1, 11:00, 11:15
    In Transit            :d2, 11:15, 14:00
    Delivery              :crit, d3, 14:00, 14:05
```

---

## 🎯 **DECISION TREE - ASSIGNMENT LOGIC**

```mermaid
flowchart TD
    Start([Order Status:<br/>Processing]) --> CheckStock{All Items<br/>In Stock?}
    
    CheckStock -->|No| NotifyAdmin[Notify Admin:<br/>Partial Stock]
    NotifyAdmin --> AdminDecision{Admin<br/>Decision}
    AdminDecision -->|Cancel| CancelOrder([Cancel Order])
    AdminDecision -->|Partial| PartialAssign[Assign Available<br/>Items]
    AdminDecision -->|Wait| WaitStock[Wait for<br/>Restock]
    
    CheckStock -->|Yes| CheckPacker{Packer<br/>Available?}
    CheckPacker -->|No| QueueOrder[Add to<br/>Pending Queue]
    QueueOrder --> WaitPacker[Wait for<br/>Packer]
    WaitPacker --> CheckPacker
    
    CheckPacker -->|Yes| AssignPacker[Assign to<br/>Packer]
    PartialAssign --> AssignPacker
    
    AssignPacker --> PackerQueue[Add to<br/>Packer Queue]
    PackerQueue --> PackerProcess[Packer<br/>Processes]
    PackerProcess --> PackComplete{Packing<br/>Complete?}
    
    PackComplete -->|Issues| ReportIssue[Report Issue<br/>to Admin]
    ReportIssue --> AdminResolve{Admin<br/>Resolves?}
    AdminResolve -->|Yes| PackComplete
    AdminResolve -->|No| CancelOrder
    
    PackComplete -->|Success| CheckShipper{Shipper<br/>Available?}
    CheckShipper -->|No| QueueShip[Add to<br/>Shipping Queue]
    QueueShip --> WaitShipper[Wait for<br/>Shipper]
    WaitShipper --> CheckShipper
    
    CheckShipper -->|Yes| AssignShipper[Assign to<br/>Shipper]
    AssignShipper --> ShipperQueue[Add to<br/>Shipper Queue]
    ShipperQueue --> ShipperProcess[Shipper<br/>Processes]
    ShipperProcess --> ShipComplete{Shipping<br/>Complete?}
    
    ShipComplete -->|Issues| ReportShipIssue[Report Issue<br/>to Admin]
    ReportShipIssue --> AdminResolveShip{Admin<br/>Resolves?}
    AdminResolveShip -->|Yes| ShipComplete
    AdminResolveShip -->|No| CancelOrder
    
    ShipComplete -->|Success| Shipped([Order<br/>Shipped])
    
    style Start fill:#90EE90
    style CancelOrder fill:#FFB6C1
    style Shipped fill:#87CEEB
    style AssignPacker fill:#FFE4B5
    style AssignShipper fill:#FFE4B5
```

---

## 🔄 **PACKER WORKFLOW - DETAILED**

```mermaid
flowchart TD
    Start([Packer Logs In]) --> Dashboard[Packing Station<br/>Dashboard]
    Dashboard --> ViewQueue[View Pending<br/>Orders Tab]
    ViewQueue --> SelectOrder{Select<br/>Order}
    
    SelectOrder --> OrderDetails[View Order<br/>Details]
    OrderDetails --> CheckItems{All Items<br/>Clear?}
    CheckItems -->|No| ContactAdmin[Contact Admin]
    ContactAdmin --> SelectOrder
    
    CheckItems -->|Yes| StartPacking[Click<br/>Start Packing]
    StartPacking --> UpdateStatus[(Update Status:<br/>In Progress)]
    UpdateStatus --> MoveTab[Move to<br/>In Progress Tab]
    
    MoveTab --> Physical[Physical Tasks]
    
    subgraph Physical[Physical Packing Process]
        direction TB
        T1[Retrieve Items<br/>from Inventory] --> T2[Verify Against<br/>Order]
        T2 --> T3[Check for<br/>Damage/Defects]
        T3 --> T4[Wrap Items<br/>Securely]
        T4 --> T5[Place in<br/>Shipping Box]
        T5 --> T6[Add Packing<br/>Materials]
        T6 --> T7[Seal Box<br/>with Tape]
        T7 --> T8[Attach Packing<br/>Slip]
    end
    
    Physical --> QualityCheck{Quality<br/>Check Pass?}
    QualityCheck -->|No| Repack[Repack<br/>Order]
    Repack --> Physical
    
    QualityCheck -->|Yes| Complete[Click<br/>Complete Packing]
    Complete --> NotesModal[Add Packing<br/>Notes Modal]
    NotesModal --> EnterNotes[Enter Notes:<br/>Condition, Issues]
    EnterNotes --> Submit[Click<br/>Submit]
    Submit --> UpdateComplete[(Update Status:<br/>Completed)]
    UpdateComplete --> RemoveQueue[Remove from<br/>Packer Queue]
    RemoveQueue --> CreateShipper[(Create Shipper<br/>Assignment)]
    CreateShipper --> End([Order Ready<br/>for Shipping])
    
    style Start fill:#90EE90
    style End fill:#87CEEB
    style UpdateStatus fill:#FFE4B5
    style UpdateComplete fill:#FFE4B5
    style CreateShipper fill:#FFE4B5
    style Physical fill:#FFF4E6
```

---

## 🚚 **SHIPPER WORKFLOW - DETAILED**

```mermaid
flowchart TD
    Start([Shipper Logs In]) --> Dashboard[Shipping Station<br/>Dashboard]
    Dashboard --> ViewQueue[View Pending<br/>Orders Tab]
    ViewQueue --> SelectOrder{Select<br/>Packed Order}
    
    SelectOrder --> OrderDetails[View Order<br/>& Packing Info]
    OrderDetails --> VerifyPacking{Packing<br/>Verified?}
    VerifyPacking -->|Issues| ContactPacker[Contact Packer/<br/>Admin]
    ContactPacker --> SelectOrder
    
    VerifyPacking -->|OK| StartShipping[Click<br/>Start Shipping]
    StartShipping --> UpdateStatus[(Update Status:<br/>In Progress)]
    UpdateStatus --> MoveTab[Move to<br/>In Progress Tab]
    
    MoveTab --> Physical[Physical Tasks]
    
    subgraph Physical[Physical Shipping Process]
        direction TB
        S1[Retrieve Packed<br/>Box] --> S2[Verify Packing<br/>Slip]
        S2 --> S3[Weigh<br/>Package]
        S3 --> S4[Select Shipping<br/>Carrier]
        S4 --> S5[Generate Shipping<br/>Label]
        S5 --> S6[Print Label]
        S6 --> S7[Attach Label<br/>to Box]
        S7 --> S8[Scan Tracking<br/>Barcode]
        S8 --> S9[Stage for<br/>Carrier Pickup]
    end
    
    Physical --> LabelCheck{Label<br/>Correct?}
    LabelCheck -->|No| ReprintLabel[Reprint<br/>Label]
    ReprintLabel --> Physical
    
    LabelCheck -->|Yes| Complete[Click<br/>Complete Shipping]
    Complete --> ShippingModal[Shipping Details<br/>Modal]
    ShippingModal --> EnterTracking[Enter Tracking<br/>Number]
    EnterTracking --> SelectCarrier[Select Carrier:<br/>DHL, FedEx, etc.]
    SelectCarrier --> EnterNotes[Enter Shipping<br/>Notes]
    EnterNotes --> Submit[Click<br/>Submit]
    Submit --> UpdateComplete[(Update Status:<br/>Completed)]
    UpdateComplete --> UpdateOrder[(Update Order:<br/>Shipped)]
    UpdateOrder --> SaveTracking[(Save Tracking<br/>Info)]
    SaveTracking --> NotifyCustomer[Send Customer<br/>Notification]
    NotifyCustomer --> RemoveQueue[Remove from<br/>Shipper Queue]
    RemoveQueue --> End([Order<br/>Shipped])
    
    style Start fill:#90EE90
    style End fill:#87CEEB
    style UpdateStatus fill:#FFE4B5
    style UpdateComplete fill:#FFE4B5
    style UpdateOrder fill:#FFE4B5
    style SaveTracking fill:#FFE4B5
    style Physical fill:#E6FFE6
```

---

## 📱 **USER INTERFACE FLOW**

```mermaid
flowchart LR
    subgraph AdminUI[Admin Portal UI]
        A1[Login Page] --> A2[Dashboard]
        A2 --> A3[Orders List]
        A3 --> A4[Assignment Modal]
        A4 --> A3
    end
    
    subgraph PackerUI[Packer Portal UI]
        P1[Login Page] --> P2[Packing Station]
        P2 --> P3[Pending Tab]
        P2 --> P4[In Progress Tab]
        P2 --> P5[Completed Tab]
        P3 --> P6[Order Card]
        P6 --> P7[Start Modal]
        P7 --> P4
        P4 --> P8[Complete Modal]
        P8 --> P5
    end
    
    subgraph ShipperUI[Shipper Portal UI]
        S1[Login Page] --> S2[Shipping Station]
        S2 --> S3[Pending Tab]
        S2 --> S4[In Progress Tab]
        S2 --> S5[Completed Tab]
        S3 --> S6[Order Card]
        S6 --> S7[Start Modal]
        S7 --> S4
        S4 --> S8[Complete Modal]
        S8 --> S5
    end
    
    A4 -.->|Assignment| P3
    P5 -.->|Auto-Assign| S3
    
    style AdminUI fill:#E6F3FF
    style PackerUI fill:#FFF4E6
    style ShipperUI fill:#E6FFE6
```

---

## 🎯 **SUCCESS METRICS - PIE CHART**

```mermaid
pie title Order Fulfillment Status Distribution
    "Shipped" : 45
    "In Packing" : 15
    "In Shipping" : 10
    "Pending Assignment" : 20
    "Delivered" : 10
```

---

## 📈 **PERFORMANCE TIMELINE**

```mermaid
timeline
    title Order Fulfillment Journey
    section Order Placement
        10:00 : Customer places order
        10:02 : Payment processed
        10:05 : Order confirmed
    section Assignment
        10:08 : Admin reviews order
        10:10 : Assigned to packer
    section Packing
        10:12 : Packer starts
        10:15 : Items retrieved
        10:20 : Items packed
        10:28 : Packing complete
    section Shipping
        10:32 : Shipper starts
        10:35 : Label generated
        10:45 : Package staged
        10:50 : Shipping complete
    section Delivery
        11:00 : Carrier pickup
        13:00 : In transit
        14:00 : Delivered
```

---

**These Mermaid diagrams provide interactive, visual representations of the entire order fulfillment workflow!** 🎨

**To view these diagrams:**
1. Copy any diagram code
2. Paste into [Mermaid Live Editor](https://mermaid.live)
3. Or view in any Markdown viewer that supports Mermaid (GitHub, GitLab, VS Code with extension)
