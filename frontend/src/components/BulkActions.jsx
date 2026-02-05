import React, { useState } from 'react';
import { Checkbox } from './ui/checkbox';
import { Button } from './ui/button';
import { Trash2, Mail, Download, Edit } from 'lucide-react';

/**
 * Bulk Actions Bar component
 * Shows when items are selected and provides bulk action buttons
 */
export const BulkActionsBar = ({
    selectedCount,
    totalCount,
    onSelectAll,
    onDeselectAll,
    actions = [],
    className = ''
}) => {
    if (selectedCount === 0) return null;

    const allSelected = selectedCount === totalCount;

    return (
        <div className={`bg-indigo-50 border border-indigo-200 rounded-lg p-4 flex items-center justify-between ${className}`}>
            <div className="flex items-center gap-4">
                <Checkbox
                    checked={allSelected}
                    onCheckedChange={(checked) => {
                        if (checked) {
                            onSelectAll && onSelectAll();
                        } else {
                            onDeselectAll && onDeselectAll();
                        }
                    }}
                />
                <span className="text-sm font-medium text-slate-700">
                    {selectedCount} of {totalCount} selected
                </span>
            </div>

            <div className="flex items-center gap-2">
                {actions.map((action, index) => (
                    <Button
                        key={index}
                        onClick={action.onClick}
                        variant={action.variant || 'outline'}
                        size="sm"
                        className={action.className || ''}
                    >
                        {action.icon && <action.icon className="w-4 h-4 mr-2" />}
                        {action.label}
                    </Button>
                ))}

                <Button
                    onClick={onDeselectAll}
                    variant="ghost"
                    size="sm"
                >
                    Cancel
                </Button>
            </div>
        </div>
    );
};

/**
 * Hook for managing bulk selection state
 */
export const useBulkSelection = (items = []) => {
    const [selectedIds, setSelectedIds] = useState(new Set());

    const toggleSelection = (id) => {
        const newSelection = new Set(selectedIds);
        if (newSelection.has(id)) {
            newSelection.delete(id);
        } else {
            newSelection.add(id);
        }
        setSelectedIds(newSelection);
    };

    const selectAll = () => {
        setSelectedIds(new Set(items.map(item => item.id)));
    };

    const deselectAll = () => {
        setSelectedIds(new Set());
    };

    const isSelected = (id) => selectedIds.has(id);

    const getSelectedItems = () => {
        return items.filter(item => selectedIds.has(item.id));
    };

    return {
        selectedIds,
        selectedCount: selectedIds.size,
        toggleSelection,
        selectAll,
        deselectAll,
        isSelected,
        getSelectedItems,
    };
};

export default BulkActionsBar;
