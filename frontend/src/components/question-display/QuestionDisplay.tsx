import React from 'react';
import RendererComponent from "../question-widget-renderer/RendererComponent";

interface QuestionDisplayProps {
  onSkillChange?: (skill: string) => void;
}

const QuestionDisplay: React.FC<QuestionDisplayProps> = ({ onSkillChange }) => {
  return (
    <div className="w-full h-auto md:h-full flex flex-col items-stretch justify-start bg-transparent overflow-visible md:overflow-hidden">
      <div className="w-full h-auto md:h-full" id="perseus-capture-area">
        <RendererComponent onSkillChange={onSkillChange} />
      </div>
    </div>
  );
};

export default QuestionDisplay;
