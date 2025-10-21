import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AdminAuthProvider } from "@/contexts/AdminAuthContext";
import { AuthProvider } from "@/providers/AuthProvider";
import { WalletProvider } from "@/providers/WalletProvider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Lumiere - Algorithmic Trading Platform",
  description: "Blind to emotion, guided by algorithm",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <AdminAuthProvider>
          <WalletProvider>
            <AuthProvider>{children}</AuthProvider>
          </WalletProvider>
        </AdminAuthProvider>
      </body>
    </html>
  );
}
