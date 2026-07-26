import { Calendar, CheckCircle, Clock, Code, Loader } from 'lucide-react';

import { Button } from '../ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Input } from '../ui/input';
import { Label } from '../ui/label';

const getLocalDateInputValue = (date) => {
  const localDate = new Date(date.getTime() - (date.getTimezoneOffset() * 60_000));
  return localDate.toISOString().slice(0, 10);
};

const getLocalTimeInputValue = (date) => [date.getHours(), date.getMinutes()]
  .map((value) => String(value).padStart(2, '0'))
  .join(':');

const ScheduleModal = ({
  open,
  onOpenChange,
  selectedCandidate,
  scheduleDate,
  setScheduleDate,
  scheduleTime,
  setScheduleTime,
  schedulingLoading,
  onSchedule,
}) => {
  const now = new Date();
  const today = getLocalDateInputValue(now);
  const earliestTime = scheduleDate === today ? getLocalTimeInputValue(now) : undefined;
  const scheduledDateTime = scheduleDate && scheduleTime
    ? new Date(`${scheduleDate}T${scheduleTime}`)
    : null;
  const isPastTime = Boolean(earliestTime && scheduleTime && scheduleTime < earliestTime);
  const hasValidSchedule = Boolean(
    scheduleDate
    && scheduleTime
    && scheduleDate >= today
    && !isPastTime,
  );

  const handleOpenChange = (nextOpen) => {
    if (!nextOpen && !schedulingLoading) {
      setScheduleDate('');
      setScheduleTime('');
    }
    onOpenChange(nextOpen);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader className="pr-8">
          <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-accent text-primary">
            <Calendar className="h-5 w-5" aria-hidden="true" />
          </div>
          <DialogTitle className="text-xl">Schedule assessment</DialogTitle>
          <DialogDescription>
            Set the assessment window and format for{' '}
            <span className="font-medium text-foreground">
              {selectedCandidate?.name || 'this candidate'}
            </span>.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5 py-2">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="assessment-date" className="flex items-center gap-2 text-sm font-medium">
                <Calendar className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                Date
              </Label>
              <Input
                id="assessment-date"
                type="date"
                value={scheduleDate}
                onChange={(event) => setScheduleDate(event.target.value)}
                min={today}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="assessment-time" className="flex items-center gap-2 text-sm font-medium">
                <Clock className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                Time
              </Label>
              <Input
                id="assessment-time"
                type="time"
                value={scheduleTime}
                onChange={(event) => setScheduleTime(event.target.value)}
                min={earliestTime}
                required
              />
              {isPastTime ? (
                <p className="text-xs text-destructive" role="alert">Choose a future time.</p>
              ) : null}
            </div>
          </div>

          <div
            aria-labelledby="assessment-format-label"
            aria-describedby="assessment-format-description"
            className="flex w-full items-center justify-between gap-4 rounded-xl border bg-card p-4 text-left"
          >
            <span className="flex min-w-0 items-center gap-3">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent text-primary">
                <Code className="h-5 w-5" aria-hidden="true" />
              </span>
              <span className="min-w-0">
                <span id="assessment-format-label" className="block text-sm font-semibold text-foreground">
                  Knowledge and workstyle assessment
                </span>
                <span id="assessment-format-description" className="mt-0.5 block text-xs text-muted-foreground">
                  Coding exercises are paused on this deployment; the standard assessment is ready.
                </span>
              </span>
            </span>
            <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">Ready</span>
          </div>

          {hasValidSchedule && scheduledDateTime ? (
            <div className="flex items-start gap-3 rounded-lg border border-emerald-200 bg-emerald-50 p-4" aria-live="polite">
              <CheckCircle className="mt-0.5 h-5 w-5 shrink-0 text-emerald-700" aria-hidden="true" />
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.12em] text-emerald-700">Assessment time</p>
                <time
                  dateTime={`${scheduleDate}T${scheduleTime}`}
                  className="mt-1 block text-sm font-medium text-emerald-950"
                >
                  {scheduledDateTime.toLocaleString(undefined, {
                    weekday: 'long',
                    month: 'short',
                    day: 'numeric',
                    hour: 'numeric',
                    minute: '2-digit',
                  })}
                </time>
              </div>
            </div>
          ) : null}
        </div>

        <DialogFooter className="gap-2 border-t pt-5 sm:space-x-0">
          <Button
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={schedulingLoading}
            className="w-full sm:w-auto"
          >
            Cancel
          </Button>
          <Button
            onClick={onSchedule}
            disabled={schedulingLoading || !hasValidSchedule}
            className="w-full min-w-[164px] sm:w-auto"
          >
            {schedulingLoading ? (
              <>
                <Loader className="animate-spin" aria-hidden="true" />
                Scheduling
              </>
            ) : (
              <>
                <Calendar aria-hidden="true" />
                Schedule assessment
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ScheduleModal;
