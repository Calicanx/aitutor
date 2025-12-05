import React from 'react';
import RendererComponent from "../question-widget-renderer/RendererComponent";

interface QuestionDisplayProps {
  onSkillChange?: (skill: string) => void;
}

const QuestionDisplay: React.FC<QuestionDisplayProps> = ({ onSkillChange }) => {
  return (
    <div className="w-full h-full flex flex-col items-stretch justify-start bg-transparent overflow-auto">
      <div className="w-full h-full overflow-auto" id="perseus-capture-area">
        <RendererComponent onSkillChange={onSkillChange} />
      </div>
    </div>
  );
};

export default QuestionDisplay;
