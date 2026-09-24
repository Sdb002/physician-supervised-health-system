import type { Metadata } from "next";
import { Figtree, Noto_Sans_Bengali } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";

/* Self-hosted by next/font: no request to fonts.googleapis.com and no layout
 * shift on load. Two families because Figtree has no Bengali coverage - the
 * app's Bangla headings would otherwise fall back to whatever the OS happens
 * to have, which is what made them look inconsistent next to the Latin UI. */
const figtree = Figtree({
  subsets: ["latin"],
  variable: "--font-figtree",
  display: "swap",
});

const notoSansBengali = Noto_Sans_Bengali({
  subsets: ["bengali", "latin"],
  variable: "--font-noto-bengali",
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
  title: "স্বাস্থ্য পরিকল্পনা — Physician-Supervised Health System",
  description:
    "Physician-supervised diet & lifestyle recommendation system: intake, review, approve, report.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${figtree.variable} ${notoSansBengali.variable}`}
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
