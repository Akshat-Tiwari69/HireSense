import React from 'react';
import { Button } from '../ui/button';
import { Card, CardContent } from '../ui/card';
import { RadioGroup, RadioGroupItem } from '../ui/radio-group';
import { Label } from '../ui/label';
import { Progress } from '../ui/progress';
import { Badge } from '../ui/badge';
import { Brain, CheckCircle, Loader2, ChevronLeft, ChevronRight } from 'lucide-react';

const PsychometricSection = ({
  scenarios,
  currentQuestion,
  psychometricAnswers,
  onAnswer,
  onPrevSection,
  onSubmit,
  isSubmitting,
  setCurrentQuestion,
}) => {
  if (!scenarios || scenarios.length === 0) {
    return <p className="text-slate-400 text-center py-8">No scenarios available</p>;
  }

  const scenario = scenarios[currentQuestion];
  if (!scenario) return null;

  const answeredCount = Object.keys(psychometricAnswers).length;
  const progressPercent = (answeredCount / scenarios.length) * 100;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent flex items-center gap-3">
              <Brain className="w-6 h-6 text-purple-400" />
              Scenario {currentQuestion + 1} of {scenarios.length}
            </h3>
            <Badge className="bg-gradient-to-r from-purple-600 to-purple-700 text-white border-0">
              Personality Assessment
            </Badge>
          </div>
          <div className="mt-3">
            <Progress value={progressPercent} className="h-2 bg-slate-700" />
            <p className="text-xs text-slate-400 mt-2">{answeredCount}/{scenarios.length} answered</p>
          </div>
        </div>
      </div>

      <Card className="bg-gradient-to-br from-slate-800 to-slate-900 shadow-xl border-slate-700 hover:shadow-2xl transition-all duration-300">
        <CardContent className="pt-8">
          <div className="bg-gradient-to-r from-purple-900/40 to-pink-900/40 border border-purple-700/50 p-6 rounded-lg mb-8">
            <p className="text-lg text-slate-100 leading-relaxed font-medium">{scenario.scenario}</p>
          </div>
          <div className="space-y-3">
            <p className="text-slate-400 text-sm font-semibold mb-4">
              Choose the response that best describes your reaction:
            </p>
            <RadioGroup
              value={psychometricAnswers[scenario.id] !== undefined ? psychometricAnswers[scenario.id].toString() : ''}
              onValueChange={(value) => onAnswer(scenario.id, parseInt(value))}
            >
              <div className="space-y-3">
                {scenario.options.map((option, idx) => (
                  <div
                    key={idx}
                    className={`flex items-start space-x-4 p-5 rounded-lg border-2 transition-all duration-200 cursor-pointer ${
                      psychometricAnswers[scenario.id] === idx
                        ? 'border-purple-500 bg-purple-500/15 shadow-md'
                        : 'border-slate-600 hover:border-purple-500 hover:bg-slate-700/40'
                    }`}
                    onClick={() => onAnswer(scenario.id, idx)}
                  >
                    <RadioGroupItem value={idx.toString()} id={`psy-${idx}`} className="border-slate-400 mt-1" />
                    <Label htmlFor={`psy-${idx}`} className="flex-1 cursor-pointer text-slate-200 text-base leading-relaxed">
                      {option}
                    </Label>
                  </div>
                ))}
              </div>
            </RadioGroup>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-between gap-3 pt-4">
        {currentQuestion > 0 ? (
          <Button
            variant="outline"
            onClick={() => setCurrentQuestion(prev => prev - 1)}
            className="border-slate-600 text-slate-300 hover:bg-slate-700 hover:text-white gap-2"
          >
            <ChevronLeft className="w-4 h-4" /> Previous Scenario
          </Button>
        ) : (
          <Button
            variant="outline"
            onClick={onPrevSection}
            className="border-slate-600 text-slate-300 hover:bg-slate-700 hover:text-white gap-2"
          >
            <ChevronLeft className="w-4 h-4" /> Previous Section
          </Button>
        )}

        {currentQuestion < scenarios.length - 1 ? (
          <Button
            onClick={() => setCurrentQuestion(prev => prev + 1)}
            className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 gap-2"
          >
            Next Scenario <ChevronRight className="w-4 h-4" />
          </Button>
        ) : (
          <Button
            onClick={onSubmit}
            className="bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 gap-2 font-semibold"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <><Loader2 className="w-4 h-4 animate-spin" />Submitting...</>
            ) : (
              <><CheckCircle className="w-4 h-4" />Submit Assessment</>
            )}
          </Button>
        )}
      </div>
    </div>
  );
};

export default PsychometricSection;
