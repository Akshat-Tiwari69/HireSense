import React from 'react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../ui/dialog';
import { BarChart3, CheckCircle, ThumbsUp, ThumbsDown, Users, Download, XCircle, AlertCircle, Loader } from 'lucide-react';

const CandidateDetailsModal = ({
  open,
  onOpenChange,
  selectedCandidate,
  assessmentDetails,
  decisionLoading,
  onDownloadResume,
  onFinalDecision,
}) => (
  <Dialog open={open} onOpenChange={onOpenChange}>
    <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
      <div className="absolute top-0 left-0 right-0 h-2 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-t-lg" />
      <DialogHeader className="pt-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-xl shadow-lg">
              {selectedCandidate?.name?.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
            </div>
            <div>
              <DialogTitle className="text-2xl font-bold text-slate-800">{selectedCandidate?.name}</DialogTitle>
              <DialogDescription className="text-slate-600 flex items-center gap-2 mt-1">
                {selectedCandidate?.email}
                {selectedCandidate?.status && (
                  <Badge variant="outline" className={`ml-2 ${
                    selectedCandidate.status === 'Completed' ? 'bg-indigo-100 text-indigo-700 border-indigo-200' :
                    selectedCandidate.status === 'Hired' ? 'bg-emerald-100 text-emerald-700 border-emerald-200' :
                    selectedCandidate.status === 'Rejected' ? 'bg-red-100 text-red-700 border-red-200' :
                    'bg-slate-100 text-slate-700 border-slate-200'
                  }`}>
                    {selectedCandidate.status}
                  </Badge>
                )}
              </DialogDescription>
            </div>
          </div>
          <Button
            size="sm"
            variant="outline"
            className="border-indigo-200 text-indigo-700 hover:bg-indigo-50"
            onClick={() => onDownloadResume(selectedCandidate?.id)}
          >
            <Download className="w-4 h-4 mr-1" />
            Resume
          </Button>
        </div>
      </DialogHeader>

      {selectedCandidate && (
        <div className="space-y-6 mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* AI Match Score */}
            <div>
              <h3 className="font-semibold text-lg mb-3 flex items-center gap-2">
                <div className="p-1.5 bg-indigo-100 rounded-lg">
                  <BarChart3 className="w-4 h-4 text-indigo-600" />
                </div>
                AI Match Score
              </h3>
              <div className="bg-gradient-to-br from-indigo-50 to-purple-50 p-5 rounded-xl border border-indigo-100 shadow-sm">
                <div className="text-5xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent mb-3">
                  {selectedCandidate.aiMatchScore}%
                </div>
                <div className="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-indigo-500 to-purple-500 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${selectedCandidate.aiMatchScore}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Assessment Results */}
            {assessmentDetails && (
              <div>
                <h3 className="font-semibold text-lg mb-3 flex items-center gap-2">
                  <div className="p-1.5 bg-purple-100 rounded-lg">
                    <CheckCircle className="w-4 h-4 text-purple-600" />
                  </div>
                  Assessment Results
                </h3>
                {assessmentDetails.decision && (
                  <div className={`mb-4 px-4 py-3 rounded-xl font-bold text-center shadow-sm ${
                    assessmentDetails.decision.toLowerCase().includes('recommend')
                      ? 'bg-gradient-to-r from-emerald-50 to-green-50 text-emerald-700 border border-emerald-200'
                      : assessmentDetails.decision.toLowerCase().includes('consider')
                        ? 'bg-gradient-to-r from-blue-50 to-indigo-50 text-blue-700 border border-blue-200'
                        : 'bg-gradient-to-r from-red-50 to-pink-50 text-red-700 border border-red-200'
                  }`}>
                    {assessmentDetails.decision}
                  </div>
                )}
                <div className="bg-gradient-to-br from-purple-50 to-indigo-50 p-4 rounded-xl border border-purple-100 shadow-sm space-y-3">
                  {[
                    { label: 'Technical Score', value: assessmentDetails.technical_score, color: 'bg-purple-500', textColor: 'text-purple-700' },
                    { label: 'Psychometric Score', value: assessmentDetails.psychometric_score, color: 'bg-indigo-500', textColor: 'text-indigo-700' },
                  ].map(({ label, value, color, textColor }) => (
                    <div key={label} className="flex justify-between items-center">
                      <span className="text-slate-600 text-sm">{label}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-20 bg-slate-200 rounded-full h-2">
                          <div className={`${color} h-2 rounded-full transition-all`} style={{ width: `${value || 0}%` }} />
                        </div>
                        <span className={`font-bold ${textColor} w-12 text-right`}>{Math.round(value) || 0}%</span>
                      </div>
                    </div>
                  ))}
                  <div className="border-t border-purple-200 pt-3 flex justify-between items-center">
                    <span className="text-slate-800 font-semibold">Overall Score</span>
                    <span className="font-bold text-2xl bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent">
                      {Math.round(assessmentDetails.overall_score) || 0}%
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Strengths */}
          <div className="mt-2">
            <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
              <div className="p-2 bg-emerald-100 rounded-lg">
                <ThumbsUp className="w-5 h-5 text-emerald-600" />
              </div>
              Strengths
            </h3>
            <ul className="space-y-3">
              {(selectedCandidate.pros || []).length === 0 ? (
                <li className="text-slate-500 italic p-4 bg-slate-50 rounded-xl text-center">No strengths data available</li>
              ) : (selectedCandidate.pros || []).map((pro, idx) => (
                <li key={idx} className="flex items-start gap-3 bg-gradient-to-r from-emerald-50 to-green-50 p-4 rounded-xl border border-emerald-100 shadow-sm">
                  <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                  <span className="text-slate-700">{pro}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Considerations */}
          <div className="mt-6">
            <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
              <div className="p-2 bg-amber-100 rounded-lg">
                <ThumbsDown className="w-5 h-5 text-amber-600" />
              </div>
              Areas for Consideration
            </h3>
            <ul className="space-y-3">
              {(selectedCandidate.cons || []).length === 0 ? (
                <li className="text-slate-500 italic p-4 bg-slate-50 rounded-xl text-center">No considerations data available</li>
              ) : (selectedCandidate.cons || []).map((con, idx) => (
                <li key={idx} className="flex items-start gap-3 bg-gradient-to-r from-amber-50 to-orange-50 p-4 rounded-xl border border-amber-100 shadow-sm">
                  <XCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                  <span className="text-slate-700">{con}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Final Decision */}
          {selectedCandidate.status === 'Completed' && assessmentDetails && (
            <div className="border-t border-slate-200 pt-6 mt-6">
              <div className="bg-gradient-to-r from-slate-50 to-indigo-50 rounded-xl p-6 border border-slate-200">
                <h3 className="font-semibold text-lg mb-4 text-center flex items-center justify-center gap-2">
                  <div className="p-1.5 bg-indigo-100 rounded-lg">
                    <Users className="w-4 h-4 text-indigo-600" />
                  </div>
                  Final Hiring Decision
                </h3>
                <div className="flex justify-center gap-4">
                  {[
                    { decision: 'no-hire', label: 'No-Hire', icon: XCircle, gradient: 'from-red-500 to-red-600 hover:from-red-600 hover:to-red-700' },
                    { decision: 'hire', label: 'Hire', icon: CheckCircle, gradient: 'from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700' },
                  ].map(({ decision, label, icon: Icon, gradient }) => (
                    <Button
                      key={decision}
                      size="lg"
                      className={`w-36 bg-gradient-to-r ${gradient} text-white shadow-md`}
                      onClick={() => onFinalDecision(decision)}
                      disabled={decisionLoading}
                    >
                      {decisionLoading ? <Loader className="w-4 h-4 animate-spin" /> : (
                        <><Icon className="w-4 h-4 mr-2" />{label}</>
                      )}
                    </Button>
                  ))}
                </div>
                <p className="text-center text-sm text-slate-500 mt-4 flex items-center justify-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  This will send a final status email to the candidate.
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </DialogContent>
  </Dialog>
);

export default CandidateDetailsModal;
