# Happy Place Boutique - Complete Database Schema
## E-Commerce Platform with GDPR Compliance

**Version:** 3.2 AMENDED
**Date:** November 23, 2025
**Author:** Development Team
**Status:** Ready for Final Approval

---

## Document Overview

This document presents the **final amended database schema** for Happy Place Boutique, incorporating:

✅ **Customer & Employee Separation** - Distinct tables for online shoppers vs system users
✅ **GDPR Compliance** - Right to be forgotten, consent management, audit trails
✅ **Optimized Category Hierarchy** - Using a Closure Table for high-performance querying
✅ **Normalized Product Variants** - Scalable management of sizes, colors, and SKUs
✅ **Expanded E-Commerce Features** - Promotions, Shipping, and Returns management
✅ **POS System** - Physical store transaction support
✅ **Inventory Management** - Unified stock tracking (online + physical store)
✅ **M-Pesa Integration** - Kenya mobile payment support
✅ **Data Retention** - Automatic anonymization policies

---

## Table of Contents

1. [Database Summary](#database-summary)
2. [Entity Relationship Diagram](#entity-relationship-diagram)
3. [Core Tables](#core-tables)
4. [E-Commerce Tables](#e-commerce-tables)
5. [POS & Store Tables](#pos--store-tables)
6. [GDPR Compliance Tables](#gdpr-compliance-tables)
7. [Complete Table List](#complete-table-list)
8. [Indexes & Performance](#indexes--performance)
9. [Migration Plan](#migration-plan)
10. [Review Checklist](#review-checklist)

---

## Database Summary

### Statistics

- **Total Tables:** 29
- **Core Business:** 13 tables
- **E-Commerce:** 13 tables
- **GDPR Compliance:** 3 tables
- **Total Columns:** ~300+
- **Foreign Keys:** 45+
- **Indexes:** 80+

### Table Categories

| Category | Tables | Purpose |
|----------|--------|---------|
| **User Management** | customers, employees, customer_addresses | Authentication & profiles |
| **Product Catalog** | categories, category_closure, products, product_variants, product_images, inventory | Product management, hierarchy, and normalization |
| **Shopping** | carts, cart_items, wishlists, wishlist_items | Customer shopping experience |
| **Orders** | orders, order_items, payments, returns, return_items | Order & returns processing |
| **Promotions** | promotions, order_promotions | Discount and coupon management |
| **Shipping** | shipping_methods | Shipping options and costs |
| **Reviews** | reviews | Customer feedback |
| **POS** | pos_transactions, pos_transaction_items, store_locations | Physical store sales |
| **GDPR** | gdpr_data_requests, gdpr_consent_log, data_access_log | Data privacy compliance |
| **Audit** | activity_logs | System activity tracking |

---

## Entity Relationship Diagram
*Diagram updated to include CATEGORY_CLOSURE table.*
```mermaid
erDiagram
    %% ... (previous relationships remain the same) ...

    %% Category Hierarchy
    CATEGORIES ||--o{ CATEGORIES : "has parent"
    CATEGORIES ||--o{ PRODUCTS : "contains"
    CATEGORIES ||--o{ CATEGORY_CLOSURE : "ancestor"
    CATEGORIES ||--o{ CATEGORY_CLOSURE : "descendant"

    CATEGORY_CLOSURE {
        int ancestor_id PK FK
        int descendant_id PK FK
        int depth
    }

    %% ... (rest of the diagram) ...
```
---

## Core Tables

### 1. CUSTOMERS ⭐ **(GDPR Compliant)**
*(No changes)*

### 2. CUSTOMER_ADDRESSES
*(No changes)*

### 3. EMPLOYEES
*(No changes)*

### 4. CATEGORIES (Amended for Closure Table)

**Purpose:** Product categorization with hierarchical support. The `parent_id` maintains the direct parent-child link, while the `category_closure` table provides high-performance querying of the entire hierarchy.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique category ID |
| name | VARCHAR(100) | UNIQUE, NOT NULL | Category name (e.g., "Women's", "Dresses") |
| slug | VARCHAR(100) | UNIQUE, NOT NULL | URL-friendly slug |
| description | TEXT | NULL | Category description |
| parent_id | INTEGER | FK→categories.id | Direct Parent category (Adjacency List) |
| is_active | BOOLEAN | DEFAULT TRUE | Visibility status |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation date |

---

### 5. CATEGORY_CLOSURE (New Table)

**Purpose:** Stores all ancestor-descendant paths for the category tree. This enables extremely fast queries for all products under a given parent category (e.g., all "Women's" clothing).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| ancestor_id | INTEGER | FK→categories.id, NOT NULL | The parent/ancestor category |
| descendant_id | INTEGER | FK→categories.id, NOT NULL | The child/descendant category |
| depth | INTEGER | NOT NULL | How many levels separate them (0 for self) |
| **PRIMARY KEY** | **(ancestor_id, descendant_id)**| | Composite primary key |

**Indexes:**
```sql
CREATE INDEX idx_category_closure_descendant ON category_closure(descendant_id);
```

---

### 6. PRODUCTS
*(Renumbered, no other changes)*

---

### 7. PRODUCT_VARIANTS
*(Renumbered, no other changes)*

---

### 8. PRODUCT_IMAGES
*(Renumbered, no other changes)*

---

### 9. INVENTORY
*(Renumbered, no other changes)*

---

## E-Commerce Tables
*(All tables from this section are renumbered accordingly, starting from #10)*

---
## POS & Store Tables
*(All tables from this section are renumbered accordingly)*

---
## GDPR Compliance Tables
*(All tables from this section are renumbered accordingly)*

---

## Complete Table List

### Summary: 29 Tables

| # | Table Name | Category |
|---|---|---|
| ... | ... | ... |
| 4 | categories | Catalog |
| 5 | **category_closure** | **Catalog** |
| 6 | products | Catalog |
| ... | ... | ... |
*(The rest of the table list is renumbered)*

---

## Migration Plan (Amended)

### Phase 1: Core Infrastructure (Amended)

1. **Create CUSTOMERS, CUSTOMER_ADDRESSES, EMPLOYEES tables.**
2. **Create STORE_LOCATIONS table.**
3. **Create CATEGORIES table.**
4. **Create CATEGORY_CLOSURE table.**
5. **Populate `categories` and `category_closure` with initial data (e.g., "Women's", "Maternity").**

### Phase 2: Product Catalog Normalization
*(No changes, just renumbered)*

### Phase 3: GDPR Compliance
*(No changes, just renumbered)*

### Phase 4: E-Commerce Features
*(No changes, just renumbered)*

### Phase 5: Returns, Reviews & POS
*(No changes, just renumbered)*

### Phase 6: Indexes & Optimization
*(No changes, just renumbered)*

---

## Review Checklist

### Architecture

- [x] **Optimized Category Hierarchy** - Implemented via Closure Table.
- [x] **Product Variant Normalization** - Implemented.
- [ ] **Customers vs Employees separation** - Approved?
- ... *(rest of checklist remains)*

---

**Document Status:** ✅ READY FOR FINAL APPROVAL
**Total Tables:** 29
**GDPR Compliant:** Yes
**Production Ready:** After approval and testing
