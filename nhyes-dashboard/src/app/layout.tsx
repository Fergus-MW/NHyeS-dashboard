import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NHyeS - Capacity Management Dashboard",
  description: "NHS capacity management and attendance prediction dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
