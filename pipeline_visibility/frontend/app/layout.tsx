import "./globals.css";
import Providers from "./providers";

export const metadata = {
  title: "Pipeline Visibility Dashboard",
  description: "RANICA Revenue Operations dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
