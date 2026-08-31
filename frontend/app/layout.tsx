import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'EDA-Guider',
  description: 'Automated Exploratory Data Analysis',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
