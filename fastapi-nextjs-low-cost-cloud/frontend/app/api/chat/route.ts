import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';
import { cookies } from 'next/headers';
import { createServerClient } from '@supabase/auth-helpers-nextjs';

export async function POST(req: NextRequest) {
  const body = await req.json();

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseAnonKey) {
    return NextResponse.json(
      { error: 'Supabase environment variables are not configured' },
      { status: 500 }
    );
  }

  // Read Supabase session from HTTP-only cookies and forward JWT to FastAPI
  const cookieStore = await cookies();

  const supabase = createServerClient(supabaseUrl, supabaseAnonKey, {
    cookies: {
      getAll: async () => cookieStore.getAll(),
      setAll: async (setCookies) => {
        setCookies.forEach(({ name, value, options }) => {
          cookieStore.set(name, value, options);
        });
      },
    },
    cookieOptions: {
      name: 'sb-auth-token',
      sameSite: 'lax',
      secure: process.env.NODE_ENV === 'production',
    },
  });

  const {
    data: { session },
  } = await supabase.auth.getSession();

  const accessToken = session?.access_token;

  const result = await axios.post(`${process.env.API_URL}/api/chat`, body, {
    headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
  });

  return NextResponse.json(result.data);
}