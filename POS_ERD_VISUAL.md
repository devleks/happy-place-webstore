# 🏪 POS System - Visual ERD

## Entity Relationship Diagram

```mermaid
erDiagram
    EMPLOYEES ||--o{ POS_SHIFTS : "works"
    EMPLOYEES ||--o{ POS_TRANSACTIONS : "processes"
    EMPLOYEES ||--o{ POS_CASH_MOVEMENTS : "performs"
    
    STORE_LOCATIONS ||--o{ POS_SHIFTS : "hosts"
    STORE_LOCATIONS ||--o{ POS_TRANSACTIONS : "occurs_at"
    
    POS_SHIFTS ||--o{ POS_TRANSACTIONS : "contains"
    POS_SHIFTS ||--o{ POS_CASH_MOVEMENTS : "tracks"
    
    POS_TRANSACTIONS ||--o{ POS_TRANSACTION_ITEMS : "has"
    
    POS_TRANSACTION_ITEMS }o--|| PRODUCTS : "references"
    POS_TRANSACTION_ITEMS }o--|| PRODUCT_VARIANTS : "uses"
    POS_TRANSACTION_ITEMS }o--|| INVENTORY : "deducts_from"
    
    CUSTOMERS ||--o{ POS_TRANSACTIONS : "makes"
    
    EMPLOYEES {
        int id PK
        string first_name
        string last_name
        string email UK
        string password_hash
        string role "cashier/manager/admin"
        boolean is_active
        timestamp created_at
    }
    
    STORE_LOCATIONS {
        int id PK
        string name
        string address
        string city
        string phone
        boolean is_active
    }
    
    POS_SHIFTS {
        int id PK
        int employee_id FK
        int store_location_id FK
        string shift_number UK "YYYYMMDD-LOC1-EMP2-001"
        timestamp start_time
        timestamp end_time "NULL=open"
        decimal opening_float
        decimal closing_cash
        decimal expected_cash
        decimal variance "closing-expected"
        string status "open/closed"
        text notes
        timestamp created_at
        timestamp updated_at
    }
    
    POS_TRANSACTIONS {
        int id PK
        string transaction_number UK "POS-20251205-0001"
        int employee_id FK
        int shift_id FK
        int store_location_id FK
        int customer_id FK "NULLABLE"
        string payment_method "cash/mpesa/card"
        decimal subtotal
        decimal tax
        decimal total
        decimal cash_tendered
        decimal change_given
        string status "completed/voided"
        boolean receipt_printed
        boolean receipt_emailed
        timestamp voided_at
        int voided_by FK
        text void_reason
        timestamp created_at
        timestamp updated_at
    }
    
    POS_TRANSACTION_ITEMS {
        int id PK
        int transaction_id FK
        int product_id FK
        int variant_id FK
        int inventory_id FK
        int quantity
        decimal unit_price
        decimal total_price
        timestamp created_at
    }
    
    POS_CASH_MOVEMENTS {
        int id PK
        int shift_id FK "CASCADE"
        string movement_type "cash_in/cash_out/starting_float/closing_count"
        decimal amount
        text reason
        int performed_by FK
        timestamp created_at
    }
    
    CUSTOMERS {
        int id PK
        string email
        string first_name
        string last_name
        string phone
    }
    
    PRODUCTS {
        int id PK
        string name
        string sku
        decimal price
        decimal sale_price
    }
    
    PRODUCT_VARIANTS {
        int id PK
        int product_id FK
        string sku
        string size
        string color
        decimal price
    }
    
    INVENTORY {
        int id PK
        int variant_id FK
        int quantity
        int reserved
        int available
    }
```

---

## Simplified Flow Diagram

```mermaid
flowchart TB
    subgraph Login["🔐 Authentication"]
        E[Employee Login]
    end
    
    subgraph Shift["📅 Shift Management"]
        S1[Start Shift<br/>sp_start_shift]
        S2[Opening Float<br/>KSh 5,000]
        S3[Shift Active<br/>Status: OPEN]
    end
    
    subgraph Transaction["💰 Transaction Processing"]
        T1[Scan Products]
        T2[Add to Cart]
        T3[Select Payment]
        T4[Create Transaction<br/>sp_create_pos_transaction]
        T5[Deduct Inventory]
        T6[Print Receipt]
    end
    
    subgraph Cash["💵 Cash Management"]
        C1[Cash In/Out]
        C2[Log Movement]
    end
    
    subgraph Close["🔒 Shift Closure"]
        CL1[Count Cash]
        CL2[Close Shift<br/>sp_close_shift]
        CL3[Calculate Variance]
        CL4[Generate Report]
    end
    
    E --> S1
    S1 --> S2
    S2 --> S3
    S3 --> T1
    T1 --> T2
    T2 --> T3
    T3 --> T4
    T4 --> T5
    T5 --> T6
    T6 --> T1
    
    S3 --> C1
    C1 --> C2
    C2 --> S3
    
    S3 --> CL1
    CL1 --> CL2
    CL2 --> CL3
    CL3 --> CL4
    
    style E fill:#e1f5ff
    style S1 fill:#c8e6c9
    style T4 fill:#fff9c4
    style CL2 fill:#ffccbc
```

---

## Data Flow Sequence

```mermaid
sequenceDiagram
    participant C as Cashier
    participant POS as POS System
    participant DB as Database
    participant INV as Inventory Service
    
    Note over C,INV: 1. SHIFT START
    C->>POS: Login (email, password)
    POS->>DB: Verify credentials
    DB-->>POS: Employee authenticated
    
    C->>POS: Start Shift (opening_float: 5000)
    POS->>DB: sp_start_shift()
    DB->>DB: Create pos_shifts record
    DB->>DB: Log cash_movement (starting_float)
    DB-->>POS: shift_id: 10, shift_number: 20251205-LOC1-EMP2-001
    
    Note over C,INV: 2. TRANSACTION
    C->>POS: Scan product (variant_id: 1)
    POS->>DB: Get product details
    DB-->>POS: Product: Floral Maxi Dress, Price: 5149
    
    C->>POS: Add to cart (quantity: 2)
    C->>POS: Process payment (cash: 10000)
    
    POS->>DB: sp_create_pos_transaction()
    DB->>DB: Validate shift is open
    DB->>INV: Check inventory availability
    INV-->>DB: Available: 50 units
    DB->>DB: Create pos_transactions record
    DB->>DB: Create pos_transaction_items records
    DB->>INV: sp_deduct_inventory(variant_id: 1, qty: 2)
    INV->>INV: Update inventory.quantity -= 2
    DB-->>POS: Success! Transaction: POS-20251205-0001
    
    POS->>C: Print receipt (change: 702)
    
    Note over C,INV: 3. CASH MOVEMENT
    C->>POS: Cash Out (bank deposit: 5000)
    POS->>DB: Create cash_movement record
    DB-->>POS: Logged
    
    Note over C,INV: 4. SHIFT CLOSE
    C->>POS: Count cash (closing_cash: 5300)
    POS->>DB: sp_close_shift()
    DB->>DB: Calculate cash_sales from transactions
    DB->>DB: Sum cash_in and cash_out movements
    DB->>DB: expected_cash = opening + sales + in - out
    DB->>DB: variance = closing - expected
    DB->>DB: Update shift status = 'closed'
    DB-->>POS: Variance: +300 (OVER)
    
    POS->>C: Display shift summary
```

---

## Smart Shift Numbering

```mermaid
graph LR
    A[Shift Number] --> B[Date<br/>YYYYMMDD]
    A --> C[Location<br/>LOC1]
    A --> D[Employee<br/>EMP2]
    A --> E[Sequence<br/>001]
    
    B --> F[20251205-LOC1-EMP2-001]
    C --> F
    D --> F
    E --> F
    
    style F fill:#4CAF50,color:#fff
```

**Benefits:**
- 📅 **Date Filtering:** Easily find shifts by date
- 🏪 **Location Tracking:** Filter by store location
- 👤 **Employee Performance:** Track individual cashier metrics
- 🔢 **Sequence:** Identify shift order for the day

---

## Transaction States

```mermaid
stateDiagram-v2
    [*] --> Draft: Create Cart
    Draft --> Pending: Submit Payment
    Pending --> Completed: Payment Success
    Pending --> Failed: Payment Failed
    Completed --> Voided: Manager Void
    Failed --> [*]
    Voided --> [*]
    Completed --> [*]
    
    note right of Completed
        Inventory deducted
        Receipt printed
        Cash recorded
    end note
    
    note right of Voided
        Inventory restored
        Void reason logged
        Manager approval required
    end note
```

---

## Cash Reconciliation Formula

```mermaid
graph TD
    A[Opening Float<br/>KSh 5,000] --> B[+ Cash Sales<br/>KSh 10,298]
    B --> C[+ Cash In<br/>KSh 0]
    C --> D[- Cash Out<br/>KSh 0]
    D --> E[Expected Cash<br/>KSh 15,298]
    
    F[Closing Cash Count<br/>KSh 15,598] --> G{Compare}
    E --> G
    
    G -->|Difference| H[Variance<br/>+KSh 300 OVER]
    
    style A fill:#e3f2fd
    style E fill:#fff9c4
    style F fill:#ffccbc
    style H fill:#ffcdd2
```

**Variance Interpretation:**
- ✅ **Zero variance:** Perfect reconciliation
- ⚠️ **Positive variance (+300):** Cash OVER - Extra money in drawer
- ❌ **Negative variance (-300):** Cash SHORT - Missing money

---

## Stored Procedures Flow

```mermaid
graph TB
    subgraph sp_start_shift
        SS1[Check no open shift]
        SS2[Generate shift number]
        SS3[Create pos_shifts record]
        SS4[Log opening_float]
        SS1 --> SS2 --> SS3 --> SS4
    end
    
    subgraph sp_create_pos_transaction
        CT1[Validate shift is open]
        CT2[Check inventory]
        CT3[Calculate totals]
        CT4[Create transaction]
        CT5[Create items]
        CT6[Deduct inventory]
        CT1 --> CT2 --> CT3 --> CT4 --> CT5 --> CT6
    end
    
    subgraph sp_void_pos_transaction
        VT1[Check not already voided]
        VT2[Verify manager role]
        VT3[Restore inventory]
        VT4[Mark as voided]
        VT1 --> VT2 --> VT3 --> VT4
    end
    
    subgraph sp_close_shift
        CS1[Get shift details]
        CS2[Calculate cash sales]
        CS3[Sum cash movements]
        CS4[Calculate expected]
        CS5[Calculate variance]
        CS6[Update shift closed]
        CS1 --> CS2 --> CS3 --> CS4 --> CS5 --> CS6
    end
    
    style sp_start_shift fill:#c8e6c9
    style sp_create_pos_transaction fill:#fff9c4
    style sp_void_pos_transaction fill:#ffccbc
    style sp_close_shift fill:#e1bee7
```

---

## Index Strategy

```mermaid
graph LR
    subgraph Performance Indexes
        I1[pos_shifts.employee_id]
        I2[pos_shifts.status]
        I3[pos_transactions.shift_id]
        I4[pos_transactions.created_at]
        I5[pos_transaction_items.transaction_id]
        I6[pos_cash_movements.shift_id]
    end
    
    subgraph Unique Constraints
        U1[pos_shifts.shift_number]
        U2[pos_transactions.transaction_number]
    end
    
    subgraph Foreign Keys
        F1[All FK columns indexed]
    end
    
    style Performance fill:#4CAF50,color:#fff
    style Unique fill:#2196F3,color:#fff
    style Foreign fill:#FF9800,color:#fff
```

---

## View this diagram in your IDE

Most modern IDEs and GitHub support Mermaid rendering. If you're viewing this in:
- **VS Code:** Install "Markdown Preview Mermaid Support" extension
- **GitHub:** Diagrams render automatically
- **Online:** Copy to https://mermaid.live/

---

**Created:** December 5, 2025  
**Version:** 1.0  
**Database Schema:** 005_pos_enhancements.sql
