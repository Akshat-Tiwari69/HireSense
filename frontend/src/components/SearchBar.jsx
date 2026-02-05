import React, { useState } from 'react';
import { Search, X } from 'lucide-react';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';

/**
 * SearchBar component with filter capabilities
 */
export const SearchBar = ({
    placeholder = 'Search...',
    onSearch,
    onClear,
    filters = [],
    className = ''
}) => {
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedFilters, setSelectedFilters] = useState({});

    const handleSearch = (value) => {
        setSearchTerm(value);
        onSearch && onSearch(value, selectedFilters);
    };

    const handleClear = () => {
        setSearchTerm('');
        setSelectedFilters({});
        onClear && onClear();
    };

    const handleFilterChange = (filterKey, value) => {
        const newFilters = { ...selectedFilters, [filterKey]: value };
        setSelectedFilters(newFilters);
        onSearch && onSearch(searchTerm, newFilters);
    };

    return (
        <div className={`flex flex-col sm:flex-row gap-3 ${className}`}>
            {/* Search Input */}
            <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                    type="text"
                    placeholder={placeholder}
                    value={searchTerm}
                    onChange={(e) => handleSearch(e.target.value)}
                    className="pl-10 pr-10"
                />
                {searchTerm && (
                    <button
                        onClick={handleClear}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-slate-600"
                    >
                        <X className="w-4 h-4" />
                    </button>
                )}
            </div>

            {/* Filter Dropdowns */}
            {filters.map((filter) => (
                <Select
                    key={filter.key}
                    value={selectedFilters[filter.key] || ''}
                    onValueChange={(value) => handleFilterChange(filter.key, value)}
                >
                    <SelectTrigger className="w-full sm:w-[180px]">
                        <SelectValue placeholder={filter.label} />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="">All {filter.label}</SelectItem>
                        {filter.options.map((option) => (
                            <SelectItem key={option.value} value={option.value}>
                                {option.label}
                            </SelectItem>
                        ))}
                    </SelectContent>
                </Select>
            ))}

            {/* Clear All Button */}
            {(searchTerm || Object.keys(selectedFilters).length > 0) && (
                <Button
                    variant="ghost"
                    onClick={handleClear}
                    className="whitespace-nowrap"
                >
                    Clear All
                </Button>
            )}
        </div>
    );
};

/**
 * Filter and sort data based on search term and filters
 */
export const filterData = (data, searchTerm, filters, searchFields = []) => {
    if (!data) return [];

    let filtered = [...data];

    // Apply search term
    if (searchTerm) {
        const term = searchTerm.toLowerCase();
        filtered = filtered.filter((item) => {
            // Search in specified fields or all string fields
            const fieldsToSearch = searchFields.length > 0
                ? searchFields
                : Object.keys(item).filter(key => typeof item[key] === 'string');

            return fieldsToSearch.some(field => {
                const value = item[field];
                return value && String(value).toLowerCase().includes(term);
            });
        });
    }

    // Apply filters
    Object.entries(filters || {}).forEach(([key, value]) => {
        if (value) {
            filtered = filtered.filter(item => {
                if (typeof item[key] === 'string') {
                    return item[key].toLowerCase() === value.toLowerCase();
                }
                return item[key] === value;
            });
        }
    });

    return filtered;
};

export default SearchBar;
