import { Badge } from '../../ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/table';
import { TabsContent } from '../../ui/tabs';
import { ShieldCheck } from 'lucide-react';

const formatAction = (action) => String(action || 'unknown').replace(/_/g, ' ');

const AuditLogTab = ({ auditLogs }) => (
  <TabsContent value="audit-log">
    <Card>
      <CardHeader className="border-b">
        <CardTitle>Audit trail</CardTitle>
        <CardDescription>Review recorded role, sector, and candidate-matching actions.</CardDescription>
      </CardHeader>
      <CardContent className="pt-5">
        {auditLogs.length === 0 ? (
          <div className="flex min-h-56 flex-col items-center justify-center rounded-lg border border-dashed px-6 text-center">
            <span className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-muted text-muted-foreground">
              <ShieldCheck className="h-5 w-5" />
            </span>
            <p className="font-medium text-foreground">No audit entries found</p>
            <p className="mt-1 text-sm text-muted-foreground">Role, sector, and matching actions will appear here.</p>
          </div>
        ) : (
          <Table className="min-w-[920px]" aria-label="Administrative audit trail">
            <TableHeader>
              <TableRow>
                <TableHead>Time</TableHead>
                <TableHead>Actor</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead>Details</TableHead>
                <TableHead>IP address</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {auditLogs.map((log) => {
                const details = log.details ? JSON.stringify(log.details) : '';
                return (
                  <TableRow key={log.id}>
                    <TableCell className="whitespace-nowrap text-xs text-muted-foreground">
                      {new Date(log.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-sm text-foreground">{log.user_email || 'System'}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="border-slate-200 bg-slate-50 text-slate-700 capitalize">
                        {formatAction(log.action)}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-foreground">
                      {log.entity_type ? `${log.entity_type} #${log.entity_id}` : '—'}
                    </TableCell>
                    <TableCell className="max-w-[280px] truncate text-xs text-muted-foreground" title={details}>
                      {details || '—'}
                    </TableCell>
                    <TableCell className="whitespace-nowrap font-mono text-xs text-muted-foreground">{log.ip_address || '—'}</TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  </TabsContent>
);

export default AuditLogTab;
