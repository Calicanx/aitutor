/**
 * Text-based Teachr Logo Component
 */
import React from 'react';

interface TeachrLogoProps {
  size?: 'small' | 'medium' | 'large';
  color?: string;
  className?: string;
}

const TeachrLogo: React.FC<TeachrLogoProps> = ({ 
  size = 'medium', 
  color = '#000000',
  className = '' 
}) => {
  const sizeClasses = {
    small: 'text-2xl',
    medium: 'text-4xl',
    large: 'text-6xl'
  };

  return (
    <div className={`font-black tracking-tight ${sizeClasses[size]} ${className}`} style={{ color }}>
      <span className="text-[#FFD93D]">T</span>
      <span>eachr</span>
    </div>
  );
};

export default TeachrLogo;

