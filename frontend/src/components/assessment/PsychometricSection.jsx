import { Check, ChevronLeft, ChevronRight, LoaderCircle } from 'lucide-react';

import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { RadioGroup, RadioGroupItem } from '../ui/radio-group';

const PsychometricSection = ({
  scenarios,
  currentQuestion,
  psychometricAnswers,
  onAnswer,
  onPrevSection,
  onSubmit,
  isSubmitting,
  setCurrentQuestion,
  savingQuestionId,
}) => {
  if (!scenarios?.length) {
    return <p className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">No work-style scenarios are assigned.</p>;
  }

  const scenario = scenarios[currentQuestion];
  if (!scenario) return null;

  const answeredCount = scenarios.filter(({ id }) => psychometricAnswers[id] !== undefined).length;
  const selectedAnswer = psychometricAnswers[scenario.id];
  const progress = (answeredCount / scenarios.length) * 100;

  return (
    <section className="space-y-6" aria-labelledby="work-style-heading">
      <div>
        <p className="text-xs font-medium uppercase tracking-[0.14em] text-slate-500">Work style</p>
        <h2 id="work-style-heading" className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">
          Scenario {currentQuestion + 1} of {scenarios.length}
        </h2>
        <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-slate-100" aria-hidden="true">
          <div className="h-full rounded-full bg-blue-600" style={{ width: `${progress}%` }} />
        </div>
        <p className="mt-2 text-xs text-slate-500">{answeredCount} of {scenarios.length} answered</p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7">
        <p className="text-base font-medium leading-7 text-slate-950 sm:text-lg">{scenario.scenario}</p>
        <p className="mt-3 text-sm text-slate-500">Choose the response closest to how you would act.</p>
        <RadioGroup
          className="mt-6 space-y-3"
          value={selectedAnswer === undefined ? '' : String(selectedAnswer)}
          onValueChange={(value) => onAnswer(scenario.id, Number(value))}
          aria-label={`Responses for scenario ${currentQuestion + 1}`}
        >
          {scenario.options?.map((option, index) => {
            const optionId = `work-style-${scenario.id}-${index}`;
            const selected = selectedAnswer === index;
            return (
              <Label
                key={optionId}
                htmlFor={optionId}
                className={`flex cursor-pointer items-start gap-3 rounded-lg border p-4 text-sm font-normal leading-6 transition-colors ${
                  selected
                    ? 'border-blue-500 bg-blue-50/70 text-slate-950'
                    : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                }`}
              >
                <RadioGroupItem id={optionId} value={String(index)} className="mt-1" />
                <span>{option}</span>
              </Label>
            );
          })}
        </RadioGroup>
        {savingQuestionId === scenario.id && (
          <p className="mt-3 text-xs text-slate-500" role="status">Saving response…</p>
        )}
      </div>

      <div className="flex flex-col-reverse justify-between gap-3 sm:flex-row">
        {currentQuestion > 0 ? (
          <Button type="button" variant="outline" onClick={() => setCurrentQuestion((value) => value - 1)}>
            <ChevronLeft className="mr-2 h-4 w-4" />
            Previous scenario
          </Button>
        ) : (
          <Button type="button" variant="outline" onClick={onPrevSection}>
            <ChevronLeft className="mr-2 h-4 w-4" />
            Previous section
          </Button>
        )}

        {currentQuestion < scenarios.length - 1 ? (
          <Button type="button" onClick={() => setCurrentQuestion((value) => value + 1)}>
            Next scenario
            <ChevronRight className="ml-2 h-4 w-4" />
          </Button>
        ) : (
          <Button type="button" onClick={onSubmit} disabled={isSubmitting}>
            {isSubmitting ? <LoaderCircle className="mr-2 h-4 w-4 animate-spin" /> : <Check className="mr-2 h-4 w-4" />}
            Submit assessment
          </Button>
        )}
      </div>
    </section>
  );
};

export default PsychometricSection;
