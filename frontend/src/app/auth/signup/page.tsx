'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import Link from 'next/link';
import { motion } from 'framer-motion';

export default function SignupPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [farmName, setFarmName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const router = useRouter();

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      // Sign up user
      const { error: signUpError } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            farm_name: farmName,
          },
        },
      });

      if (signUpError) {
        setError(signUpError.message);
        setLoading(false);
        return;
      }

      setSuccess('Account created! Check your email to verify. Then login.');
      setTimeout(() => {
        router.push('/auth/login');
      }, 2000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Signup failed');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-600 to-green-800 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md"
      >
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-green-700 mb-2">Kisan Mitra 🌾</h1>
          <p className="text-gray-600">नया खाता बनाएं</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSignup} className="space-y-4">
          {/* Farm Name */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Farm Name / खेत का नाम
            </label>
            <input
              type="text"
              value={farmName}
              onChange={(e) => setFarmName(e.target.value)}
              placeholder="My Farm"
              required
              className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition-all"
            />
          </div>

          {/* Email */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition-all"
            />
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Password (min 8 chars)
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              minLength={8}
              required
              className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition-all"
            />
          </div>

          {/* Error Message */}
          {error && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm"
            >
              {error}
            </motion.div>
          )}

          {/* Success Message */}
          {success && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm"
            >
              {success}
            </motion.div>
          )}

          {/* Submit Button */}
          <motion.button
            whileTap={{ scale: 0.95 }}
            type="submit"
            disabled={loading}
            className={`w-full py-3 rounded-lg font-semibold text-white transition-all ${
              loading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-green-600 hover:bg-green-700 active:scale-95'
            }`}
          >
            {loading ? 'Creating account...' : 'Sign Up'}
          </motion.button>
        </form>

        {/* Login Link */}
        <div className="mt-6 text-center">
          <p className="text-gray-600 text-sm">
            पहले से खाता है?{' '}
            <Link href="/auth/login" className="text-green-600 font-semibold hover:text-green-700">
              Login करें
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
