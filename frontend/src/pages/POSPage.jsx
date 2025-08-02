import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Search,
  Plus,
  Minus,
  Trash2,
  ShoppingCart,
  CreditCard,
  DollarSign,
  Smartphone,
  Receipt,
  User,
  Scan,
} from 'lucide-react';
import { apiClient } from '../lib/api';
import LoadingSpinner from '../components/LoadingSpinner';
import { toast } from 'sonner';

const POSPage = () => {
  const [cart, setCart] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [customer, setCustomer] = useState(null);
  const [customerSearch, setCustomerSearch] = useState('');
  const [customerResults, setCustomerResults] = useState([]);
  const [paymentMethod, setPaymentMethod] = useState('Cash');
  const [discount, setDiscount] = useState(0);
  const [processing, setProcessing] = useState(false);
  const [showReceipt, setShowReceipt] = useState(false);
  const [lastSale, setLastSale] = useState(null);
  const [branches, setBranches] = useState([]);
  const [selectedBranch, setSelectedBranch] = useState(null);
  
  const barcodeInputRef = useRef(null);
  const searchTimeoutRef = useRef(null);

  useEffect(() => {
    loadBranches();
    // Focus on barcode input when component mounts
    if (barcodeInputRef.current) {
      barcodeInputRef.current.focus();
    }
  }, []);

  useEffect(() => {
    // Debounced product search
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (searchQuery.length >= 2) {
      searchTimeoutRef.current = setTimeout(() => {
        searchProducts();
      }, 300);
    } else {
      setSearchResults([]);
    }

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchQuery]);

  const loadBranches = async () => {
    try {
      const response = await apiClient.getBranches();
      setBranches(response.branches || []);
      if (response.branches?.length > 0) {
        setSelectedBranch(response.branches[0].id);
      }
    } catch (error) {
      console.error('Failed to load branches:', error);
      toast.error('Failed to load branches');
    }
  };

  const searchProducts = async () => {
    try {
      setSearching(true);
      const response = await apiClient.searchProducts(searchQuery);
      setSearchResults(response.products || []);
    } catch (error) {
      console.error('Product search failed:', error);
      toast.error('Product search failed');
    } finally {
      setSearching(false);
    }
  };

  const searchCustomers = async (query) => {
    try {
      const response = await apiClient.searchCustomers(query);
      setCustomerResults(response.customers || []);
    } catch (error) {
      console.error('Customer search failed:', error);
    }
  };

  const handleBarcodeInput = async (e) => {
    if (e.key === 'Enter') {
      const barcode = e.target.value.trim();
      if (barcode) {
        try {
          const response = await apiClient.getProductByBarcode(barcode);
          addToCart(response.product);
          e.target.value = '';
        } catch (error) {
          toast.error('Product not found');
          e.target.value = '';
        }
      }
    }
  };

  const addToCart = (product) => {
    setCart(prevCart => {
      const existingItem = prevCart.find(item => item.product_id === product.id);
      
      if (existingItem) {
        return prevCart.map(item =>
          item.product_id === product.id
            ? { ...item, quantity: item.quantity + 1 }
            : item
        );
      } else {
        return [...prevCart, {
          product_id: product.id,
          product_name: product.product_name,
          product_code: product.product_code,
          unit_price: parseFloat(product.selling_price),
          quantity: 1,
          tax_rate: parseFloat(product.tax_rate || 0),
        }];
      }
    });
    
    // Clear search
    setSearchQuery('');
    setSearchResults([]);
    
    // Refocus on barcode input
    if (barcodeInputRef.current) {
      barcodeInputRef.current.focus();
    }
  };

  const updateQuantity = (productId, newQuantity) => {
    if (newQuantity <= 0) {
      removeFromCart(productId);
      return;
    }

    setCart(prevCart =>
      prevCart.map(item =>
        item.product_id === productId
          ? { ...item, quantity: newQuantity }
          : item
      )
    );
  };

  const removeFromCart = (productId) => {
    setCart(prevCart => prevCart.filter(item => item.product_id !== productId));
  };

  const clearCart = () => {
    setCart([]);
    setCustomer(null);
    setDiscount(0);
    setPaymentMethod('Cash');
  };

  const calculateTotals = () => {
    const subtotal = cart.reduce((sum, item) => {
      return sum + (item.unit_price * item.quantity);
    }, 0);

    const taxAmount = cart.reduce((sum, item) => {
      const itemSubtotal = item.unit_price * item.quantity;
      return sum + (itemSubtotal * (item.tax_rate / 100));
    }, 0);

    const discountAmount = (subtotal * discount) / 100;
    const total = subtotal + taxAmount - discountAmount;

    return {
      subtotal: subtotal.toFixed(2),
      taxAmount: taxAmount.toFixed(2),
      discountAmount: discountAmount.toFixed(2),
      total: total.toFixed(2),
    };
  };

  const processSale = async () => {
    if (cart.length === 0) {
      toast.error('Cart is empty');
      return;
    }

    if (!selectedBranch) {
      toast.error('Please select a branch');
      return;
    }

    try {
      setProcessing(true);

      const totals = calculateTotals();
      const saleData = {
        branch_id: selectedBranch,
        customer_id: customer?.id || null,
        payment_method: paymentMethod,
        discount_amount: parseFloat(totals.discountAmount),
        total_amount: parseFloat(totals.total),
        items: cart.map(item => ({
          product_id: item.product_id,
          quantity: item.quantity,
          unit_price: item.unit_price,
          discount_amount: 0,
        })),
      };

      const response = await apiClient.createSale(saleData);
      
      setLastSale(response.sale);
      setShowReceipt(true);
      clearCart();
      
      toast.success('Sale completed successfully!');
      
    } catch (error) {
      console.error('Sale processing failed:', error);
      toast.error(error.message || 'Sale processing failed');
    } finally {
      setProcessing(false);
    }
  };

  const totals = calculateTotals();

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
      {/* Left Panel - Product Search & Cart */}
      <div className="lg:col-span-2 space-y-6">
        {/* Search Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Search className="h-5 w-5 mr-2" />
              Product Search
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Barcode Scanner Input */}
            <div>
              <Label htmlFor="barcode">Scan Barcode</Label>
              <Input
                id="barcode"
                ref={barcodeInputRef}
                placeholder="Scan or enter barcode..."
                onKeyDown={handleBarcodeInput}
                className="text-lg"
              />
            </div>

            {/* Product Search */}
            <div>
              <Label htmlFor="search">Search Products</Label>
              <Input
                id="search"
                placeholder="Search by name or code..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            {/* Search Results */}
            {searching && (
              <div className="flex justify-center py-4">
                <LoadingSpinner />
              </div>
            )}

            {searchResults.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-60 overflow-y-auto">
                {searchResults.map((product) => (
                  <Card
                    key={product.id}
                    className="cursor-pointer hover:bg-gray-50 transition-colors"
                    onClick={() => addToCart(product)}
                  >
                    <CardContent className="p-3">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h4 className="font-medium text-sm">{product.product_name}</h4>
                          <p className="text-xs text-gray-500">{product.product_code}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-medium text-sm">${product.selling_price}</p>
                          <Badge variant="outline" className="text-xs">
                            {product.category?.category_name}
                          </Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Shopping Cart */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center">
                <ShoppingCart className="h-5 w-5 mr-2" />
                Shopping Cart ({cart.length})
              </div>
              {cart.length > 0 && (
                <Button variant="outline" size="sm" onClick={clearCart}>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Clear
                </Button>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {cart.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <ShoppingCart className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>Cart is empty</p>
                <p className="text-sm">Scan or search for products to add</p>
              </div>
            ) : (
              <div className="space-y-3">
                {cart.map((item) => (
                  <div key={item.product_id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex-1">
                      <h4 className="font-medium text-sm">{item.product_name}</h4>
                      <p className="text-xs text-gray-500">{item.product_code}</p>
                      <p className="text-sm font-medium">${item.unit_price.toFixed(2)} each</p>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => updateQuantity(item.product_id, item.quantity - 1)}
                      >
                        <Minus className="h-3 w-3" />
                      </Button>
                      
                      <span className="w-8 text-center font-medium">{item.quantity}</span>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => updateQuantity(item.product_id, item.quantity + 1)}
                      >
                        <Plus className="h-3 w-3" />
                      </Button>
                      
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => removeFromCart(item.product_id)}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                    
                    <div className="text-right ml-4">
                      <p className="font-medium">${(item.unit_price * item.quantity).toFixed(2)}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Right Panel - Checkout */}
      <div className="space-y-6">
        {/* Customer Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <User className="h-5 w-5 mr-2" />
              Customer
            </CardTitle>
          </CardHeader>
          <CardContent>
            {customer ? (
              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <div>
                  <p className="font-medium">{customer.first_name} {customer.last_name}</p>
                  <p className="text-sm text-gray-500">{customer.email}</p>
                  <p className="text-xs text-blue-600">{customer.loyalty_points} points</p>
                </div>
                <Button variant="outline" size="sm" onClick={() => setCustomer(null)}>
                  Remove
                </Button>
              </div>
            ) : (
              <div className="space-y-2">
                <Input
                  placeholder="Search customer..."
                  value={customerSearch}
                  onChange={(e) => {
                    setCustomerSearch(e.target.value);
                    if (e.target.value.length >= 2) {
                      searchCustomers(e.target.value);
                    } else {
                      setCustomerResults([]);
                    }
                  }}
                />
                {customerResults.length > 0 && (
                  <div className="max-h-40 overflow-y-auto space-y-1">
                    {customerResults.map((cust) => (
                      <div
                        key={cust.id}
                        className="p-2 hover:bg-gray-50 cursor-pointer rounded"
                        onClick={() => {
                          setCustomer(cust);
                          setCustomerSearch('');
                          setCustomerResults([]);
                        }}
                      >
                        <p className="text-sm font-medium">{cust.first_name} {cust.last_name}</p>
                        <p className="text-xs text-gray-500">{cust.email}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Order Summary */}
        <Card>
          <CardHeader>
            <CardTitle>Order Summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Branch Selection */}
            <div>
              <Label>Branch</Label>
              <Select value={selectedBranch?.toString()} onValueChange={(value) => setSelectedBranch(parseInt(value))}>
                <SelectTrigger>
                  <SelectValue placeholder="Select branch" />
                </SelectTrigger>
                <SelectContent>
                  {branches.map((branch) => (
                    <SelectItem key={branch.id} value={branch.id.toString()}>
                      {branch.branch_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Discount */}
            <div>
              <Label htmlFor="discount">Discount (%)</Label>
              <Input
                id="discount"
                type="number"
                min="0"
                max="100"
                value={discount}
                onChange={(e) => setDiscount(parseFloat(e.target.value) || 0)}
              />
            </div>

            <Separator />

            {/* Totals */}
            <div className="space-y-2">
              <div className="flex justify-between">
                <span>Subtotal:</span>
                <span>${totals.subtotal}</span>
              </div>
              <div className="flex justify-between">
                <span>Tax:</span>
                <span>${totals.taxAmount}</span>
              </div>
              {discount > 0 && (
                <div className="flex justify-between text-green-600">
                  <span>Discount ({discount}%):</span>
                  <span>-${totals.discountAmount}</span>
                </div>
              )}
              <Separator />
              <div className="flex justify-between text-lg font-bold">
                <span>Total:</span>
                <span>${totals.total}</span>
              </div>
            </div>

            {/* Payment Method */}
            <div>
              <Label>Payment Method</Label>
              <Select value={paymentMethod} onValueChange={setPaymentMethod}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Cash">
                    <div className="flex items-center">
                      <DollarSign className="h-4 w-4 mr-2" />
                      Cash
                    </div>
                  </SelectItem>
                  <SelectItem value="Card">
                    <div className="flex items-center">
                      <CreditCard className="h-4 w-4 mr-2" />
                      Card
                    </div>
                  </SelectItem>
                  <SelectItem value="Mobile">
                    <div className="flex items-center">
                      <Smartphone className="h-4 w-4 mr-2" />
                      Mobile Payment
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Checkout Button */}
            <Button
              className="w-full h-12 text-lg"
              onClick={processSale}
              disabled={cart.length === 0 || processing || !selectedBranch}
            >
              {processing ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Processing...
                </>
              ) : (
                <>
                  <Receipt className="h-5 w-5 mr-2" />
                  Complete Sale (${totals.total})
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Receipt Dialog */}
      <Dialog open={showReceipt} onOpenChange={setShowReceipt}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Sale Completed</DialogTitle>
            <DialogDescription>
              Transaction processed successfully
            </DialogDescription>
          </DialogHeader>
          
          {lastSale && (
            <div className="space-y-4">
              <div className="text-center">
                <h3 className="text-lg font-bold">Receipt</h3>
                <p className="text-sm text-gray-500">Sale #{lastSale.sale_number}</p>
                <p className="text-xs text-gray-500">
                  {new Date(lastSale.sale_date).toLocaleString()}
                </p>
              </div>
              
              <Separator />
              
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Subtotal:</span>
                  <span>${lastSale.sub_total?.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Tax:</span>
                  <span>${lastSale.tax_amount?.toFixed(2)}</span>
                </div>
                {lastSale.discount_amount > 0 && (
                  <div className="flex justify-between text-green-600">
                    <span>Discount:</span>
                    <span>-${lastSale.discount_amount?.toFixed(2)}</span>
                  </div>
                )}
                <Separator />
                <div className="flex justify-between text-lg font-bold">
                  <span>Total:</span>
                  <span>${lastSale.total_amount?.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Payment:</span>
                  <span>{lastSale.payment_method}</span>
                </div>
              </div>
              
              <div className="flex space-x-2">
                <Button variant="outline" className="flex-1" onClick={() => setShowReceipt(false)}>
                  Close
                </Button>
                <Button className="flex-1" onClick={() => window.print()}>
                  Print Receipt
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default POSPage;

