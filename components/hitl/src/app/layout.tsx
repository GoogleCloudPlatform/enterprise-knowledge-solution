/**
 * Copyright 2025 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Image from "next/image";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Enterprise Knowledge Solution",
  description: "Human-in-the-Loop app for EKS",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
    <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
    >
    <div className={"bg-gray-100 min-h-screen"}>
        <header className={"bg-white text-white p-4 flex justify-between items-center"}>
            <div className={"flex items-center gap-2"}>
                <Image src={"/googleLogo.png"} alt={"Google"} width={70} height={40} />
                <h1 className={"text-[24px] text-[#0d6efd]  font-weight-bold"}>Enterprise Knowledge Solution - HITL</h1>
            </div>
        </header>
        <div
            className="flex justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20 font-[family-name:var(--font-geist-sans)] bg-[#eee]">
            <main className={"bg-white p-6 rounded-lg shadow-md flex-auto mb-20"}>
                {children}
            </main>
        </div>
    </div>
    </body>
    </html>
);
}
