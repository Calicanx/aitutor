import React, { useRef, useState } from 'react';
import { ServerItemRenderer } from "../../package/perseus/src/server-item-renderer";
import { storybookDependenciesV2 } from "../../package/perseus/testing/test-dependencies";
import { RenderStateRoot } from "@khanacademy/wonder-blocks-core";
import { PerseusI18nContextProvider } from "../../package/perseus/src/components/i18n-context";
import { mockStrings } from "../../package/perseus/src/strings";
import { scorePerseusItem } from "@khanacademy/perseus-score";
import { keScoreFromPerseusScore } from "../../package/perseus/src/util/scoring";
import { Button } from "@/components/ui/button";
import { CheckCircle2, XCircle } from "lucide-react";
import { KEScore } from "@khanacademy/perseus-core";

interface Props {
  question: any;
  questionNumber: number;
  totalQuestions: number;
  onAnswer: (isCorrect: boolean) => void;
}

const AssessmentQuestion: React.FC<Props> = ({
  question,
  questionNumber,
  totalQuestions,
  onAnswer
}) => {
  const rendererRef = useRef<ServerItemRenderer>(null);
  const [isAnswered, setIsAnswered] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);
  const [keScore, setKeScore] = useState<KEScore | null>(null);

  const handleSubmit = () => {
    if (!rendererRef.current) return;

    const userInput = rendererRef.current.getUserInput();
    const questionData = question.question;
    const scoreResult = scorePerseusItem(questionData, userInput, "en");

    const maxCompatGuess = [rendererRef.current.getUserInputLegacy(), []];
    const score = keScoreFromPerseusScore(
      scoreResult,
      maxCompatGuess,
      rendererRef.current.getSerializedState().question,
    );

    setIsAnswered(true);
    setShowFeedback(true);
    setKeScore(score);
    onAnswer(score.correct);
  };

  return (
    <div>
      <div style={{
        marginBottom: '20px',
        fontSize: '14px',
        color: '#666',
        textAlign: 'center'
      }}>
        Question {questionNumber}/{totalQuestions}
      </div>

      <div className="border-[3px] border-black dark:border-white bg-white dark:bg-neutral-800 text-black dark:text-white p-4 shadow-[2px_2px_0_0_rgba(0,0,0,1)]">
        <PerseusI18nContextProvider locale="en" strings={mockStrings}>
          <RenderStateRoot>
            <ServerItemRenderer
              ref={rendererRef}
              problemNum={0}
              item={question}
              dependencies={storybookDependenciesV2}
              apiOptions={{}}
              linterContext={{
                contentType: "",
                highlightLint: true,
                paths: [],
                stack: [],
              }}
              showSolutions="none"
              hintsVisible={0}
              reviewMode={false}
            />
          </RenderStateRoot>
        </PerseusI18nContextProvider>
      </div>

      {!isAnswered && (
        <div style={{ marginTop: '20px', textAlign: 'center' }}>
          <Button onClick={handleSubmit}>Submit Answer</Button>
        </div>
      )}

      {showFeedback && keScore && (
        <div style={{ marginTop: '20px', textAlign: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
            {keScore.correct ? (
              <>
                <CheckCircle2 style={{ color: '#4CAF50' }} />
                <span style={{ color: '#4CAF50', fontWeight: 'bold' }}>Correct!</span>
              </>
            ) : (
              <>
                <XCircle style={{ color: '#f44336' }} />
                <span style={{ color: '#f44336', fontWeight: 'bold' }}>Incorrect</span>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AssessmentQuestion;
