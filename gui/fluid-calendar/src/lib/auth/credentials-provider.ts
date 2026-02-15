import { compare } from "bcrypt";
import { logger } from "@/lib/logger";
import { prisma } from "@/lib/prisma";
import Credentials from "next-auth/providers/credentials";

const LOG_SOURCE = "CredentialsProvider";

export const credentialsProvider = Credentials({
  name: "Credentials",
  credentials: {
    email: { label: "Email", type: "email" },
    password: { label: "Password", type: "password" },
  },
  async authorize(credentials) {
    if (!credentials?.email || !credentials?.password) {
      return null;
    }

    const email = credentials.email.toLowerCase();

    // 1. Find User including their Credentials Account
    // (Password hash id_token mein chhupa hota hai is repo mein)
    const user = await prisma.user.findUnique({
      where: { email },
      include: {
        accounts: {
          where: { provider: "credentials" },
          select: { id_token: true }, 
          take: 1,
        },
      },
    });

    // 2. If User Not Found
    if (!user) {
      logger.warn("User not found", { email, source: LOG_SOURCE });
      return null;
    }

    // 3. Verify Password
    // Credentials password hash is stored on the credentials account record.
    const passwordHash = user.accounts?.[0]?.id_token;
    
    if (!passwordHash) {
      logger.warn("User has no credentials password set", { email, source: LOG_SOURCE });
      return null;
    }

    const isValid = await compare(credentials.password, passwordHash);

    if (!isValid) {
      logger.warn("Invalid password", { email, source: LOG_SOURCE });
      return null;
    }

    return {
      id: user.id,
      email: user.email,
      name: user.name,
      role: user.role,
    };
  },
});