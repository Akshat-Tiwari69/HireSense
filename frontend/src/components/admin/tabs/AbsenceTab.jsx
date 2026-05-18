import React from 'react';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { Label } from '../../ui/label';
import { TabsContent } from '../../ui/tabs';
import { AlertTriangle, RefreshCw, Loader2, CheckCircle, Edit, Trash2 } from 'lucide-react';

const AbsenceTab = ({
  absenceCandidates,
  absenceLoading,
  absenceEditing,
  absenceForm,
  setAbsenceForm,
  absenceSaving,
  fetchAbsenceCandidates,
  startEditAbsence,
  cancelEditAbsence,
  saveAbsenceDetails,
  handleDeleteCandidate,
}) => (
  <TabsContent value="absence-details">
    <Card className="bg-white border-none shadow-md">
      <CardHeader className="border-b border-slate-200 pb-4 flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2 text-slate-900">
            <AlertTriangle className="w-5 h-5 text-orange-500" />
            Candidates with Missing Details ({absenceCandidates.length})
          </CardTitle>
          <CardDescription className="text-slate-600">These candidates were uploaded but had critical information missing from their resume. Click Edit to fill in the details and move them to Applied status.</CardDescription>
        </div>
        <Button variant="outline" size="sm" onClick={fetchAbsenceCandidates} disabled={absenceLoading}>
          <RefreshCw className={`w-4 h-4 mr-1 ${absenceLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </CardHeader>
      <CardContent className="pt-4">
        {absenceLoading ? (
          <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-orange-500" /></div>
        ) : absenceCandidates.length === 0 ? (
          <div className="text-center py-12 text-slate-500">
            <CheckCircle className="w-12 h-12 mx-auto mb-3 text-green-300" />
            <p className="font-medium text-green-700">All good!</p>
            <p className="text-sm mt-1">No candidates with missing details</p>
          </div>
        ) : (
          <div className="space-y-3">
            {absenceCandidates.map(c => (
              <div key={c.id} className="border border-orange-200 rounded-lg p-4 bg-orange-50/30 hover:shadow-md transition-all">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3 flex-1">
                    <div className="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center text-orange-600 font-bold text-sm">
                      #{c.id}
                    </div>
                    <div className="flex-1">
                      {absenceEditing === c.id ? (
                        <div className="space-y-3">
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                            <div className="space-y-1">
                              <Label className="text-xs font-medium text-slate-600">Name *</Label>
                              <Input
                                value={absenceForm.name}
                                onChange={e => setAbsenceForm(f => ({ ...f, name: e.target.value }))}
                                placeholder="Full name"
                                className={`h-8 text-sm ${c.missing_fields?.includes('name') ? 'border-orange-300 bg-orange-50' : ''}`}
                              />
                            </div>
                            <div className="space-y-1">
                              <Label className="text-xs font-medium text-slate-600">Email *</Label>
                              <Input
                                value={absenceForm.email}
                                onChange={e => setAbsenceForm(f => ({ ...f, email: e.target.value }))}
                                placeholder="email@example.com"
                                className={`h-8 text-sm ${c.missing_fields?.includes('email') ? 'border-orange-300 bg-orange-50' : ''}`}
                              />
                            </div>
                            <div className="space-y-1">
                              <Label className="text-xs font-medium text-slate-600">Phone</Label>
                              <Input
                                value={absenceForm.phone}
                                onChange={e => setAbsenceForm(f => ({ ...f, phone: e.target.value }))}
                                placeholder="+91 98765 43210"
                                className="h-8 text-sm"
                              />
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <Button size="sm" onClick={() => saveAbsenceDetails(c.id)} disabled={absenceSaving}
                              className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 h-7 text-xs">
                              {absenceSaving ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <CheckCircle className="w-3 h-3 mr-1" />}
                              Save & Mark Applied
                            </Button>
                            <Button variant="ghost" size="sm" onClick={cancelEditAbsence} className="h-7 text-xs">Cancel</Button>
                          </div>
                        </div>
                      ) : (
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-semibold text-slate-800">{c.name}</span>
                            <span className="text-sm text-slate-500">{c.email}</span>
                            {c.job_title && c.job_title !== 'N/A' && (
                              <Badge variant="outline" className="text-xs border-indigo-200 text-indigo-600">{c.job_title}</Badge>
                            )}
                            {c.match_score > 0 && (
                              <Badge variant="outline" className="text-xs">{c.match_score}% match</Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-2 mt-2 flex-wrap">
                            <span className="text-xs font-medium text-orange-700">Missing:</span>
                            {c.missing_fields?.map(field => (
                              <Badge key={field} className="bg-orange-100 text-orange-800 text-xs capitalize hover:bg-orange-100">
                                {field}
                              </Badge>
                            ))}
                            {c.created_at && (
                              <span className="text-xs text-slate-400 ml-2">
                                Uploaded {new Date(c.created_at).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  {absenceEditing !== c.id && (
                    <div className="flex items-center gap-1 ml-3">
                      <Button variant="outline" size="sm" onClick={() => startEditAbsence(c)}
                        className="h-8 text-xs border-orange-200 text-orange-700 hover:bg-orange-50">
                        <Edit className="w-3.5 h-3.5 mr-1" />
                        Edit & Fix
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => handleDeleteCandidate(c.id)}
                        className="h-8 text-xs hover:text-red-600" title="Delete candidate">
                        <Trash2 className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  </TabsContent>
);

export default AbsenceTab;
