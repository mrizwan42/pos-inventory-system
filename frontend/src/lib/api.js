// API configuration and utilities
const API_BASE_URL = '/api';

class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  getAuthToken() {
    return localStorage.getItem('access_token');
  }

  setAuthToken(token) {
    localStorage.setItem('access_token', token);
  }

  removeAuthToken() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const token = this.getAuthToken();

    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, config);
      
      if (response.status === 401) {
        // Token expired, try to refresh
        const refreshed = await this.refreshToken();
        if (refreshed) {
          // Retry the original request
          config.headers.Authorization = `Bearer ${this.getAuthToken()}`;
          const retryResponse = await fetch(url, config);
          return this.handleResponse(retryResponse);
        } else {
          // Refresh failed, redirect to login
          this.removeAuthToken();
          window.location.href = '/login';
          return null;
        }
      }

      return this.handleResponse(response);
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  async handleResponse(response) {
    const contentType = response.headers.get('content-type');
    
    if (contentType && contentType.includes('application/json')) {
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || `HTTP error! status: ${response.status}`);
      }
      
      return data;
    } else {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response;
    }
  }

  async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) return false;

    try {
      const response = await fetch(`${this.baseURL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${refreshToken}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        this.setAuthToken(data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        return true;
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
    }

    return false;
  }

  // Authentication endpoints
  async login(credentials) {
    const response = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });

    if (response.access_token) {
      this.setAuthToken(response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);
      localStorage.setItem('user', JSON.stringify(response.user));
    }

    return response;
  }

  async logout() {
    try {
      await this.request('/auth/logout', { method: 'POST' });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      this.removeAuthToken();
    }
  }

  async getCurrentUser() {
    return this.request('/auth/me');
  }

  // Products endpoints
  async getProducts(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/products?${queryString}`);
  }

  async getProduct(id) {
    return this.request(`/products/${id}`);
  }

  async createProduct(product) {
    return this.request('/products', {
      method: 'POST',
      body: JSON.stringify(product),
    });
  }

  async updateProduct(id, product) {
    return this.request(`/products/${id}`, {
      method: 'PUT',
      body: JSON.stringify(product),
    });
  }

  async deleteProduct(id) {
    return this.request(`/products/${id}`, { method: 'DELETE' });
  }

  async searchProducts(query) {
    return this.request(`/products/search?q=${encodeURIComponent(query)}`);
  }

  async getProductByBarcode(barcode) {
    return this.request(`/products/barcode/${encodeURIComponent(barcode)}`);
  }

  // Inventory endpoints
  async getInventory(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/inventory?${queryString}`);
  }

  async adjustStock(adjustment) {
    return this.request('/inventory/adjust', {
      method: 'POST',
      body: JSON.stringify(adjustment),
    });
  }

  async transferStock(transfer) {
    return this.request('/inventory/transfer', {
      method: 'POST',
      body: JSON.stringify(transfer),
    });
  }

  async getStockMovements(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/inventory/movements?${queryString}`);
  }

  async getLowStockItems(branchId) {
    const params = branchId ? `?branch_id=${branchId}` : '';
    return this.request(`/inventory/low-stock${params}`);
  }

  // Sales endpoints
  async getSales(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/sales?${queryString}`);
  }

  async getSale(id) {
    return this.request(`/sales/${id}`);
  }

  async createSale(sale) {
    return this.request('/sales', {
      method: 'POST',
      body: JSON.stringify(sale),
    });
  }

  async refundSale(id, reason) {
    return this.request(`/sales/${id}/refund`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  }

  async getDailySummary(date, branchId) {
    const params = new URLSearchParams({ date });
    if (branchId) params.append('branch_id', branchId);
    return this.request(`/sales/daily-summary?${params}`);
  }

  async getReceipt(saleId) {
    return this.request(`/sales/receipt/${saleId}`);
  }

  // Customers endpoints
  async getCustomers(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/customers?${queryString}`);
  }

  async getCustomer(id) {
    return this.request(`/customers/${id}`);
  }

  async createCustomer(customer) {
    return this.request('/customers', {
      method: 'POST',
      body: JSON.stringify(customer),
    });
  }

  async updateCustomer(id, customer) {
    return this.request(`/customers/${id}`, {
      method: 'PUT',
      body: JSON.stringify(customer),
    });
  }

  async searchCustomers(query) {
    return this.request(`/customers/search?q=${encodeURIComponent(query)}`);
  }

  // Suppliers endpoints
  async getSuppliers(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/suppliers?${queryString}`);
  }

  async createSupplier(supplier) {
    return this.request('/suppliers', {
      method: 'POST',
      body: JSON.stringify(supplier),
    });
  }

  // Purchase orders endpoints
  async getPurchaseOrders(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/purchases?${queryString}`);
  }

  async createPurchaseOrder(po) {
    return this.request('/purchases', {
      method: 'POST',
      body: JSON.stringify(po),
    });
  }

  async approvePurchaseOrder(id) {
    return this.request(`/purchases/${id}/approve`, { method: 'POST' });
  }

  async receivePurchaseOrder(id, items) {
    return this.request(`/purchases/${id}/receive`, {
      method: 'POST',
      body: JSON.stringify({ items }),
    });
  }

  // Reports endpoints
  async getSalesReport(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/reports/sales-summary?${queryString}`);
  }

  async getTopProducts(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/reports/top-products?${queryString}`);
  }

  async getInventoryValuation(branchId) {
    const params = branchId ? `?branch_id=${branchId}` : '';
    return this.request(`/reports/inventory-valuation${params}`);
  }

  async getProfitLossReport(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/reports/profit-loss?${queryString}`);
  }

  // Settings endpoints
  async getSettings() {
    return this.request('/settings');
  }

  async updateSetting(key, value) {
    return this.request(`/settings/${key}`, {
      method: 'PUT',
      body: JSON.stringify({ setting_value: value }),
    });
  }

  async getBranches() {
    return this.request('/settings/branches');
  }

  async getCategories() {
    return this.request('/settings/categories');
  }

  async createCategory(category) {
    return this.request('/settings/categories', {
      method: 'POST',
      body: JSON.stringify(category),
    });
  }
}

export const apiClient = new ApiClient();

