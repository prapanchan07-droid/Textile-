import React from 'react';
import { cn } from '../lib/format';

/**
 * Lightweight, responsive rendering of the Ashok Textile identity.  The mark
 * uses the cyan, blue, red and charcoal geometry from the supplied company
 * logo so navigation stays recognisable even when the sidebar is collapsed.
 */
export const AshokLogo: React.FC<{ compact?: boolean; className?: string }> = ({ compact = false, className }) => (
  <div className={cn('flex min-w-0 items-center', compact ? 'justify-center' : 'gap-2.5', className)} aria-label="Ashok Textile Mills Pvt Ltd">
    <svg viewBox="0 0 52 62" className={cn('shrink-0', compact ? 'h-8 w-7' : 'h-11 w-9')} role="img" aria-label="Ashok logo">
      <path d="M25.8 1 15 19.2h11.2L31.8 9.8 25.8 1Z" fill="#7c8285" />
      <path d="m36.8 3.2-7.3 12.2h14.1L36.8 3.2Z" fill="#ec2834" />
      <path d="m18.7 22.3-7.4 12.5h14.8l-7.4-12.5Z" fill="#00a4dc" />
      <path d="m27.4 14.1-7.3 12.4h14.7l-7.4-12.4Z" fill="#0077b9" />
      <path d="m9.9 37.8-8.1 13.6h17.1L9.9 37.8Z" fill="#00a4dc" />
      <path d="m19.1 37.8-8.3 13.6h17.2l-8.9-13.6Z" fill="#0089c7" />
      <path d="m28.1 37.8-8.2 13.6h17.2l-9.1-13.6Z" fill="#0069ad" />
      <path d="m19 53.6-5.2 8.4h22.9l-7.6-8.4H19Z" fill="#009bd4" />
    </svg>
    {!compact && (
      <div className="min-w-0 leading-none text-[#202020]">
        <div className="font-serif text-[20px] font-bold tracking-tight">ASHOK</div>
        <div className="mt-0.5 whitespace-nowrap font-serif text-[8px] font-semibold tracking-[0.015em]">Ashok Textile Mills Pvt Ltd</div>
      </div>
    )}
  </div>
);
