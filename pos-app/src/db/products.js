/**
 * Product Operations for IndexedDB
 * Ported from electron/database.js product functions
 */

import { products } from './schema';

/**
 * Get all products with optional filters
 * @param {Object} filters - { category, search, active, limit }
 * @returns {Promise<Array>} Array of products
 */
export async function getProducts(filters = {}) {
  try {
    let query = products.toCollection();

    // Apply filters
    if (filters.category) {
      query = products.where('category').equals(filters.category);
    }

    if (filters.search) {
      const searchTerm = filters.search.toLowerCase();
      query = query.filter(product =>
        product.name.toLowerCase().includes(searchTerm) ||
        product.sku.toLowerCase().includes(searchTerm) ||
        (product.barcode && product.barcode.toLowerCase().includes(searchTerm))
      );
    }

    if (filters.active !== undefined) {
      query = query.filter(product => product.active === filters.active);
    }

    // Sort by name
    const results = await query.sortBy('name');

    // Apply limit
    const limit = filters.limit || 1000;
    return results.slice(0, limit);
  } catch (error) {
    console.error('❌ Error getting products:', error);
    return [];
  }
}

/**
 * Get product by ID
 * @param {number} id - Product ID
 * @returns {Promise<Object|null>} Product or null
 */
export async function getProduct(id) {
  try {
    return await products.get(id);
  } catch (error) {
    console.error('❌ Error getting product:', error);
    return null;
  }
}

/**
 * Get product by SKU
 * @param {string} sku - Product SKU
 * @returns {Promise<Object|null>} Product or null
 */
export async function getProductBySku(sku) {
  try {
    return await products.where('sku').equals(sku).first();
  } catch (error) {
    console.error('❌ Error getting product by SKU:', error);
    return null;
  }
}

/**
 * Get product by barcode
 * @param {string} barcode - Product barcode
 * @returns {Promise<Object|null>} Product or null
 */
export async function getProductByBarcode(barcode) {
  try {
    return await products.where('barcode').equals(barcode).first();
  } catch (error) {
    console.error('❌ Error getting product by barcode:', error);
    return null;
  }
}

/**
 * Search products by name, SKU, or barcode
 * @param {string} searchTerm - Search term
 * @returns {Promise<Array>} Array of matching products
 */
export async function searchProducts(searchTerm) {
  try {
    const term = searchTerm.toLowerCase();

    const results = await products
      .filter(product =>
        product.name.toLowerCase().includes(term) ||
        product.sku.toLowerCase().includes(term) ||
        (product.barcode && product.barcode.toLowerCase().includes(term))
      )
      .toArray();

    return results;
  } catch (error) {
    console.error('❌ Error searching products:', error);
    return [];
  }
}

/**
 * Update product stock quantity
 * @param {number} productId - Product ID
 * @param {number} quantityChange - Quantity to add (positive) or subtract (negative)
 * @returns {Promise<Object>} Updated product
 */
export async function updateProductStock(productId, quantityChange) {
  try {
    const product = await products.get(productId);

    if (!product) {
      throw new Error(`Product ${productId} not found`);
    }

    const newQuantity = product.quantity + quantityChange;

    if (newQuantity < 0) {
      throw new Error(`Insufficient stock for product ${product.name}. Available: ${product.quantity}, Requested: ${Math.abs(quantityChange)}`);
    }

    await products.update(productId, {
      quantity: newQuantity,
      updated_at: new Date().toISOString()
    });

    const updatedProduct = await products.get(productId);
    console.log(`✅ Updated stock for ${product.name}: ${product.quantity} → ${newQuantity}`);

    return updatedProduct;
  } catch (error) {
    console.error('❌ Error updating product stock:', error);
    throw error;
  }
}

/**
 * Update product details
 * @param {number} productId - Product ID
 * @param {Object} updates - Fields to update
 * @returns {Promise<Object>} Updated product
 */
export async function updateProduct(productId, updates) {
  try {
    await products.update(productId, {
      ...updates,
      updated_at: new Date().toISOString()
    });

    const updatedProduct = await products.get(productId);
    console.log(`✅ Product ${productId} updated`);

    return updatedProduct;
  } catch (error) {
    console.error('❌ Error updating product:', error);
    throw error;
  }
}

/**
 * Add new product
 * @param {Object} productData - Product data
 * @returns {Promise<Object>} Created product
 */
export async function addProduct(productData) {
  try {
    // Check if SKU already exists
    const existingSku = await getProductBySku(productData.sku);
    if (existingSku) {
      throw new Error(`Product with SKU ${productData.sku} already exists`);
    }

    const product = {
      sku: productData.sku,
      barcode: productData.barcode || null,
      name: productData.name,
      description: productData.description || null,
      category: productData.category,
      price: productData.price,
      cost: productData.cost || 0,
      quantity: productData.quantity || 0,
      reorder_level: productData.reorder_level || 10,
      active: productData.active !== undefined ? productData.active : true,
      image_url: productData.image_url || null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    const id = await products.add(product);
    const createdProduct = await products.get(id);

    console.log(`✅ Product ${product.name} created with SKU ${product.sku}`);
    return createdProduct;
  } catch (error) {
    console.error('❌ Error adding product:', error);
    throw error;
  }
}

/**
 * Delete product (soft delete by setting active = false)
 * @param {number} productId - Product ID
 */
export async function deleteProduct(productId) {
  try {
    await products.update(productId, {
      active: false,
      updated_at: new Date().toISOString()
    });

    console.log(`✅ Product ${productId} deactivated`);
  } catch (error) {
    console.error('❌ Error deleting product:', error);
    throw error;
  }
}

/**
 * Get low stock products
 * @returns {Promise<Array>} Products below reorder level
 */
export async function getLowStockProducts() {
  try {
    const allProducts = await products.toArray();
    const lowStock = allProducts.filter(product =>
      product.active && product.quantity <= product.reorder_level
    );

    return lowStock.sort((a, b) => a.quantity - b.quantity);
  } catch (error) {
    console.error('❌ Error getting low stock products:', error);
    return [];
  }
}

/**
 * Get products by category
 * @param {string} category - Category name
 * @returns {Promise<Array>} Products in category
 */
export async function getProductsByCategory(category) {
  try {
    return await products
      .where('category')
      .equals(category)
      .and(product => product.active)
      .toArray();
  } catch (error) {
    console.error('❌ Error getting products by category:', error);
    return [];
  }
}

/**
 * Get all product categories
 * @returns {Promise<Array>} Array of unique category names
 */
export async function getCategories() {
  try {
    const allProducts = await products.toArray();
    const categories = [...new Set(allProducts.map(p => p.category))];
    return categories.sort();
  } catch (error) {
    console.error('❌ Error getting categories:', error);
    return [];
  }
}

/**
 * Bulk update product stock (for inventory sync)
 * @param {Array} updates - Array of { product_id, quantity }
 * @returns {Promise<number>} Number of products updated
 */
export async function bulkUpdateStock(updates) {
  try {
    let updatedCount = 0;

    for (const update of updates) {
      const product = await products.get(update.product_id);
      if (product) {
        await products.update(update.product_id, {
          quantity: update.quantity,
          updated_at: new Date().toISOString()
        });
        updatedCount++;
      }
    }

    console.log(`✅ Bulk updated ${updatedCount} products`);
    return updatedCount;
  } catch (error) {
    console.error('❌ Error bulk updating stock:', error);
    throw error;
  }
}
