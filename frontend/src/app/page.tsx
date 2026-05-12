'use client';

import { useTranslation } from 'react-i18next';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';

export default function LandingPage() {
  const { t, i18n } = useTranslation();
  const router = useRouter();

  const toggleLanguage = () => {
    const nextLang = i18n.language === 'en' ? 'hi' : 'en';
    i18n.changeLanguage(nextLang);
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-4 md:p-8 bg-gradient-to-b from-green-50 to-white">
      <div className="w-full max-w-md mx-auto text-center space-y-8">
        <div className="space-y-2">
          <h1 className="text-3xl md:text-4xl font-bold text-green-800">
            {t('landing.title')}
          </h1>
          <p className="text-gray-600">
            {t('landing.subtitle')}
          </p>
        </div>

        <div className="pt-8 space-y-4">
          <Button 
            fullWidth 
            onClick={() => router.push('/auth/login')}
          >
            {t('landing.cta_login')}
          </Button>
          
          <Button 
            variant="outline" 
            fullWidth 
            onClick={toggleLanguage}
          >
            {i18n.language === 'en' ? 'हिंदी में बदलें' : 'Switch to English'}
          </Button>
        </div>
      </div>
    </main>
  );
}
