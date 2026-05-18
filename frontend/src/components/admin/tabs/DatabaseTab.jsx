import React from 'react';
import { Button } from '../../ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/table';
import { TabsContent } from '../../ui/tabs';
import { Table as TableIcon } from 'lucide-react';

const DatabaseTab = ({
  dbTables,
  selectedTable,
  tableData,
  fetchTableData,
}) => (
  <TabsContent value="database">
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      <Card className="bg-white border-none shadow-md hover:shadow-xl transition-all duration-300">
        <CardHeader>
          <CardTitle className="text-slate-900 text-lg">Tables</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {dbTables.map((table) => (
            <Button
              key={table}
              variant={selectedTable === table ? 'default' : 'outline'}
              className={`w-full justify-start ${selectedTable === table ? 'bg-indigo-600' : 'border-slate-300 text-slate-700 hover:bg-slate-50'}`}
              onClick={() => fetchTableData(table)}
            >
              <TableIcon className="w-4 h-4 mr-2" />
              {table}
            </Button>
          ))}
        </CardContent>
      </Card>

      <Card className="bg-white border-none shadow-md hover:shadow-xl transition-all duration-300 lg:col-span-3">
        <CardHeader>
          <CardTitle className="text-slate-900">
            {selectedTable ? `Table: ${selectedTable}` : 'Select a table'}
          </CardTitle>
          <CardDescription className="text-slate-600">
            {selectedTable ? `Showing ${tableData.data.length} rows` : 'Click a table to view its data'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {selectedTable && tableData.columns.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-200">
                    {tableData.columns.map((col) => (
                      <TableHead key={col} className="text-slate-700 whitespace-nowrap">{col}</TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tableData.data.map((row, idx) => (
                    <TableRow key={idx} className="border-slate-200">
                      {tableData.columns.map((col) => (
                        <TableCell key={col} className="text-slate-700 max-w-xs truncate">
                          {row[col] !== null ? String(row[col]).substring(0, 50) : 'NULL'}
                          {String(row[col] || '').length > 50 && '...'}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <p className="text-slate-600 text-center py-8">Select a table from the left to view its data</p>
          )}
        </CardContent>
      </Card>
    </div>
  </TabsContent>
);

export default DatabaseTab;
