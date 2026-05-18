import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/table';
import { Badge } from '../../ui/badge';
import { TabsContent } from '../../ui/tabs';

const AuditLogTab = ({ auditLogs }) => (
  <TabsContent value="audit-log">
    <Card className="bg-white border-none shadow-md hover:shadow-xl transition-all duration-300">
      <CardHeader>
        <CardTitle className="text-slate-900">Audit Log</CardTitle>
        <CardDescription className="text-slate-600">Track all user actions — job postings, candidate matching, status changes</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow className="border-slate-200">
              <TableHead className="text-slate-700">Time</TableHead>
              <TableHead className="text-slate-700">User</TableHead>
              <TableHead className="text-slate-700">Action</TableHead>
              <TableHead className="text-slate-700">Entity</TableHead>
              <TableHead className="text-slate-700">Details</TableHead>
              <TableHead className="text-slate-700">IP</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {auditLogs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-slate-500">
                  No audit log entries found
                </TableCell>
              </TableRow>
            ) : (
              auditLogs.map((log) => (
                <TableRow key={log.id} className="border-slate-200">
                  <TableCell className="text-slate-600 text-xs">
                    {new Date(log.created_at).toLocaleString()}
                  </TableCell>
                  <TableCell className="text-slate-700 text-sm">{log.user_email || 'System'}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="border-slate-300 text-slate-700">
                      {(log.action || '').replace(/_/g, ' ')}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-slate-700 text-sm">
                    {log.entity_type && `${log.entity_type} #${log.entity_id}`}
                  </TableCell>
                  <TableCell className="text-slate-600 text-xs max-w-[200px] truncate" title={JSON.stringify(log.details)}>
                    {log.details ? JSON.stringify(log.details).substring(0, 60) : '—'}
                  </TableCell>
                  <TableCell className="text-slate-500 text-xs">{log.ip_address || '—'}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  </TabsContent>
);

export default AuditLogTab;
