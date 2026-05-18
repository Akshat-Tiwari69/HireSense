import React from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '../ui/dialog';
import { Calendar, Clock, Code, CheckCircle, XCircle, FileText, Upload, BookOpen, Loader } from 'lucide-react';

const ScheduleModal = ({
  open,
  onOpenChange,
  selectedCandidate,
  scheduleDate,
  setScheduleDate,
  scheduleTime,
  setScheduleTime,
  isTechnicalRole,
  setIsTechnicalRole,
  customQFile,
  setCustomQFile,
  customQUploading,
  schedulingLoading,
  onSchedule,
}) => (
  <Dialog open={open} onOpenChange={onOpenChange}>
    <DialogContent className="sm:max-w-md">
      <div className="absolute top-0 left-0 right-0 h-2 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-t-lg" />
      <DialogHeader className="pt-4">
        <DialogTitle className="flex items-center gap-3 text-xl">
          <div className="p-2 bg-indigo-100 rounded-lg">
            <Calendar className="w-5 h-5 text-indigo-600" />
          </div>
          Schedule Assessment
        </DialogTitle>
        <DialogDescription className="text-slate-600">
          Choose date and time for <span className="font-semibold text-slate-800">{selectedCandidate?.name}</span>'s assessment
        </DialogDescription>
      </DialogHeader>

      <div className="space-y-5 py-4">
        <div className="space-y-2">
          <Label htmlFor="date" className="text-sm font-medium text-slate-700 flex items-center gap-2">
            <Calendar className="w-4 h-4 text-slate-500" />
            Select Date
          </Label>
          <Input
            id="date"
            type="date"
            value={scheduleDate}
            onChange={(e) => setScheduleDate(e.target.value)}
            min={new Date().toISOString().split('T')[0]}
            className="border-slate-200 focus:border-indigo-500 focus:ring-indigo-500"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="time" className="text-sm font-medium text-slate-700 flex items-center gap-2">
            <Clock className="w-4 h-4 text-slate-500" />
            Select Time
          </Label>
          <Input
            id="time"
            type="time"
            value={scheduleTime}
            onChange={(e) => setScheduleTime(e.target.value)}
            className="border-slate-200 focus:border-indigo-500 focus:ring-indigo-500"
          />
        </div>

        <div
          className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-100 hover:border-indigo-200 transition-colors cursor-pointer"
          onClick={() => setIsTechnicalRole(!isTechnicalRole)}
        >
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${isTechnicalRole ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-200 text-slate-500'}`}>
              <Code className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-semibold text-slate-800">Technical Role</div>
              <div className="text-xs text-slate-500">{isTechnicalRole ? 'Includes Coding & MCQ' : 'MCQ Only (Non-Technical)'}</div>
            </div>
          </div>
          <div className={`w-12 h-6 rounded-full transition-colors relative ${isTechnicalRole ? 'bg-indigo-600' : 'bg-slate-300'}`}>
            <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${isTechnicalRole ? 'left-7' : 'left-1'}`} />
          </div>
        </div>

        <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
          <div className="flex items-center gap-2 mb-2">
            <BookOpen className="w-4 h-4 text-indigo-500" />
            <span className="text-sm font-semibold text-slate-700">Custom Questions (Optional)</span>
          </div>
          <p className="text-xs text-slate-500 mb-2">Upload a PDF/DOCX with your own questions. AI will blend them into the assessment.</p>
          <div
            className={`border border-dashed rounded-md p-3 text-center cursor-pointer transition-colors ${customQFile ? 'border-indigo-400 bg-indigo-50' : 'border-slate-300 hover:border-indigo-300'}`}
            onClick={() => document.getElementById('schedule-qb-file').click()}
          >
            <input
              id="schedule-qb-file"
              type="file"
              accept=".pdf,.docx"
              className="hidden"
              onChange={(e) => setCustomQFile(e.target.files[0] || null)}
            />
            {customQFile ? (
              <div className="flex items-center justify-center gap-2 text-sm text-indigo-700">
                <FileText className="w-4 h-4" />
                <span className="font-medium">{customQFile.name}</span>
                <button onClick={(e) => { e.stopPropagation(); setCustomQFile(null); }} className="ml-1 text-slate-400 hover:text-red-500">
                  <XCircle className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : (
              <div className="flex items-center justify-center gap-2 text-xs text-slate-400">
                <Upload className="w-4 h-4" />
                <span>Drop PDF/DOCX or click to browse</span>
              </div>
            )}
          </div>
        </div>

        {scheduleDate && scheduleTime && (
          <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-3 flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-indigo-600" />
            <div className="text-sm">
              <span className="text-slate-600">Scheduled for: </span>
              <span className="font-semibold text-indigo-700">
                {new Date(`${scheduleDate}T${scheduleTime}`).toLocaleString('en-US', {
                  weekday: 'long', month: 'short', day: 'numeric',
                  hour: 'numeric', minute: '2-digit'
                })}
              </span>
            </div>
          </div>
        )}
      </div>

      <DialogFooter className="gap-2 sm:gap-0">
        <Button variant="outline" onClick={() => onOpenChange(false)} disabled={schedulingLoading} className="border-slate-200">
          Cancel
        </Button>
        <Button
          onClick={onSchedule}
          className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 min-w-[150px] shadow-md"
          disabled={schedulingLoading}
        >
          {schedulingLoading ? (
            <Loader className="w-4 h-4 animate-spin" />
          ) : (
            <>
              <Calendar className="mr-2 w-4 h-4" />
              Confirm Schedule
            </>
          )}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
);

export default ScheduleModal;
