/**
 * Teachr Logo Component using logo.png
 */
import React from 'react';

interface TeachrLogoProps {
  size?: 'small' | 'medium' | 'large';
  color?: string; // Kept for backward compatibility, but not used with image
  className?: string;
}

const TeachrLogo: React.FC<TeachrLogoProps> = ({ 
  size = 'medium', 
  className = '' 
}) => {
  const sizeMap = {
    small: '1.5rem',   // 24px
    medium: '2rem',    // 32px
    large: '3rem'      // 48px
  };

  return (
    <img
      src="/logo.png"
      alt="Teachr"
      className={className}
      style={{ 
        height: sizeMap[size], 
        width: 'auto'
      }}
    />
  );
};

export default TeachrLogo;

