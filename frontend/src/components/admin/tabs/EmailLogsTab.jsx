import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/table';
import { Badge } from '../../ui/badge';
import { TabsContent } from '../../ui/tabs';

const EmailLogsTab = ({ emailLogs }) => (
  <TabsContent value="email-logs">
    <Card className="bg-white border-none shadow-md hover:shadow-lg transition-all duration-300">
      <CardHeader>
        <CardTitle className="text-slate-900">Email Logs</CardTitle>
        <CardDescription className="text-slate-600">History of system emails sent to candidates and users</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow className="border-slate-200">
              <TableHead className="text-slate-700">Time</TableHead>
              <TableHead className="text-slate-700">Recipient</TableHead>
              <TableHead className="text-slate-700">Type</TableHead>
              <TableHead className="text-slate-700">Subject</TableHead>
              <TableHead className="text-slate-700">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {emailLogs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8 text-slate-500">
                  No email logs found
                </TableCell>
              </TableRow>
            ) : (
              emailLogs.map((log) => (
                <TableRow key={log.id} className="border-slate-200">
                  <TableCell className="text-slate-600 text-xs">
                    {new Date(log.sent_at).toLocaleString()}
                  </TableCell>
                  <TableCell className="text-slate-700">
                    <div className="flex flex-col">
                      <span className="text-slate-900">{log.recipient_name}</span>
                      <span className="text-xs text-slate-500">{log.recipient_email}</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-slate-700">
                    <Badge variant="outline" className="border-slate-300 text-slate-700">
                      {log.email_type
                        ? log.email_type
                          .split('_')
                          .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                          .join(' ')
                        : 'Unknown'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-slate-700 max-w-xs truncate" title={log.subject}>
                    {log.subject}
                  </TableCell>
                  <TableCell>
                    {log.status === 'sent' ? (
                      <Badge className="bg-green-900 text-green-200 hover:bg-green-800">
                        Sent
                      </Badge>
                    ) : (
                      <div className="flex flex-col items-start gap-1">
                        <Badge className="bg-red-900 text-red-200 hover:bg-red-800">
                          Failed
                        </Badge>
                        <span className="text-xs text-red-400 max-w-[150px] truncate" title={log.error_message}>
                          {log.error_message}
                        </span>
                      </div>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  </TabsContent>
);

export default EmailLogsTab;
