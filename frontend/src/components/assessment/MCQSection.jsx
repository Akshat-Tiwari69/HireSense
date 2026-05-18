import React from 'react';
import { Button } from '../ui/button';
import { Card, CardContent } from '../ui/card';
import { RadioGroup, RadioGroupItem } from '../ui/radio-group';
import { Label } from '../ui/label';
import { Progress } from '../ui/progress';
import { Badge } from '../ui/badge';
import { ChevronLeft, ChevronRight } from 'lucide-react';

const MCQSection = ({
  questions,
  currentQuestion,
  mcqAnswers,
  onAnswer,
  onNextSection,
  setCurrentQuestion,
}) => {
  if (!questions || questions.length === 0) {
    return <p className="text-slate-400 text-center py-8">No questions available</p>;
  }

  const question = questions[currentQuestion];
  if (!question) return null;

  const answeredCount = Object.keys(mcqAnswers).length;
  const progressPercent = (answeredCount / questions.length) * 100;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-emerald-400 bg-clip-text text-transparent">
              Question {currentQuestion + 1} of {questions.length}
            </h3>
            <Badge className="bg-gradient-to-r from-indigo-600 to-indigo-700 text-white border-0">
              {question.category}
            </Badge>
          </div>
          <div className="mt-3">
            <Progress value={progressPercent} className="h-2 bg-slate-700" />
            <p className="text-xs text-slate-400 mt-2">{answeredCount}/{questions.length} answered</p>
          </div>
        </div>
      </div>

      <Card className="bg-gradient-to-br from-slate-800 to-slate-900 shadow-xl border-slate-700 hover:shadow-2xl transition-all duration-300">
        <CardContent className="pt-8">
          <p className="text-lg text-slate-100 mb-8 leading-relaxed font-medium">{question.question}</p>
          <RadioGroup
            value={mcqAnswers[question.id] !== undefined ? mcqAnswers[question.id].toString() : ''}
            onValueChange={(value) => onAnswer(question.id, parseInt(value))}
          >
            <div className="space-y-3">
              {question.options.map((option, idx) => (
                <div
                  key={idx}
                  className={`flex items-center space-x-4 p-5 rounded-lg border-2 transition-all duration-200 cursor-pointer ${
                    mcqAnswers[question.id] === idx
                      ? 'border-emerald-500 bg-emerald-500/15 shadow-md'
                      : 'border-slate-600 hover:border-indigo-500 hover:bg-slate-700/40'
                  }`}
                  onClick={() => onAnswer(question.id, idx)}
                >
                  <RadioGroupItem value={idx.toString()} id={`option-${idx}`} className="border-slate-400" />
                  <Label htmlFor={`option-${idx}`} className="flex-1 cursor-pointer text-slate-200 text-base">
                    {String.fromCharCode(65 + idx)}) {option}
                  </Label>
                </div>
              ))}
            </div>
          </RadioGroup>
        </CardContent>
      </Card>

      <div className="flex justify-between gap-3 pt-4">
        <Button
          variant="outline"
          onClick={() => setCurrentQuestion(prev => Math.max(0, prev - 1))}
          disabled={currentQuestion === 0}
          className="border-slate-600 text-slate-300 hover:bg-slate-700 hover:text-white gap-2"
        >
          <ChevronLeft className="w-4 h-4" /> Previous
        </Button>
        {currentQuestion < questions.length - 1 ? (
          <Button
            onClick={() => setCurrentQuestion(prev => prev + 1)}
            className="bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 gap-2"
          >
            Next Question <ChevronRight className="w-4 h-4" />
          </Button>
        ) : (
          <Button
            onClick={onNextSection}
            className="bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 gap-2"
          >
            Next Section <ChevronRight className="w-4 h-4" />
          </Button>
        )}
      </div>
    </div>
  );
};

export default MCQSection;
