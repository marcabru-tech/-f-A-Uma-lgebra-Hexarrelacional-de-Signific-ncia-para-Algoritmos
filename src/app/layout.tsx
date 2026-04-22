import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Álgebra Hexarrelacional',
  description: 'Motor de Álgebra Hexarrelacional — Transpilação, Relações e Distribuição'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt">
      <body>{children}</body>
    </html>
  );
}
