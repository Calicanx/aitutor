import React from 'react';
import RendererComponent from "../question-widget-renderer/RendererComponent";
import './mcq-fix.css'; // Fix for MCQ highlighting bug


interface QuestionDisplayProps {
  onSkillChange?: (skill: string) => void;
  onQuestionChange?: (questionId: string | null) => void;
  watchedVideoIds?: string[];
  onAnswerSubmitted?: () => void;
}

const QuestionDisplay: React.FC<QuestionDisplayProps> = ({ 
  onSkillChange, 
  onQuestionChange,
  watchedVideoIds,
  onAnswerSubmitted
}) => {
  return (
    <div className="w-full h-full flex flex-col items-center justify-center bg-transparent">
      <div className="w-full h-full" id="perseus-capture-area">
        <RendererComponent 
          onSkillChange={onSkillChange} 
          onQuestionChange={onQuestionChange}
          watchedVideoIds={watchedVideoIds}
          onAnswerSubmitted={onAnswerSubmitted}
        />
      </div>
    </div>
  );
};

export default QuestionDisplay;
