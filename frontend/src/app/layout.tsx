import type { Metadata, Viewport } from 'next';
import './globals.css';
import { I18nProvider } from '@/components/providers/I18nProvider';

export const metadata: Metadata = {
  title: 'AI4Agri Platform',
  description: 'Predictive Precision Agriculture Intelligence Platform',
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <I18nProvider>
          {children}
        </I18nProvider>
      </body>
    </html>
  );
}
