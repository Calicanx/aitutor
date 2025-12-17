/**
 * Assessment Guard Component
 *
 * Checks if user has completed assessment for primary subject.
 * If not completed, redirects to assessment page.
 * If completed, allows access to main app.
 */
import React, { useEffect, useState } from 'react';
import { Redirect, useHistory } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { apiUtils } from '../../lib/api-utils';

interface AssessmentGuardProps {
  children: React.ReactNode;
  subject?: string;
}

const DASH_API_URL = import.meta.env.VITE_DASH_API_URL || 'http://localhost:8000';
const DEFAULT_SUBJECT = 'math';

const AssessmentGuard: React.FC<AssessmentGuardProps> = ({
  children,
  subject = DEFAULT_SUBJECT
}) => {
  const { isAuthenticated, isLoading } = useAuth();
  const history = useHistory();
  const [assessmentStatus, setAssessmentStatus] = useState<{
    loading: boolean;
    completed: boolean;
    checkFailed: boolean;
  }>({
    loading: true,
    completed: false,
    checkFailed: false
  });

  useEffect(() => {
    if (!isAuthenticated || isLoading) {
      return;
    }

    checkAssessmentStatus();
  }, [isAuthenticated, isLoading, subject]);

  const checkAssessmentStatus = async () => {
    try {
      const response = await apiUtils.get(
        `${DASH_API_URL}/assessment/status/${subject}`
      );

      if (!response.ok) {
        console.warn(`Failed to check assessment status: ${response.status}`);
        setAssessmentStatus({
          loading: false,
          completed: false,
          checkFailed: true
        });
        return;
      }

      const data = await response.json();

      setAssessmentStatus({
        loading: false,
        completed: data.completed || false,
        checkFailed: false
      });
    } catch (error) {
      console.error('Error checking assessment status:', error);
      setAssessmentStatus({
        loading: false,
        completed: false,
        checkFailed: true
      });
    }
  };

  // Show loading while checking authentication
  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        background: '#FFFDF5'
      }}>
        <div>Initializing...</div>
      </div>
    );
  }

  // If not authenticated, let AuthGuard handle redirect
  if (!isAuthenticated) {
    return <>{children}</>;
  }

  // Show loading while checking assessment status
  if (assessmentStatus.loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        background: '#FFFDF5'
      }}>
        <div>Checking assessment status...</div>
      </div>
    );
  }

  // If check failed, allow access (don't block user on API error)
  if (assessmentStatus.checkFailed) {
    return <>{children}</>;
  }

  // If assessment not completed, redirect to assessment
  if (!assessmentStatus.completed) {
    return <Redirect to={`/app/assessment/${subject}`} />;
  }

  // Assessment completed, allow access to app
  return <>{children}</>;
};

export default AssessmentGuard;
