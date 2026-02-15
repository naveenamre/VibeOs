import { NextAuthOptions } from "next-auth";
import { PrismaAdapter } from "@next-auth/prisma-adapter";
import { prisma } from "@/lib/prisma";
import { credentialsProvider } from "./credentials-provider";

export const authOptions: NextAuthOptions = {
  adapter: PrismaAdapter(prisma),
  session: {
    strategy: "jwt",
  },
  pages: {
    signIn: "/auth/signin",
    error: "/auth/signin", 
  },
  providers: [
    // Sirf Credentials rakho, Google/Outlook hata diya taaki build fast ho
    credentialsProvider,
  ],
  callbacks: {
    async session({ session, token }) {
      if (session.user && token.sub) {
        session.user.id = token.sub;
      }
      return session;
    },
    async jwt({ token, user }) {
      if (user) {
        token.sub = user.id;
      }
      return token;
    },
  },
  // Debugging on for dev
  debug: process.env.NODE_ENV === "development",
};

export const getAuthOptions = () => authOptions;