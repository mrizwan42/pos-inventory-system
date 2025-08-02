import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Truck } from 'lucide-react';

const SuppliersPage = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Suppliers</h1>
        <p className="text-gray-600">Manage supplier relationships and procurement</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Truck className="h-5 w-5 mr-2" />
            Supplier Management
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <Truck className="h-16 w-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Suppliers Module</h3>
            <p className="text-gray-500">
              This module will help you manage supplier information, track payment terms,
              and maintain strong vendor relationships for your business.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SuppliersPage;

