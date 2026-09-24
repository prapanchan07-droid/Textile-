import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'outline' | 'flat';
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  variant = 'default',
  ...props
}) => {
  const baseStyle = 'rounded-2xl p-5 transition-all duration-200';
  const variants = {
    default: 'bg-white border border-slate-200/80 shadow-card hover:shadow-md hover:border-slate-300',
    outline: 'bg-white border border-slate-200',
    flat: 'bg-slate-50 border border-slate-200/60',
  };

  return (
    <div
      className={twMerge(clsx(baseStyle, variants[variant], className))}
      {...props}
    >
      {children}
    </div>
  );
};
