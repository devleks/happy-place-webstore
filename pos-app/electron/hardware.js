/**
 * Hardware Integration
 * Handles barcode scanners, receipt printers, and cash drawers
 */

const { ipcMain } = require('electron');

let mainWindow = null;
let barcodeScanner = null;
let receiptPrinter = null;

/**
 * Initialize hardware
 */
async function initHardware(window) {
  mainWindow = window;

  console.log('🔌 Initializing hardware...');

  try {
    // Initialize barcode scanner
    await initBarcodeScanner();

    // Initialize receipt printer
    await initReceiptPrinter();

    // Setup IPC handlers
    setupIpcHandlers();

    console.log('✅ Hardware initialized');
  } catch (error) {
    console.error('⚠️  Hardware initialization warning:', error);
    // Don't fail app if hardware is not available
  }
}

/**
 * Initialize barcode scanner
 */
async function initBarcodeScanner() {
  try {
    // TODO: Implement actual barcode scanner integration
    // For now, we'll use keyboard input simulation
    
    console.log('🔍 Barcode scanner: Using keyboard input mode');
    
    // Listen for keyboard input (barcode scanners act as keyboards)
    if (mainWindow) {
      let barcodeBuffer = '';
      let barcodeTimeout = null;

      mainWindow.webContents.on('before-input-event', (event, input) => {
        // Barcode scanners typically send Enter after the barcode
        if (input.type === 'keyDown') {
          if (input.key === 'Enter' && barcodeBuffer.length > 0) {
            // Send barcode to renderer
            mainWindow.webContents.send('barcode-scanned', barcodeBuffer.trim());
            console.log(`📷 Barcode scanned: ${barcodeBuffer}`);
            barcodeBuffer = '';
            
            if (barcodeTimeout) {
              clearTimeout(barcodeTimeout);
              barcodeTimeout = null;
            }
          } else if (input.key.length === 1) {
            // Accumulate barcode characters
            barcodeBuffer += input.key;
            
            // Reset buffer after 100ms of inactivity
            if (barcodeTimeout) {
              clearTimeout(barcodeTimeout);
            }
            barcodeTimeout = setTimeout(() => {
              barcodeBuffer = '';
            }, 100);
          }
        }
      });
    }

    return true;
  } catch (error) {
    console.error('❌ Barcode scanner initialization failed:', error);
    return false;
  }
}

/**
 * Initialize receipt printer
 */
async function initReceiptPrinter() {
  try {
    // TODO: Implement actual receipt printer integration
    // Options:
    // 1. node-escpos for ESC/POS printers
    // 2. node-printer for system printers
    // 3. electron-pos-printer
    
    console.log('🖨️  Receipt printer: Using system print dialog');
    
    return true;
  } catch (error) {
    console.error('❌ Receipt printer initialization failed:', error);
    return false;
  }
}

/**
 * Print receipt
 */
async function printReceipt(receipt) {
  try {
    console.log('🖨️  Printing receipt:', receipt.transaction_number);

    // Generate receipt HTML
    const receiptHtml = generateReceiptHtml(receipt);

    // Print using Electron's print API
    if (mainWindow) {
      const printWindow = new (require('electron').BrowserWindow)({
        show: false,
        webPreferences: {
          nodeIntegration: false,
          contextIsolation: true
        }
      });

      await printWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(receiptHtml)}`);
      
      // Auto-print without dialog in production
      const options = {
        silent: true, // Don't show print dialog
        printBackground: true,
        margins: {
          marginType: 'none'
        }
      };

      await printWindow.webContents.print(options, (success, errorType) => {
        if (success) {
          console.log('✅ Receipt printed successfully');
        } else {
          console.error('❌ Print failed:', errorType);
        }
        printWindow.close();
      });
    }

    return true;
  } catch (error) {
    console.error('❌ Receipt printing failed:', error);
    throw error;
  }
}

/**
 * Generate receipt HTML
 */
function generateReceiptHtml(receipt) {
  const date = new Date(receipt.created_at || Date.now()).toLocaleString();

  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        @page {
          size: 80mm auto;
          margin: 0;
        }
        body {
          font-family: 'Courier New', monospace;
          font-size: 12px;
          width: 80mm;
          margin: 0;
          padding: 10mm;
        }
        .center {
          text-align: center;
        }
        .bold {
          font-weight: bold;
        }
        .line {
          border-top: 1px dashed #000;
          margin: 5px 0;
        }
        table {
          width: 100%;
          border-collapse: collapse;
        }
        td {
          padding: 2px 0;
        }
        .right {
          text-align: right;
        }
        .total {
          font-size: 14px;
          font-weight: bold;
        }
      </style>
    </head>
    <body>
      <div class="center bold">
        HAPPY PLACE BOUTIQUE
      </div>
      <div class="center">
        Women's & Maternity Clothing
      </div>
      <div class="center">
        Tel: +254 XXX XXX XXX
      </div>
      
      <div class="line"></div>
      
      <div>
        <strong>Receipt #:</strong> ${receipt.transaction_number}
      </div>
      <div>
        <strong>Date:</strong> ${date}
      </div>
      ${receipt.employee_name ? `<div><strong>Cashier:</strong> ${receipt.employee_name}</div>` : ''}
      ${receipt.customer_name ? `<div><strong>Customer:</strong> ${receipt.customer_name}</div>` : ''}
      
      <div class="line"></div>
      
      <table>
        <thead>
          <tr>
            <td><strong>Item</strong></td>
            <td class="center"><strong>Qty</strong></td>
            <td class="right"><strong>Price</strong></td>
            <td class="right"><strong>Total</strong></td>
          </tr>
        </thead>
        <tbody>
          ${receipt.items.map(item => `
            <tr>
              <td>${item.product_name}</td>
              <td class="center">${item.quantity}</td>
              <td class="right">${formatCurrency(item.unit_price)}</td>
              <td class="right">${formatCurrency(item.total)}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
      
      <div class="line"></div>
      
      <table>
        <tr>
          <td><strong>Subtotal:</strong></td>
          <td class="right">${formatCurrency(receipt.subtotal)}</td>
        </tr>
        ${receipt.discount > 0 ? `
          <tr>
            <td><strong>Discount:</strong></td>
            <td class="right">-${formatCurrency(receipt.discount)}</td>
          </tr>
        ` : ''}
        ${receipt.tax > 0 ? `
          <tr>
            <td><strong>Tax:</strong></td>
            <td class="right">${formatCurrency(receipt.tax)}</td>
          </tr>
        ` : ''}
        <tr class="total">
          <td><strong>TOTAL:</strong></td>
          <td class="right">${formatCurrency(receipt.total)}</td>
        </tr>
        <tr>
          <td><strong>Payment:</strong></td>
          <td class="right">${receipt.payment_method.toUpperCase()}</td>
        </tr>
      </table>
      
      <div class="line"></div>
      
      <div class="center">
        Thank you for shopping with us!
      </div>
      <div class="center">
        Visit us at www.happyplace.co.ke
      </div>
      
      <div class="line"></div>
      
      <div class="center" style="font-size: 10px;">
        ${receipt.notes || ''}
      </div>
    </body>
    </html>
  `;
}

/**
 * Format currency
 */
function formatCurrency(amount) {
  return `KES ${parseFloat(amount).toFixed(2)}`;
}

/**
 * Open cash drawer
 */
async function openCashDrawer() {
  try {
    console.log('💰 Opening cash drawer...');
    
    // TODO: Implement actual cash drawer integration
    // ESC/POS command: 0x1B, 0x70, 0x00, 0x19, 0xFA
    
    console.log('✅ Cash drawer opened (simulated)');
    return true;
  } catch (error) {
    console.error('❌ Cash drawer open failed:', error);
    return false;
  }
}

/**
 * Setup IPC handlers
 */
function setupIpcHandlers() {
  ipcMain.handle('hardware-scan-barcode', async () => {
    // Manual barcode entry trigger
    return { success: true, message: 'Use barcode scanner or enter manually' };
  });

  ipcMain.handle('hardware-print-receipt', async (event, receipt) => {
    return await printReceipt(receipt);
  });

  ipcMain.handle('hardware-open-cash-drawer', async () => {
    return await openCashDrawer();
  });
}

/**
 * Cleanup hardware
 */
async function cleanupHardware() {
  console.log('🧹 Cleaning up hardware...');
  
  // Close barcode scanner connection
  if (barcodeScanner) {
    // TODO: Close scanner connection
    barcodeScanner = null;
  }

  // Close printer connection
  if (receiptPrinter) {
    // TODO: Close printer connection
    receiptPrinter = null;
  }

  console.log('✅ Hardware cleanup complete');
}

// ============================================================================
// EXPORTS
// ============================================================================

module.exports = {
  initHardware,
  cleanupHardware,
  printReceipt,
  openCashDrawer
};
