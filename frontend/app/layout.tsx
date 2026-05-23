import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AG-SAS | AG Structural Analysis Suite",
  description:
    "Platform perhitungan dan laporan struktur baja & beton berbasis standar SNI Indonesia.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="id">
      <body>{children}</body>
    </html>
  );
}
