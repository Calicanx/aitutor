import React from 'react';

interface Props {
  score: number;
  total: number;
  subject: string;
  onContinue: () => void;
}

const AssessmentResults: React.FC<Props> = ({
  score,
  total,
  subject,
  onContinue
}) => {
  const percentage = total > 0 ? Math.round((score / total) * 100) : 0;
  const passColor = percentage >= 70 ? '#4CAF50' : '#FF9800';

  return (
    <div style={{
      padding: '40px',
      textAlign: 'center',
      maxWidth: '500px',
      margin: '0 auto',
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center'
    }}>
      <h1 style={{ fontSize: '32px', marginBottom: '20px' }}>Assessment Complete!</h1>

      <div style={{
        fontSize: '48px',
        fontWeight: 'bold',
        margin: '20px 0',
        color: passColor
      }}>
        {score}/{total}
      </div>

      <div style={{
        fontSize: '18px',
        marginBottom: '30px',
        color: '#333'
      }}>
        You scored <strong>{percentage}%</strong> on <strong>{subject}</strong>
      </div>

      {percentage >= 70 ? (
        <p style={{ fontSize: '16px', marginBottom: '30px', color: '#4CAF50' }}>
          Great job! You're ready to start learning.
        </p>
      ) : (
        <p style={{ fontSize: '16px', marginBottom: '30px', color: '#FF9800' }}>
          Keep practicing! You'll improve over time.
        </p>
      )}

      <button
        onClick={onContinue}
        style={{
          padding: '12px 24px',
          fontSize: '16px',
          cursor: 'pointer',
          backgroundColor: passColor,
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          fontWeight: 'bold'
        }}
      >
        Start Learning
      </button>
    </div>
  );
};

export default AssessmentResults;
