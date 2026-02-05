import React from 'react';
import { Download } from 'lucide-react';
import { Button } from './ui/button';

/**
 * Export data to CSV file
 * @param {Array} data - Array of objects to export
 * @param {string} filename - Name of the CSV file (without extension)
 * @param {Array} columns - Optional array of column keys to include
 */
export const exportToCSV = (data, filename = 'export', columns = null) => {
    if (!data || data.length === 0) {
        console.warn('No data to export');
        return;
    }

    // Get headers from first object or use provided columns
    const headers = columns || Object.keys(data[0]);

    // Create CSV header row
    const csvHeader = headers.join(',');

    // Create CSV data rows
    const csvRows = data.map(row => {
        return headers.map(header => {
            const value = row[header];
            // Handle null/undefined
            if (value === null || value === undefined) return '';
            // Escape commas and quotes
            const stringValue = String(value);
            if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
                return `"${stringValue.replace(/"/g, '""')}"`;
            }
            return stringValue;
        }).join(',');
    });

    // Combine header and rows
    const csv = [csvHeader, ...csvRows].join('\n');

    // Create blob and download
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    link.setAttribute('href', url);
    link.setAttribute('download', `${filename}.csv`);
    link.style.visibility = 'hidden';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
};

/**
 * Export Button Component
 */
export const ExportButton = ({ data, filename, columns, label = 'Export CSV', disabled = false }) => {
    const handleExport = () => {
        exportToCSV(data, filename, columns);
    };

    return (
        <Button
            onClick={handleExport}
            disabled={disabled || !data || data.length === 0}
            variant="outline"
            className="border-indigo-600 text-indigo-600 hover:bg-indigo-50"
        >
            <Download className="w-4 h-4 mr-2" />
            {label}
        </Button>
    );
};

export default exportToCSV;
