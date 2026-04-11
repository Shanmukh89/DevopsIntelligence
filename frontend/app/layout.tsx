import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Auditr",
  description: "Auditr application",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
