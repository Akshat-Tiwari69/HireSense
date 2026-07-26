import { Badge } from '../../ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/table';
import { TabsContent } from '../../ui/tabs';
import StatusBadge from '../../workspace/StatusBadge';
import { Mail } from 'lucide-react';

const formatEmailType = (emailType) => (
  emailType
    ? emailType.split('_').map((word) => `${word.charAt(0).toUpperCase()}${word.slice(1)}`).join(' ')
    : 'Unknown'
);

const EmailLogsTab = ({ emailLogs }) => (
  <TabsContent value="email-logs">
    <Card>
      <CardHeader className="border-b">
        <CardTitle>Email activity</CardTitle>
        <CardDescription>Delivery history for candidate and staff notifications.</CardDescription>
      </CardHeader>
      <CardContent className="pt-5">
        {emailLogs.length === 0 ? (
          <div className="flex min-h-56 flex-col items-center justify-center rounded-lg border border-dashed px-6 text-center">
            <span className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-muted text-muted-foreground">
              <Mail className="h-5 w-5" />
            </span>
            <p className="font-medium text-foreground">No email activity yet</p>
            <p className="mt-1 text-sm text-muted-foreground">Notification delivery attempts will appear here.</p>
          </div>
        ) : (
          <Table className="min-w-[860px]" aria-label="Email delivery activity">
            <TableHeader>
              <TableRow>
                <TableHead>Sent at</TableHead>
                <TableHead>Recipient</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Subject</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {emailLogs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="whitespace-nowrap text-xs text-muted-foreground">
                    {new Date(log.sent_at).toLocaleString()}
                  </TableCell>
                  <TableCell>
                    <p className="font-medium text-foreground">{log.recipient_name || 'Unnamed recipient'}</p>
                    <p className="mt-0.5 text-xs text-muted-foreground">{log.recipient_email}</p>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="border-slate-200 bg-slate-50 text-slate-700">
                      {formatEmailType(log.email_type)}
                    </Badge>
                  </TableCell>
                  <TableCell className="max-w-xs truncate text-foreground" title={log.subject}>
                    {log.subject || 'No subject'}
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={log.status || 'unknown'} />
                    {log.status !== 'sent' && log.error_message ? (
                      <p className="mt-1 max-w-[220px] truncate text-xs text-red-700" title={log.error_message}>
                        {log.error_message}
                      </p>
                    ) : null}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  </TabsContent>
);

export default EmailLogsTab;
