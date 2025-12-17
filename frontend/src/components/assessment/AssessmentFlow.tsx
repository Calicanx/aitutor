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
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

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
      // Wait 2 seconds to show feedback before moving to next question
      setTimeout(() => {
        setCurrentIndex(currentIndex + 1);
      }, 2000);
    } else {
      // Assessment complete - submit all answers after showing final feedback
      setTimeout(() => {
        submitAssessment(newAnswers);
      }, 2000);
    }
  };

  const submitAssessment = async (finalAnswers: any[]) => {
    try {
      setSubmitting(true);
      setError(null);

      const response = await apiUtils.post(`${DASH_API_URL}/assessment/complete`, {
        subject,
        answers: finalAnswers
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to complete assessment: ${response.status}`);
      }

      const data = await response.json();
      setScore(data.score);
      setTotal(data.total);
      setCompleted(true);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to complete assessment';
      console.error('Failed to complete assessment:', err);
      setError(errorMessage);
      setSubmitting(false);
      // Don't redirect immediately - show error to user
    }
  };

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        fontSize: '18px',
        backgroundColor: 'var(--neo-bg)',
        color: 'var(--neo-black)',
        fontWeight: 700,
        textTransform: 'uppercase',
        letterSpacing: '0.05em'
      }}>
        <div style={{
          padding: '24px 32px',
          border: '5px solid var(--neo-black)',
          backgroundColor: 'var(--neo-yellow)',
          boxShadow: '3px 3px 0 var(--neo-black)'
        }}>
          Loading Assessment...
        </div>
      </div>
    );
  }

  if (completed) {
    return (
      <AssessmentResults
        score={score}
        total={total}
        subject={subject}
        onContinue={() => history.replace('/app')}
      />
    );
  }

  if (error) {
    return (
      <div style={{
        padding: '40px 20px',
        backgroundColor: 'var(--neo-bg)',
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{
          maxWidth: '600px',
          border: '5px solid var(--neo-black)',
          backgroundColor: '#FFEBEE',
          padding: '32px',
          boxShadow: '3px 3px 0 var(--neo-black)'
        }}>
          <h2 style={{
            color: '#C62828',
            fontSize: '24px',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: '16px',
            marginTop: 0
          }}>
            Assessment Error
          </h2>
          <p style={{
            color: '#C62828',
            fontSize: '16px',
            fontWeight: 600,
            marginBottom: '24px'
          }}>
            {error}
          </p>
          <button
            onClick={() => history.replace('/app')}
            style={{
              width: '100%',
              padding: '16px 32px',
              fontSize: '16px',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              backgroundColor: 'var(--neo-yellow)',
              color: 'var(--neo-black)',
              border: '5px solid var(--neo-black)',
              cursor: 'pointer',
              boxShadow: '2px 2px 0 var(--neo-black)',
              transition: 'all 0.2s ease',
            }}
            onMouseDown={(e) => {
              (e.target as HTMLElement).style.boxShadow = '1px 1px 0 var(--neo-black)';
              (e.target as HTMLElement).style.transform = 'translateY(2px) translateX(2px)';
            }}
            onMouseUp={(e) => {
              (e.target as HTMLElement).style.boxShadow = '2px 2px 0 var(--neo-black)';
              (e.target as HTMLElement).style.transform = 'translateY(0) translateX(0)';
            }}
          >
            Return to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      padding: '40px 20px',
      backgroundColor: 'var(--neo-bg)',
      minHeight: '100vh'
    }}>
      <div style={{
        maxWidth: '800px',
        margin: '0 auto'
      }}>
        {submitting && (
          <div style={{
            marginBottom: '24px',
            padding: '16px',
            border: '5px solid var(--neo-black)',
            backgroundColor: 'var(--neo-yellow)',
            boxShadow: '2px 2px 0 var(--neo-black)',
            textAlign: 'center',
            fontSize: '14px',
            fontWeight: 700,
            color: 'var(--neo-black)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em'
          }}>
            Submitting Assessment...
          </div>
        )}
        {questions.length > currentIndex && (
          <AssessmentQuestion
            question={questions[currentIndex]}
            questionNumber={currentIndex + 1}
            totalQuestions={questions.length}
            onAnswer={handleAnswer}
          />
        )}
      </div>
    </div>
  );
};

export default AssessmentFlow;
