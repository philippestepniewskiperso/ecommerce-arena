import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/Header";
import { CartProvider } from "@/lib/cart";
import { AuthProvider } from "@/lib/auth";
import ChatWidget from "@/components/ChatWidget";

export const metadata: Metadata = {
  title: "KICKS – Premium Footwear",
  description: "Premium shoe retail sandbox for agent testing",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <CartProvider>
            <Header />
            {children}
            <ChatWidget />
          </CartProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
