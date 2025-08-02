import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Warehouse } from 'lucide-react';

const InventoryPage = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Inventory</h1>
        <p className="text-gray-600">Track and manage your stock levels</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Warehouse className="h-5 w-5 mr-2" />
            Inventory Management
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <Warehouse className="h-16 w-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Inventory Module</h3>
            <p className="text-gray-500">
              This module will help you track stock levels, manage stock movements,
              handle transfers between branches, and monitor low stock alerts.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default InventoryPage;

