import { ChevronLeft, ChevronRight } from 'lucide-react';

import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { RadioGroup, RadioGroupItem } from '../ui/radio-group';

const MCQSection = ({
  questions,
  currentQuestion,
  mcqAnswers,
  onAnswer,
  onNextSection,
  setCurrentQuestion,
  savingQuestionId,
}) => {
  if (!questions?.length) {
    return <p className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">No knowledge questions are assigned.</p>;
  }

  const question = questions[currentQuestion];
  if (!question) return null;

  const answeredCount = questions.filter(({ id }) => mcqAnswers[id] !== undefined).length;
  const selectedAnswer = mcqAnswers[question.id];
  const progress = (answeredCount / questions.length) * 100;

  return (
    <section className="space-y-6" aria-labelledby="knowledge-question-heading">
      <div>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-slate-500">Knowledge check</p>
            <h2 id="knowledge-question-heading" className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">
              Question {currentQuestion + 1} of {questions.length}
            </h2>
          </div>
          <Badge variant="outline" className="capitalize">{question.category || 'General'}</Badge>
        </div>
        <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-slate-100" aria-hidden="true">
          <div className="h-full rounded-full bg-blue-600" style={{ width: `${progress}%` }} />
        </div>
        <p className="mt-2 text-xs text-slate-500">{answeredCount} of {questions.length} answered</p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7">
        <p className="text-base font-medium leading-7 text-slate-950 sm:text-lg">{question.question}</p>
        <RadioGroup
          className="mt-6 space-y-3"
          value={selectedAnswer === undefined ? '' : String(selectedAnswer)}
          onValueChange={(value) => onAnswer(question.id, Number(value))}
          aria-label={`Answers for question ${currentQuestion + 1}`}
        >
          {question.options?.map((option, index) => {
            const optionId = `mcq-${question.id}-${index}`;
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
                <span><span className="mr-2 font-semibold text-slate-500">{String.fromCharCode(65 + index)}.</span>{option}</span>
              </Label>
            );
          })}
        </RadioGroup>
        {savingQuestionId === question.id && (
          <p className="mt-3 text-xs text-slate-500" role="status">Saving answer…</p>
        )}
      </div>

      <div className="flex flex-col-reverse justify-between gap-3 sm:flex-row">
        <Button
          type="button"
          variant="outline"
          onClick={() => setCurrentQuestion((value) => Math.max(0, value - 1))}
          disabled={currentQuestion === 0}
        >
          <ChevronLeft className="mr-2 h-4 w-4" aria-hidden="true" />
          Previous
        </Button>
        {currentQuestion < questions.length - 1 ? (
          <Button type="button" onClick={() => setCurrentQuestion((value) => value + 1)}>
            Next question
            <ChevronRight className="ml-2 h-4 w-4" aria-hidden="true" />
          </Button>
        ) : (
          <Button type="button" onClick={onNextSection}>
            Continue
            <ChevronRight className="ml-2 h-4 w-4" aria-hidden="true" />
          </Button>
        )}
      </div>
    </section>
  );
};

export default MCQSection;
