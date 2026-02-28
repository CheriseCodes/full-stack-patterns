import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

export async function POST(req: NextRequest) {
  const body = await req.json();
  
  const result = await axios.post(`${process.env.API_URL}/api/chat`, body);
  
  return NextResponse.json(result.data);
}