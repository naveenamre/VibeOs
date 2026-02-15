import { prisma } from "@/lib/prisma";

// ✅ Server Component: Direct DB Access (No 'use client' needed)
export default async function ArjunMode() {
  const now = new Date();

  // 1. Fetch Current Active Task (Jo abhi chal raha hai)
  const currentTask = await prisma.calendarEvent.findFirst({
    where: {
      start: { lte: now },
      end: { gte: now },
    },
    orderBy: { start: 'desc' } // Overlap hua toh latest wala dikhayega
  });

  // 2. Fetch Next Task (Motivation ke liye)
  const nextTask = await prisma.calendarEvent.findFirst({
    where: {
      start: { gt: now },
    },
    orderBy: { start: 'asc' },
  });

  return (
    <div className="flex flex-col h-full items-center justify-center bg-background p-6 text-center animate-in fade-in duration-700">
      
      {/* 🎯 MAIN FOCUS AREA */}
      {currentTask ? (
        <div className="flex flex-col items-center gap-8 max-w-5xl w-full">
          
          {/* Badge */}
          <div className="inline-flex items-center rounded-full border border-orange-500/50 bg-orange-500/10 px-6 py-2 text-sm font-bold tracking-[0.2em] text-orange-500 shadow-[0_0_20px_rgba(249,115,22,0.3)] animate-pulse">
            👁️ ARJUN MODE ACTIVE
          </div>
          
          {/* The Task Title */}
          <h1 className="text-7xl md:text-9xl font-black tracking-tighter leading-[0.9] bg-gradient-to-b from-foreground to-muted-foreground/50 bg-clip-text text-transparent drop-shadow-2xl">
            {currentTask.title}
          </h1>

          {/* Time Display */}
          <div className="flex items-center gap-6 text-3xl md:text-5xl font-mono text-muted-foreground mt-4 bg-card/50 p-6 rounded-3xl border border-border/50 backdrop-blur-sm">
            <span className="text-foreground font-bold">
              {currentTask.start.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}
            </span>
            <span className="text-orange-500 animate-pulse">➔</span>
            <span className="text-red-500 font-bold decoration-red-500/30 underline decoration-4 underline-offset-8">
              {currentTask.end.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}
            </span>
          </div>

          {/* Motivation Tag */}
          <div className="mt-8 transform hover:scale-105 transition-transform duration-300">
            <span className="bg-foreground text-background px-8 py-3 rounded-full text-lg font-bold shadow-lg">
              ⏳ TIMELINE IS TICKING...
            </span>
          </div>

        </div>
      ) : (
        // 💤 CHILL STATE (Jab koi task nahi hai)
        <div className="flex flex-col items-center gap-6 opacity-60">
          <div className="h-32 w-32 rounded-full bg-secondary/30 flex items-center justify-center text-6xl">
            🧘
          </div>
          <h1 className="text-5xl font-bold tracking-tight">Abhi Free Time Hai Bhai!</h1>
          <p className="text-2xl text-muted-foreground max-w-md leading-relaxed">
            Ya toh chill kar, ya agla code likh. <br/>
            <span className="text-orange-500 font-medium">System is waiting for input.</span>
          </p>
        </div>
      )}

      {/* 👇 UP NEXT (Footer Hint) */}
      {nextTask && (
        <div className="absolute bottom-10 left-0 right-0 flex justify-center">
          <div className="flex flex-col items-center gap-2 opacity-50 hover:opacity-100 transition-opacity duration-300 group cursor-default">
            <p className="text-[10px] uppercase tracking-[0.3em] font-semibold text-muted-foreground group-hover:text-orange-500 transition-colors">
              Up Next
            </p>
            <div className="flex items-center gap-4 bg-muted/40 px-6 py-3 rounded-2xl border border-border/50 backdrop-blur-md shadow-sm group-hover:shadow-md group-hover:bg-muted/60 transition-all">
              <span className="font-mono text-orange-500 font-bold">
                {nextTask.start.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}
              </span>
              <div className="h-4 w-[1px] bg-border"></div>
              <span className="font-semibold text-lg text-foreground/90">
                {nextTask.title}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}