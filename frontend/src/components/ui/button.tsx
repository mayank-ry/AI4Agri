import React from 'react';
import { cn } from '@/lib/utils';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost';
  fullWidth?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = '', variant = 'default', type = 'button', fullWidth = false, ...props }, ref) => {
    const variants: Record<NonNullable<ButtonProps['variant']>, string> = {
      default:
        'bg-green-600 text-white hover:bg-green-700 focus-visible:ring-green-500',
      destructive:
        'bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-500',
      outline:
        'border border-gray-300 bg-white text-gray-800 hover:bg-gray-50 focus-visible:ring-gray-400',
      secondary:
        'bg-gray-100 text-gray-900 hover:bg-gray-200 focus-visible:ring-gray-400',
      ghost:
        'text-gray-700 hover:bg-gray-100 focus-visible:ring-gray-300',
    };

    return (
      <button
        ref={ref}
        type={type}
        className={cn(
          'inline-flex items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
          variants[variant],
          fullWidth && 'w-full',
          className
        )}
        {...props}
      />
    );
  }
);

Button.displayName = 'Button';
