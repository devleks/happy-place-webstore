/**
 * IndexedDB Database Operations - Central Export
 * Happy Place POS PWA
 */

// Export database instance and schema
export { db, initializeDatabase, getDatabaseStats } from './schema';

// Export backend sync utilities
export {
  syncEmployeesFromBackend,
  syncProductsFromBackend,
  getBackendAuthToken,
  setBackendAuthToken,
  initializeFromBackend,
  needsInitialSync,
  autoSyncOnStartup
} from './initializeFromBackend';

// Export shift operations
export {
  createShift,
  getCurrentShift,
  getShift,
  getShifts,
  closeShift,
  calculateShiftTotals,
  getUnsyncedShifts,
  markShiftAsSynced
} from './shifts';

// Export transaction operations
export {
  createTransaction,
  getTransaction,
  getTransactions,
  getShiftTransactions,
  getDailySalesSummary,
  getUnsyncedTransactions,
  markTransactionAsSynced,
  deleteTransaction
} from './transactions';

// Export product operations
export {
  getProducts,
  getProduct,
  getProductBySku,
  getProductByBarcode,
  searchProducts,
  updateProductStock,
  updateProduct,
  addProduct,
  deleteProduct,
  getLowStockProducts,
  getProductsByCategory,
  getCategories,
  bulkUpdateStock
} from './products';

// Export held transaction operations
export {
  holdTransaction,
  getHeldTransaction,
  getHeldTransactions,
  getEmployeeHeldTransactions,
  recallHeldTransaction,
  deleteHeldTransaction,
  updateHeldTransactionNotes,
  getHeldTransactionCount,
  clearOldHeldTransactions
} from './heldTransactions';

// Export employee operations
export {
  getEmployees,
  getEmployee,
  getEmployeeByEmail,
  getEmployeeByPin,
  validateEmployeeCredentials,
  validateEmployeePin,
  addEmployee,
  updateEmployee,
  deactivateEmployee,
  reactivateEmployee,
  deleteEmployee,
  getEmployeesByRole,
  searchEmployees,
  getActiveEmployeeCount
} from './employees';

// Export sync operations
export {
  addToSyncQueue,
  getPendingSyncItems,
  markSyncItemCompleted,
  markSyncItemFailed,
  clearCompletedSyncItems,
  getSyncQueueStats,
  syncWithBackend,
  isOnline,
  setMetadata,
  getMetadata,
  getLastSyncTime,
  setupBackgroundSync,
  forceSyncNow,
  getSyncStatus
} from './sync';
