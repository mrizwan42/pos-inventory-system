-- POS + Inventory Management System Database Schema
-- SQL Server Database

-- Create Database
CREATE DATABASE POSInventoryDB;
GO

USE POSInventoryDB;
GO

-- Users Table (Authentication & Role Management)
CREATE TABLE Users (
    UserID INT IDENTITY(1,1) PRIMARY KEY,
    Username NVARCHAR(50) UNIQUE NOT NULL,
    Email NVARCHAR(100) UNIQUE NOT NULL,
    PasswordHash NVARCHAR(255) NOT NULL,
    FirstName NVARCHAR(50) NOT NULL,
    LastName NVARCHAR(50) NOT NULL,
    Role NVARCHAR(20) NOT NULL CHECK (Role IN ('Admin', 'Cashier', 'InventoryManager')),
    IsActive BIT DEFAULT 1,
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    UpdatedAt DATETIME2 DEFAULT GETDATE()
);

-- Branches/Warehouses Table
CREATE TABLE Branches (
    BranchID INT IDENTITY(1,1) PRIMARY KEY,
    BranchName NVARCHAR(100) NOT NULL,
    Address NVARCHAR(255),
    Phone NVARCHAR(20),
    Email NVARCHAR(100),
    IsActive BIT DEFAULT 1,
    CreatedAt DATETIME2 DEFAULT GETDATE()
);

-- Categories Table
CREATE TABLE Categories (
    CategoryID INT IDENTITY(1,1) PRIMARY KEY,
    CategoryName NVARCHAR(100) NOT NULL,
    Description NVARCHAR(255),
    ParentCategoryID INT NULL,
    IsActive BIT DEFAULT 1,
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (ParentCategoryID) REFERENCES Categories(CategoryID)
);

-- Suppliers Table
CREATE TABLE Suppliers (
    SupplierID INT IDENTITY(1,1) PRIMARY KEY,
    SupplierName NVARCHAR(100) NOT NULL,
    ContactPerson NVARCHAR(100),
    Email NVARCHAR(100),
    Phone NVARCHAR(20),
    Address NVARCHAR(255),
    TaxNumber NVARCHAR(50),
    PaymentTerms NVARCHAR(100),
    IsActive BIT DEFAULT 1,
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    UpdatedAt DATETIME2 DEFAULT GETDATE()
);

-- Products Table
CREATE TABLE Products (
    ProductID INT IDENTITY(1,1) PRIMARY KEY,
    ProductCode NVARCHAR(50) UNIQUE NOT NULL,
    Barcode NVARCHAR(100) UNIQUE,
    ProductName NVARCHAR(200) NOT NULL,
    Description NVARCHAR(500),
    CategoryID INT NOT NULL,
    SupplierID INT,
    UnitOfMeasure NVARCHAR(20) NOT NULL,
    CostPrice DECIMAL(10,2) NOT NULL,
    SellingPrice DECIMAL(10,2) NOT NULL,
    MinStockLevel INT DEFAULT 0,
    MaxStockLevel INT DEFAULT 0,
    ReorderLevel INT DEFAULT 0,
    TaxRate DECIMAL(5,2) DEFAULT 0,
    IsActive BIT DEFAULT 1,
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    UpdatedAt DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (CategoryID) REFERENCES Categories(CategoryID),
    FOREIGN KEY (SupplierID) REFERENCES Suppliers(SupplierID)
);

-- Inventory Table
CREATE TABLE Inventory (
    InventoryID INT IDENTITY(1,1) PRIMARY KEY,
    ProductID INT NOT NULL,
    BranchID INT NOT NULL,
    CurrentStock INT NOT NULL DEFAULT 0,
    ReservedStock INT DEFAULT 0,
    AvailableStock AS (CurrentStock - ReservedStock),
    LastUpdated DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (ProductID) REFERENCES Products(ProductID),
    FOREIGN KEY (BranchID) REFERENCES Branches(BranchID),
    UNIQUE(ProductID, BranchID)
);

-- Stock Movements Table
CREATE TABLE StockMovements (
    MovementID INT IDENTITY(1,1) PRIMARY KEY,
    ProductID INT NOT NULL,
    BranchID INT NOT NULL,
    MovementType NVARCHAR(20) NOT NULL CHECK (MovementType IN ('IN', 'OUT', 'TRANSFER', 'ADJUSTMENT')),
    Quantity INT NOT NULL,
    UnitCost DECIMAL(10,2),
    Reference NVARCHAR(100),
    Notes NVARCHAR(255),
    CreatedBy INT NOT NULL,
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (ProductID) REFERENCES Products(ProductID),
    FOREIGN KEY (BranchID) REFERENCES Branches(BranchID),
    FOREIGN KEY (CreatedBy) REFERENCES Users(UserID)
);

-- Customers Table
CREATE TABLE Customers (
    CustomerID INT IDENTITY(1,1) PRIMARY KEY,
    CustomerCode NVARCHAR(50) UNIQUE,
    FirstName NVARCHAR(50) NOT NULL,
    LastName NVARCHAR(50) NOT NULL,
    Email NVARCHAR(100),
    Phone NVARCHAR(20),
    Address NVARCHAR(255),
    DateOfBirth DATE,
    LoyaltyPoints INT DEFAULT 0,
    TotalPurchases DECIMAL(12,2) DEFAULT 0,
    IsActive BIT DEFAULT 1,
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    UpdatedAt DATETIME2 DEFAULT GETDATE()
);

-- Sales Table
CREATE TABLE Sales (
    SaleID INT IDENTITY(1,1) PRIMARY KEY,
    SaleNumber NVARCHAR(50) UNIQUE NOT NULL,
    CustomerID INT,
    BranchID INT NOT NULL,
    CashierID INT NOT NULL,
    SaleDate DATETIME2 DEFAULT GETDATE(),
    SubTotal DECIMAL(12,2) NOT NULL,
    TaxAmount DECIMAL(12,2) DEFAULT 0,
    DiscountAmount DECIMAL(12,2) DEFAULT 0,
    TotalAmount DECIMAL(12,2) NOT NULL,
    PaymentMethod NVARCHAR(20) NOT NULL CHECK (PaymentMethod IN ('Cash', 'Card', 'Mobile', 'Credit')),
    PaymentStatus NVARCHAR(20) DEFAULT 'Completed' CHECK (PaymentStatus IN ('Pending', 'Completed', 'Refunded')),
    Notes NVARCHAR(255),
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID),
    FOREIGN KEY (BranchID) REFERENCES Branches(BranchID),
    FOREIGN KEY (CashierID) REFERENCES Users(UserID)
);

-- Sale Items Table
CREATE TABLE SaleItems (
    SaleItemID INT IDENTITY(1,1) PRIMARY KEY,
    SaleID INT NOT NULL,
    ProductID INT NOT NULL,
    Quantity INT NOT NULL,
    UnitPrice DECIMAL(10,2) NOT NULL,
    DiscountAmount DECIMAL(10,2) DEFAULT 0,
    TaxAmount DECIMAL(10,2) DEFAULT 0,
    LineTotal DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (SaleID) REFERENCES Sales(SaleID) ON DELETE CASCADE,
    FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
);

-- Purchase Orders Table
CREATE TABLE PurchaseOrders (
    PurchaseOrderID INT IDENTITY(1,1) PRIMARY KEY,
    PONumber NVARCHAR(50) UNIQUE NOT NULL,
    SupplierID INT NOT NULL,
    BranchID INT NOT NULL,
    OrderDate DATETIME2 DEFAULT GETDATE(),
    ExpectedDeliveryDate DATE,
    Status NVARCHAR(20) DEFAULT 'Pending' CHECK (Status IN ('Pending', 'Approved', 'Received', 'Cancelled')),
    SubTotal DECIMAL(12,2) NOT NULL,
    TaxAmount DECIMAL(12,2) DEFAULT 0,
    TotalAmount DECIMAL(12,2) NOT NULL,
    Notes NVARCHAR(255),
    CreatedBy INT NOT NULL,
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    UpdatedAt DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (SupplierID) REFERENCES Suppliers(SupplierID),
    FOREIGN KEY (BranchID) REFERENCES Branches(BranchID),
    FOREIGN KEY (CreatedBy) REFERENCES Users(UserID)
);

-- Purchase Order Items Table
CREATE TABLE PurchaseOrderItems (
    POItemID INT IDENTITY(1,1) PRIMARY KEY,
    PurchaseOrderID INT NOT NULL,
    ProductID INT NOT NULL,
    OrderedQuantity INT NOT NULL,
    ReceivedQuantity INT DEFAULT 0,
    UnitCost DECIMAL(10,2) NOT NULL,
    LineTotal DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (PurchaseOrderID) REFERENCES PurchaseOrders(PurchaseOrderID) ON DELETE CASCADE,
    FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
);

-- System Settings Table
CREATE TABLE SystemSettings (
    SettingID INT IDENTITY(1,1) PRIMARY KEY,
    SettingKey NVARCHAR(100) UNIQUE NOT NULL,
    SettingValue NVARCHAR(500),
    Description NVARCHAR(255),
    UpdatedBy INT,
    UpdatedAt DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (UpdatedBy) REFERENCES Users(UserID)
);

-- Loyalty Transactions Table
CREATE TABLE LoyaltyTransactions (
    TransactionID INT IDENTITY(1,1) PRIMARY KEY,
    CustomerID INT NOT NULL,
    SaleID INT,
    TransactionType NVARCHAR(20) NOT NULL CHECK (TransactionType IN ('EARNED', 'REDEEMED', 'EXPIRED', 'ADJUSTED')),
    Points INT NOT NULL,
    Description NVARCHAR(255),
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID),
    FOREIGN KEY (SaleID) REFERENCES Sales(SaleID)
);

-- Audit Log Table
CREATE TABLE AuditLog (
    LogID INT IDENTITY(1,1) PRIMARY KEY,
    TableName NVARCHAR(100) NOT NULL,
    RecordID INT NOT NULL,
    Action NVARCHAR(20) NOT NULL CHECK (Action IN ('INSERT', 'UPDATE', 'DELETE')),
    OldValues NVARCHAR(MAX),
    NewValues NVARCHAR(MAX),
    UserID INT,
    Timestamp DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (UserID) REFERENCES Users(UserID)
);

-- Create Indexes for Performance
CREATE INDEX IX_Products_CategoryID ON Products(CategoryID);
CREATE INDEX IX_Products_SupplierID ON Products(SupplierID);
CREATE INDEX IX_Products_Barcode ON Products(Barcode);
CREATE INDEX IX_Inventory_ProductID ON Inventory(ProductID);
CREATE INDEX IX_Inventory_BranchID ON Inventory(BranchID);
CREATE INDEX IX_Sales_SaleDate ON Sales(SaleDate);
CREATE INDEX IX_Sales_CustomerID ON Sales(CustomerID);
CREATE INDEX IX_SaleItems_SaleID ON SaleItems(SaleID);
CREATE INDEX IX_SaleItems_ProductID ON SaleItems(ProductID);
CREATE INDEX IX_StockMovements_ProductID ON StockMovements(ProductID);
CREATE INDEX IX_StockMovements_CreatedAt ON StockMovements(CreatedAt);

-- Insert Default System Settings
INSERT INTO SystemSettings (SettingKey, SettingValue, Description) VALUES
('TAX_RATE', '10.00', 'Default tax rate percentage'),
('CURRENCY', 'USD', 'System currency'),
('LOYALTY_POINTS_RATE', '1.00', 'Points earned per dollar spent'),
('LOW_STOCK_THRESHOLD', '10', 'Default low stock alert threshold'),
('RECEIPT_FOOTER', 'Thank you for your business!', 'Receipt footer message'),
('COMPANY_NAME', 'Your Company Name', 'Company name for receipts'),
('COMPANY_ADDRESS', '123 Main St, City, State 12345', 'Company address'),
('COMPANY_PHONE', '(555) 123-4567', 'Company phone number');

-- Insert Default Branch
INSERT INTO Branches (BranchName, Address, Phone, Email) VALUES
('Main Store', '123 Main Street, City, State 12345', '(555) 123-4567', 'main@company.com');

-- Insert Default Categories
INSERT INTO Categories (CategoryName, Description) VALUES
('Electronics', 'Electronic devices and accessories'),
('Clothing', 'Apparel and fashion items'),
('Food & Beverages', 'Food and drink products'),
('Home & Garden', 'Home improvement and garden supplies'),
('Books & Media', 'Books, movies, and media products');

-- Insert Default Admin User (Password: admin123 - should be hashed in real implementation)
INSERT INTO Users (Username, Email, PasswordHash, FirstName, LastName, Role) VALUES
('admin', 'admin@company.com', '$2b$10$rQZ8kHWKQYXHOGGVQExOHOqtNVyJMxS5K5rQZ8kHWKQYXHOGGVQExO', 'System', 'Administrator', 'Admin');

GO

