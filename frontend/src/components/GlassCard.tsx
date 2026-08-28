'use client';

import { motion } from 'framer-motion';
import { ReactNode } from 'react';

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
  hoverEffect?: boolean;
  delay?: number;
}

export default function GlassCard({ 
  children, 
  className = '', 
  onClick, 
  hoverEffect = false,
  delay = 0
}: GlassCardProps) {
  const baseClasses = hoverEffect ? 'glass glass-hover' : 'glass';
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      className={`rounded-xl overflow-hidden ${baseClasses} ${className}`}
      onClick={onClick}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      {children}
    </motion.div>
  );
}
