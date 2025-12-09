import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { adminAPI } from '../../services/adminAPI';
import '../../styles/AdminDashboard.css';

const AdminReports = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [reportType, setReportType] = useState('sales');
  const [dateRange, setDateRange] = useState({
    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0],
  });
  const [reportData, setReportData] = useState(null);

  useEffect(() => {
    if (!user || (user.role !== 'admin' && user.role !== 'manager')) {
      navigate('/login');
      return;
    }
  }, [user, navigate]);

  const generateReport = async () => {
    try {
      setLoading(true);
      setError(null);

      let data;
      switch (reportType) {
        case 'sales':
          data = await adminAPI.getSalesReport(dateRange.start, dateRange.end);
          break;
        case 'inventory':
          data = await adminAPI.getInventoryReport();
          break;
        case 'customers':
          data = await adminAPI.getCustomersReport(dateRange.start, dateRange.end);
          break;
        case 'products':
          data = await adminAPI.getProductsReport(dateRange.start, dateRange.end);
          break;
        case 'employees':
          data = await adminAPI.getEmployeesReport(dateRange.start, dateRange.end);
          break;
        default:
          data = null;
      }

      setReportData(data);
    } catch (err) {
      setError(err.message || 'Failed to generate report');
      console.error('Report error:', err);
    } finally {
      setLoading(false);
    }
  };

  const exportReport = async (format) => {
    try {
      await adminAPI.exportReport(reportType, dateRange.start, dateRange.end, format);
      alert(`Report exported as ${format.toUpperCase()}`);
    } catch (err) {
      alert(err.message || 'Failed to export report');
    }
  };

  const renderSalesReport = () => {
    if (!reportData) return null;

    return (
      <div className="report-content">
        <div className="report-summary">
          <div className="summary-card">
            <h3>Total Revenue</h3>
            <p className="metric-large">${reportData.totalRevenue?.toFixed(2) || '0.00'}</p>
          </div>
          <div className="summary-card">
            <h3>Total Orders</h3>
            <p className="metric-large">{reportData.totalOrders || 0}</p>
          </div>
          <div className="summary-card">
            <h3>Average Order Value</h3>
            <p className="metric-large">${reportData.avgOrderValue?.toFixed(2) || '0.00'}</p>
          </div>
          <div className="summary-card">
            <h3>Total Profit</h3>
            <p className="metric-large">${reportData.totalProfit?.toFixed(2) || '0.00'}</p>
          </div>
        </div>

        {reportData.dailySales && (
          <div className="chart-section">
            <h3>Daily Sales Trend</h3>
            <div className="simple-chart">
              {reportData.dailySales.map((day) => (
                <div key={day.date} className="chart-bar">
                  <div className="bar-label">{new Date(day.date).toLocaleDateString()}</div>
                  <div
                    className="bar"
                    style={{
                      width: `${(day.sales / Math.max(...reportData.dailySales.map((d) => d.sales))) * 100}%`,
                    }}
                  >
                    ${day.sales.toFixed(2)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {reportData.topProducts && (
          <div className="table-section">
            <h3>Top Selling Products</h3>
            <table className="report-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Units Sold</th>
                  <th>Revenue</th>
                </tr>
              </thead>
              <tbody>
                {reportData.topProducts.map((product) => (
                  <tr key={product.id}>
                    <td>{product.name}</td>
                    <td>{product.unitsSold}</td>
                    <td>${product.revenue.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
  };

  const renderInventoryReport = () => {
    if (!reportData) return null;

    return (
      <div className="report-content">
        <div className="report-summary">
          <div className="summary-card">
            <h3>Total Products</h3>
            <p className="metric-large">{reportData.totalProducts || 0}</p>
          </div>
          <div className="summary-card">
            <h3>Low Stock Items</h3>
            <p className="metric-large alert">{reportData.lowStockItems || 0}</p>
          </div>
          <div className="summary-card">
            <h3>Out of Stock</h3>
            <p className="metric-large alert">{reportData.outOfStockItems || 0}</p>
          </div>
          <div className="summary-card">
            <h3>Total Value</h3>
            <p className="metric-large">${reportData.totalInventoryValue?.toFixed(2) || '0.00'}</p>
          </div>
        </div>

        {reportData.lowStockProducts && (
          <div className="table-section">
            <h3>Low Stock Products</h3>
            <table className="report-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Current Stock</th>
                  <th>Threshold</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {reportData.lowStockProducts.map((product) => (
                  <tr key={product.id}>
                    <td>{product.name}</td>
                    <td>{product.stock}</td>
                    <td>{product.threshold}</td>
                    <td>
                      <span className="badge badge-warning">Low Stock</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
  };

  const renderCustomersReport = () => {
    if (!reportData) return null;

    return (
      <div className="report-content">
        <div className="report-summary">
          <div className="summary-card">
            <h3>Total Customers</h3>
            <p className="metric-large">{reportData.totalCustomers || 0}</p>
          </div>
          <div className="summary-card">
            <h3>New Customers</h3>
            <p className="metric-large">{reportData.newCustomers || 0}</p>
          </div>
          <div className="summary-card">
            <h3>Active Customers</h3>
            <p className="metric-large">{reportData.activeCustomers || 0}</p>
          </div>
          <div className="summary-card">
            <h3>Customer Lifetime Value</h3>
            <p className="metric-large">${reportData.avgLifetimeValue?.toFixed(2) || '0.00'}</p>
          </div>
        </div>

        {reportData.topCustomers && (
          <div className="table-section">
            <h3>Top Customers</h3>
            <table className="report-table">
              <thead>
                <tr>
                  <th>Customer</th>
                  <th>Orders</th>
                  <th>Total Spent</th>
                </tr>
              </thead>
              <tbody>
                {reportData.topCustomers.map((customer) => (
                  <tr key={customer.id}>
                    <td>{customer.name}</td>
                    <td>{customer.totalOrders}</td>
                    <td>${customer.totalSpent.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
  };

  const renderProductsReport = () => {
    if (!reportData) return null;

    return (
      <div className="report-content">
        <div className="report-summary">
          <div className="summary-card">
            <h3>Total Products Sold</h3>
            <p className="metric-large">{reportData.totalProductsSold || 0}</p>
          </div>
          <div className="summary-card">
            <h3>Unique Products</h3>
            <p className="metric-large">{reportData.uniqueProducts || 0}</p>
          </div>
          <div className="summary-card">
            <h3>Avg Units per Order</h3>
            <p className="metric-large">{reportData.avgUnitsPerOrder?.toFixed(2) || '0.00'}</p>
          </div>
        </div>

        {reportData.categoryBreakdown && (
          <div className="table-section">
            <h3>Sales by Category</h3>
            <table className="report-table">
              <thead>
                <tr>
                  <th>Category</th>
                  <th>Units Sold</th>
                  <th>Revenue</th>
                  <th>% of Total</th>
                </tr>
              </thead>
              <tbody>
                {reportData.categoryBreakdown.map((cat) => (
                  <tr key={cat.category}>
                    <td>{cat.category}</td>
                    <td>{cat.unitsSold}</td>
                    <td>${cat.revenue.toFixed(2)}</td>
                    <td>{cat.percentage.toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
  };

  const renderEmployeesReport = () => {
    if (!reportData) return null;

    return (
      <div className="report-content">
        <div className="report-summary">
          <div className="summary-card">
            <h3>Total Employees</h3>
            <p className="metric-large">{reportData.totalEmployees || 0}</p>
          </div>
          <div className="summary-card">
            <h3>Total Hours Worked</h3>
            <p className="metric-large">{reportData.totalHours?.toFixed(2) || '0.00'}</p>
          </div>
          <div className="summary-card">
            <h3>Labor Cost</h3>
            <p className="metric-large">${reportData.totalLaborCost?.toFixed(2) || '0.00'}</p>
          </div>
        </div>

        {reportData.employeePerformance && (
          <div className="table-section">
            <h3>Employee Performance</h3>
            <table className="report-table">
              <thead>
                <tr>
                  <th>Employee</th>
                  <th>Hours Worked</th>
                  <th>Sales Processed</th>
                  <th>Revenue Generated</th>
                </tr>
              </thead>
              <tbody>
                {reportData.employeePerformance.map((emp) => (
                  <tr key={emp.id}>
                    <td>{emp.name}</td>
                    <td>{emp.hours.toFixed(2)}</td>
                    <td>{emp.salesProcessed}</td>
                    <td>${emp.revenue.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="admin-reports">
      <div className="page-header">
        <h1>Reports & Analytics</h1>
      </div>

      {error && (
        <div className="error-message">
          {error}
          <button onClick={() => setError(null)} className="close-btn">×</button>
        </div>
      )}

      {/* Report Controls */}
      <div className="report-controls">
        <div className="control-group">
          <label>Report Type:</label>
          <select
            value={reportType}
            onChange={(e) => setReportType(e.target.value)}
            className="form-input"
          >
            <option value="sales">Sales Report</option>
            <option value="inventory">Inventory Report</option>
            <option value="customers">Customers Report</option>
            <option value="products">Products Report</option>
            <option value="employees">Employees Report</option>
          </select>
        </div>

        {reportType !== 'inventory' && (
          <>
            <div className="control-group">
              <label>Start Date:</label>
              <input
                type="date"
                value={dateRange.start}
                onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
                className="form-input"
              />
            </div>

            <div className="control-group">
              <label>End Date:</label>
              <input
                type="date"
                value={dateRange.end}
                onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
                className="form-input"
              />
            </div>
          </>
        )}

        <button onClick={generateReport} className="btn-primary" disabled={loading}>
          {loading ? 'Generating...' : 'Generate Report'}
        </button>
      </div>

      {/* Export Buttons */}
      {reportData && (
        <div className="export-controls">
          <button onClick={() => exportReport('csv')} className="btn-secondary">
            Export as CSV
          </button>
          <button onClick={() => exportReport('json')} className="btn-secondary">
            Export as JSON
          </button>
          <button onClick={() => exportReport('pdf')} className="btn-secondary">
            Export as PDF
          </button>
        </div>
      )}

      {/* Report Display */}
      {loading && <div className="loading-spinner">Generating report...</div>}

      {!loading && reportData && (
        <div className="report-container">
          {reportType === 'sales' && renderSalesReport()}
          {reportType === 'inventory' && renderInventoryReport()}
          {reportType === 'customers' && renderCustomersReport()}
          {reportType === 'products' && renderProductsReport()}
          {reportType === 'employees' && renderEmployeesReport()}
        </div>
      )}

      {!loading && !reportData && (
        <div className="empty-state">
          <p>Select a report type and date range, then click "Generate Report"</p>
        </div>
      )}
    </div>
  );
};

export default AdminReports;
