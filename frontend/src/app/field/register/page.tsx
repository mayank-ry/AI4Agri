'use client';

import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useEffect } from 'react';
import { supabase } from '@/lib/supabase';

/** MVP placeholder: fields are usually created via Supabase or a future form. */
export default function FieldRegisterPlaceholder() {
  const router = useRouter();

  useEffect(() => {
    (async () => {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session) router.replace('/auth/login');
    })();
  }, [router]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 p-6 text-center">
      <h1 className="text-2xl font-bold text-green-800 mb-2">Naya khet (field)</h1>
      <p className="text-gray-600 max-w-md mb-6">
        Abhi frontend par field registration form complete nahi hai. Apna khet Supabase dashboard se{' '}
        <code className="bg-gray-200 px-1 rounded text-sm">fields</code> table mein add kar sakte hain, ya
        yahi screen baad mein form se replace ho jayegi.
      </p>
      <Link
        href="/dashboard"
        className="text-white bg-green-600 hover:bg-green-700 px-6 py-3 rounded-lg font-semibold"
      >
        Dashboard par wapas jayein
      </Link>
    </div>
  );
}
