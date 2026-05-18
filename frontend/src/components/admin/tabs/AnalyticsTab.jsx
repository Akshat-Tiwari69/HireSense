import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { TabsContent } from '../../ui/tabs';

const AnalyticsTab = ({ analytics }) => (
  <TabsContent value="analytics">
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Candidate Analytics */}
      <Card className="bg-white border-none shadow-md hover:shadow-xl transition-all duration-300">
        <CardHeader>
          <CardTitle className="text-slate-900">Candidate Statistics</CardTitle>
          <CardDescription className="text-slate-600">Overview of candidate pipeline</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-slate-900/50 p-4 rounded-lg">
              <div className="text-3xl font-bold text-slate-900">{analytics.candidates?.total || 0}</div>
              <div className="text-sm text-slate-600">Total Candidates</div>
            </div>
            <div className="bg-slate-900/50 p-4 rounded-lg">
              <div className="text-3xl font-bold text-blue-400">{analytics.candidates?.this_month || 0}</div>
              <div className="text-sm text-slate-600">This Month</div>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-slate-700">Pending</span>
              <Badge className="bg-yellow-600">{analytics.candidates?.pending || 0}</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-700">Under Review</span>
              <Badge className="bg-blue-600">{analytics.candidates?.under_review || 0}</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-700">Hired</span>
              <Badge className="bg-green-600">{analytics.candidates?.hired || 0}</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-700">Rejected</span>
              <Badge className="bg-red-600">{analytics.candidates?.rejected || 0}</Badge>
            </div>
          </div>
          <div className="pt-4 border-t border-slate-200">
            <div className="flex justify-between items-center">
              <span className="text-slate-700">Avg. Match Score</span>
              <span className="text-2xl font-bold text-indigo-400">{analytics.candidates?.avg_match_score || 0}%</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Assessment Analytics */}
      <Card className="bg-white border-none shadow-md hover:shadow-xl transition-all duration-300">
        <CardHeader>
          <CardTitle className="text-slate-900">Assessment Statistics</CardTitle>
          <CardDescription className="text-slate-600">Assessment performance metrics</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-slate-900/50 p-4 rounded-lg">
              <div className="text-3xl font-bold text-slate-900">{analytics.assessments?.total || 0}</div>
              <div className="text-sm text-slate-600">Total Assessments</div>
            </div>
            <div className="bg-slate-900/50 p-4 rounded-lg">
              <div className="text-3xl font-bold text-purple-400">{analytics.assessments?.this_month || 0}</div>
              <div className="text-sm text-slate-600">This Month</div>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-slate-700">Scheduled</span>
              <Badge className="bg-yellow-600">{analytics.assessments?.scheduled || 0}</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-700">In Progress</span>
              <Badge className="bg-blue-600">{analytics.assessments?.in_progress || 0}</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-700">Completed</span>
              <Badge className="bg-green-600">{analytics.assessments?.completed || 0}</Badge>
            </div>
          </div>
          <div className="pt-4 border-t border-slate-200 space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-slate-700">Avg. Technical Score</span>
              <span className="text-xl font-bold text-green-400">{analytics.assessments?.avg_technical_score || 0}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-700">Avg. Psychometric Score</span>
              <span className="text-xl font-bold text-purple-400">{analytics.assessments?.avg_psychometric_score || 0}%</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  </TabsContent>
);

export default AnalyticsTab;
