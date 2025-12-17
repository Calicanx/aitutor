import React, { useState, useEffect } from 'react';
import { useHistory, useParams } from 'react-router-dom';
import { apiUtils } from '../../lib/api-utils';
import AssessmentQuestion from './AssessmentQuestion';
import AssessmentResults from './AssessmentResults';

const DASH_API_URL = import.meta.env.VITE_DASH_API_URL || 'http://localhost:8000';

interface Question {
  question: any;
  answerArea: any;
  hints: any[];
  dash_metadata: any;
  [key: string]: any;
}

interface Params {
  subject: string;
}

const AssessmentFlow: React.FC = () => {
  const history = useHistory();
  const { subject } = useParams<Params>();

  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [completed, setCompleted] = useState(false);
  const [score, setScore] = useState(0);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    startAssessment();
  }, [subject]);

  const startAssessment = async () => {
    try {
      const response = await apiUtils.post(`${DASH_API_URL}/assessment/start/${subject}`, {});
      
      if (!response.ok) {
        throw new Error(`Failed to start assessment: ${response.status}`);
      }

      const data = await response.json();

      if (data.error) {
        // Already completed
        setCompleted(true);
        setScore(data.score);
        setTotal(data.total || 0);
        setLoading(false);
        return;
      }

      setQuestions(data.questions);
      setTotal(data.total);
      setLoading(false);
    } catch (error) {
      console.error('Failed to start assessment:', error);
      history.push('/app');
    }
  };

  const handleAnswer = async (isCorrect: boolean) => {
    const currentQuestion = questions[currentIndex];
    const newAnswer = {
      question_id: currentQuestion.dash_metadata.dash_question_id,
      skill_id: currentQuestion.dash_metadata.skill_ids[0],
      is_correct: isCorrect
    };

    const newAnswers = [...answers, newAnswer];
    setAnswers(newAnswers);

    if (currentIndex < questions.length - 1) {
      // Move to next question
      setCurrentIndex(currentIndex + 1);
    } else {
      // Assessment complete - submit all answers
      submitAssessment(newAnswers);
    }
  };

  const submitAssessment = async (finalAnswers: any[]) => {
    try {
      const response = await apiUtils.post(`${DASH_API_URL}/assessment/complete`, {
        subject,
        answers: finalAnswers
      });

      if (!response.ok) {
        throw new Error(`Failed to complete assessment: ${response.status}`);
      }

      const data = await response.json();
      setScore(data.score);
      setCompleted(true);
    } catch (error) {
      console.error('Failed to complete assessment:', error);
      history.push('/app');
    }
  };

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        fontSize: '18px'
      }}>
        Loading assessment...
      </div>
    );
  }

  if (completed) {
    return (
      <AssessmentResults
        score={score}
        total={total}
        subject={subject}
        onContinue={() => history.push('/app')}
      />
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      <h1>Assessment - Question {currentIndex + 1} of {questions.length}</h1>

      {questions.length > currentIndex && (
        <AssessmentQuestion
          question={questions[currentIndex]}
          questionNumber={currentIndex + 1}
          totalQuestions={questions.length}
          onAnswer={handleAnswer}
        />
      )}
    </div>
  );
};

export default AssessmentFlow;
