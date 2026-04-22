import { NextRequest, NextResponse } from 'next/server';
import { pyToJS, pyToRust } from '@/lib/algebra-engine';

export async function POST(req: NextRequest) {
  try {
    const { code, targetLang } = await req.json();
    if (!code) {
      return NextResponse.json({ error: 'Código obrigatório' }, { status: 400 });
    }
    const result: Record<string, string> = {};
    if (!targetLang || targetLang === 'javascript') {
      result['javascript'] = pyToJS(code as string);
    }
    if (!targetLang || targetLang === 'rust') {
      result['rust'] = pyToRust(code as string);
    }
    if (targetLang && !result[targetLang as string]) {
      return NextResponse.json(
        { error: `Linguagem não suportada: ${targetLang}` },
        { status: 400 },
      );
    }
    return NextResponse.json({ result });
  } catch {
    return NextResponse.json({ error: 'Erro interno do servidor' }, { status: 500 });
  }
}
