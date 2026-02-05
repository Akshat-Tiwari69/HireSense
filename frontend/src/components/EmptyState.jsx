import React from 'react';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Inbox, Plus, Search, FileX } from 'lucide-react';

export const EmptyState = ({ 
  icon: Icon = Inbox, 
  title = 'No items found', 
  description = 'Get started by creating a new item',
  action,
  actionLabel = 'Create New'
}) => {
  return (
    <Card className="bg-white border-none shadow-md">
      <div className="p-12 text-center">
        <div className="flex justify-center mb-6">
          <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center">
            <Icon className="w-10 h-10 text-slate-400" />
          </div>
        </div>
        <h3 className="text-xl font-semibold text-slate-900 mb-2">{title}</h3>
        <p className="text-slate-600 mb-6 max-w-md mx-auto">{description}</p>
        {action && (
          <Button onClick={action} className="bg-indigo-600 hover:bg-indigo-700">
            <Plus className="w-4 h-4 mr-2" />
            {actionLabel}
          </Button>
        )}
      </div>
    </Card>
  );
};

export const EmptySearchResults = ({ searchQuery, onReset }) => {
  return (
    <div className="text-center py-12">
      <div className="flex justify-center mb-4">
        <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center">
          <Search className="w-8 h-8 text-slate-400" />
        </div>
      </div>
      <h3 className="text-lg font-semibold text-slate-900 mb-2">No results found</h3>
      <p className="text-slate-600 mb-4">
        We couldn't find any results for "{searchQuery}"
      </p>
      {onReset && (
        <Button variant="outline" onClick={onReset} className="border-slate-300 text-slate-700">
          Clear Search
        </Button>
      )}
    </div>
  );
};

export const EmptyTableState = ({ message = 'No data available' }) => {
  return (
    <div className="text-center py-8">
      <FileX className="w-12 h-12 text-slate-400 mx-auto mb-3" />
      <p className="text-slate-600">{message}</p>
    </div>
  );
};

export default EmptyState;
