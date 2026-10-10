import type { Metadata } from "next";
import { Atkinson_Hyperlegible_Next, Baloo_Da_2, Noto_Sans_Bengali } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";

/* Self-hosted by next/font: no request to fonts.googleapis.com and no layout
 * shift on load. Two families because Atkinson has no Bengali coverage - the
 * app's Bangla text would otherwise fall back to whatever the OS happens to
 * have. Both are variable fonts, so every weight comes from one file each. */
const atkinson = Atkinson_Hyperlegible_Next({
  subsets: ["latin"],
  variable: "--font-atkinson",
  display: "swap",
});

const notoSansBengali = Noto_Sans_Bengali({
  subsets: ["bengali", "latin"],
  variable: "--font-noto-bengali",
  display: "swap",
});

/* Headings only. Baloo Da 2 was drawn by Ek Type for Bangla first, so a
 * heading reads with the same round, friendly voice in either script; body
 * text and every number a reader has to trust stay in Atkinson. */
const balooDa = Baloo_Da_2({
  subsets: ["bengali", "latin"],
  variable: "--font-baloo",
  display: "swap",
});

/* Runs before first paint so a dark-mode user never sees a white flash. It is
 * deliberately tiny and synchronous; anything async would paint first. */
const themeScript = `
(function () {
  try {
    var stored = localStorage.getItem("theme");
    var dark = stored === "dark" ||
      (stored !== "light" && window.matchMedia("(prefers-color-scheme: dark)").matches);
    document.documentElement.classList.toggle("dark", dark);
  } catch (e) {}
})();
`;

export const metadata: Metadata = {
  title: "স্বাস্থ্য পরিকল্পনা · Health Plan",
  description:
    "Physician-supervised diet & lifestyle recommendation system: intake, review, approve, report.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${atkinson.variable} ${notoSansBengali.variable} ${balooDa.variable}`}
      // The theme script sets .dark on the client before React hydrates, so
      // the server and client html classNames legitimately differ.
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="min-h-screen antialiased">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
