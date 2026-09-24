import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  className,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabled,
  ...props
}) => {
  const baseStyle = 'inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-factory-accent/50 disabled:opacity-50 disabled:cursor-not-allowed';
  
  const sizes = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-5 py-2.5 text-base',
  };

  const variants = {
    primary: 'bg-factory-accent hover:bg-blue-600 text-white shadow-sm',
    secondary: 'bg-factory-surface hover:bg-slate-800 text-slate-200 border border-factory-border',
    outline: 'bg-transparent hover:bg-factory-surface text-slate-300 border border-factory-border',
    danger: 'bg-factory-rose hover:bg-rose-600 text-white shadow-sm',
    ghost: 'bg-transparent hover:bg-factory-surface/60 text-slate-300',
  };

  return (
    <button
      className={twMerge(clsx(baseStyle, sizes[size], variants[variant], className))}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <span className="mr-2 inline-block animate-spin border-2 border-current border-t-transparent rounded-full w-4 h-4" />
      ) : null}
      {children}
    </button>
  );
};
