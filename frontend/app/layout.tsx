import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';
import { ThemeProvider } from '@/components/theme-provider';
import { MarketingHeader } from '@/components/marketing-header';
import { Footer } from '@/components/footer';
import { AdminAuthProvider } from '@/src/contexts/AdminAuthContext';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'Lumiere - AI-Powered Trading Platform',
  description: 'Transform raw market data into winning strategies with AI',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className="h-full">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased h-full`}>
        <AdminAuthProvider>
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            <div className="h-full flex flex-col overflow-hidden">
              <MarketingHeader />
              <main className="flex-1 overflow-y-auto">
                {children}
              </main>
              <Footer />
            </div>
          </ThemeProvider>
        </AdminAuthProvider>
      </body>
    </html>
  );
}
