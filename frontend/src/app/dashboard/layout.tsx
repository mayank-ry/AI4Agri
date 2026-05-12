'use client';

import { useTranslation } from 'react-i18next';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { supabase } from '@/lib/supabase';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { t } = useTranslation();
  const router = useRouter();

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      {/* Mobile-first top navigation */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="px-4 py-3 flex items-center justify-between">
          <h1 className="text-xl font-bold text-green-700">
            {t('dashboard.title')}
          </h1>
          <Button 
            variant="outline" 
            className="text-sm px-3 py-1"
            onClick={async () => {
              await supabase.auth.signOut();
              router.push('/auth/login');
            }}
          >
            {t('dashboard.logout')}
          </Button>
        </div>
      </header>

      <main className="flex-1 w-full max-w-md mx-auto p-4 md:p-6 md:max-w-4xl">
        {children}
      </main>
    </div>
  );
}
