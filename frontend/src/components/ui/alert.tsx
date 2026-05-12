import React from 'react';
import { cn } from '@/lib/utils';

interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'destructive';
}

export function Alert({ className, variant = 'default', ...props }: AlertProps) {
  return (
    <div
      role="alert"
      className={cn(
        'rounded-lg border p-4 text-sm',
        variant === 'destructive'
          ? 'border-red-200 bg-red-50 text-red-800'
          : 'border-gray-200 bg-gray-50 text-gray-800',
        className
      )}
      {...props}
    />
  );
}

export function AlertTitle({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn('mb-1 font-semibold', className)} {...props} />;
}

export function AlertDescription({
  className,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn('text-sm opacity-90', className)} {...props} />;
}
