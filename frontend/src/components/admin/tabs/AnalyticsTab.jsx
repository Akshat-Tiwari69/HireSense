import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../ui/card';
import { TabsContent } from '../../ui/tabs';
import StatusBadge from '../../workspace/StatusBadge';
import { ClipboardCheck, Users } from 'lucide-react';

const SummaryMetric = ({ label, value, accent = false }) => (
  <div className="rounded-lg border bg-slate-50/60 p-4">
    <p className={`text-3xl font-semibold tracking-tight tabular-nums ${accent ? 'text-blue-700' : 'text-foreground'}`}>{value || 0}</p>
    <p className="mt-1 text-sm text-muted-foreground">{label}</p>
  </div>
);

const BreakdownRow = ({ status, value }) => (
  <div className="flex items-center justify-between gap-4 border-b py-3 last:border-0">
    <StatusBadge status={status} />
    <span className="font-semibold tabular-nums text-foreground">{value || 0}</span>
  </div>
);

const AnalyticsTab = ({ analytics }) => (
  <TabsContent value="analytics">
    <div className="grid gap-5 xl:grid-cols-2">
      <Card>
        <CardHeader className="border-b">
          <div className="flex items-start gap-3">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-700">
              <Users className="h-4 w-4" />
            </span>
            <div className="space-y-1.5">
              <CardTitle>Candidate pipeline</CardTitle>
              <CardDescription>Current volume and movement across the hiring process.</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-5 pt-5">
          <div className="grid grid-cols-2 gap-3">
            <SummaryMetric label="Total candidates" value={analytics.candidates?.total} />
            <SummaryMetric label="Added this month" value={analytics.candidates?.this_month} accent />
          </div>
          <div aria-label="Candidate status breakdown">
            <BreakdownRow status="pending" value={analytics.candidates?.pending} />
            <BreakdownRow status="under review" value={analytics.candidates?.under_review} />
            <BreakdownRow status="hired" value={analytics.candidates?.hired} />
            <BreakdownRow status="rejected" value={analytics.candidates?.rejected} />
          </div>
          <div className="flex items-end justify-between gap-4 rounded-lg border border-blue-200 bg-blue-50 p-4">
            <div>
              <p className="text-sm font-medium text-blue-900">Average match score</p>
              <p className="mt-1 text-xs text-blue-700">Across all scored candidates</p>
            </div>
            <p className="text-2xl font-semibold tabular-nums text-blue-800">{analytics.candidates?.avg_match_score || 0}%</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="border-b">
          <div className="flex items-start gap-3">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-emerald-700">
              <ClipboardCheck className="h-4 w-4" />
            </span>
            <div className="space-y-1.5">
              <CardTitle>Assessment activity</CardTitle>
              <CardDescription>Session volume, completion, and average performance.</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-5 pt-5">
          <div className="grid grid-cols-2 gap-3">
            <SummaryMetric label="Total assessments" value={analytics.assessments?.total} />
            <SummaryMetric label="Created this month" value={analytics.assessments?.this_month} accent />
          </div>
          <div aria-label="Assessment status breakdown">
            <BreakdownRow status="scheduled" value={analytics.assessments?.scheduled} />
            <BreakdownRow status="in progress" value={analytics.assessments?.in_progress} />
            <BreakdownRow status="completed" value={analytics.assessments?.completed} />
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-lg border bg-slate-50/60 p-4">
              <p className="text-sm text-muted-foreground">Avg. technical score</p>
              <p className="mt-2 text-2xl font-semibold tabular-nums text-emerald-700">{analytics.assessments?.avg_technical_score || 0}%</p>
            </div>
            <div className="rounded-lg border bg-slate-50/60 p-4">
              <p className="text-sm text-muted-foreground">Avg. psychometric score</p>
              <p className="mt-2 text-2xl font-semibold tabular-nums text-blue-700">{analytics.assessments?.avg_psychometric_score || 0}%</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  </TabsContent>
);

export default AnalyticsTab;
