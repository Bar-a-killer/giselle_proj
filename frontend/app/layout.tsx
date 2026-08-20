import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { CurrentUserProvider } from "@/lib/currentUser";
import { LocationProvider } from "@/lib/location";
import { Nav } from "@/components/Nav";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "giselle — personalized venue scores",
  description: "Personalized restaurant/venue scores from Google Maps reviews.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-zinc-50 dark:bg-black">
        <CurrentUserProvider>
          <LocationProvider>
            <Nav />
            <main className="flex flex-1 flex-col">{children}</main>
          </LocationProvider>
        </CurrentUserProvider>
      </body>
    </html>
  );
}
