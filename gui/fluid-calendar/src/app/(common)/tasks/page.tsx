import { prisma } from "@/lib/prisma";
import { Button } from "@/components/ui/button";
import { Check, X, EyeOff } from "lucide-react";
import { cn } from "@/lib/utils";
import { revalidatePath } from "next/cache";

// --- SERVER ACTION (Direct DB Update) ---
async function updateTaskStatus(taskId: string, status: string) {
  "use server";
  
  if (taskId) {
      try {
        // Attempt to update Task table directly using ID
        // Note: Assuming 'CalendarEvent.id' maps to 'Task.id' or 'Task.calendar_event_id'
        // For VibeOS logic, let's assume we are updating the Task entity.
        
        await prisma.task.update({
            where: { id: taskId },
            data: { 
                status: status,
                completedAt: status === "COMPLETED" ? new Date() : null
            }
        });
        revalidatePath("/tasks"); 
      } catch (e) {
          console.log("Error updating task status:", e);
      }
  }
}

export default async function DailyHisaabPage() {
  // 1. Get Today's Schedule (Start of day to End of day)
  const startOfDay = new Date();
  startOfDay.setHours(0, 0, 0, 0);
  
  const endOfDay = new Date();
  endOfDay.setHours(23, 59, 59, 999);

  // Fetch Calendar Events for Today
  // We fetch from CalendarEvent because that's what's scheduled by engine.py
  const events = await prisma.calendarEvent.findMany({
    where: {
      start: {
        gte: startOfDay,
        lte: endOfDay,
      },
    },
    orderBy: { start: "asc" },
  });

  return (
    <div className="max-w-4xl mx-auto py-10 px-4">
      <div className="flex items-center justify-between mb-8">
        <div>
            <h1 className="text-3xl font-bold tracking-tight">Aaj Ka Hisaab 📝</h1>
            <p className="text-muted-foreground mt-1">
                {startOfDay.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
            </p>
        </div>
      </div>

      <div className="space-y-4">
        {events.length === 0 ? (
            <div className="text-center py-20 bg-muted/20 rounded-xl border border-dashed">
                <div className="text-4xl mb-4">🎉</div>
                <h3 className="text-xl font-semibold">No tasks scheduled!</h3>
                <p className="text-muted-foreground">System is chill. You should be too.</p>
            </div>
        ) : (
            events.map((event) => {
                const startTime = new Date(event.start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                const endTime = new Date(event.end).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                const isPast = new Date(event.end) < new Date();

                return (
                    <div key={event.id} className={cn(
                        "flex items-center justify-between p-4 rounded-xl border bg-card transition-all hover:shadow-md group",
                        isPast ? "opacity-70 bg-muted/30" : "border-l-4 border-l-orange-500"
                    )}>
                        {/* Time & Title */}
                        <div className="flex items-center gap-6">
                            <div className="flex flex-col items-center min-w-[80px] text-center border-r pr-6 border-border/50">
                                <span className="text-lg font-bold font-mono tracking-tight">{startTime}</span>
                                <span className="text-[10px] text-muted-foreground uppercase tracking-wider">{endTime}</span>
                            </div>
                            
                            <div>
                                <h3 className="font-semibold text-lg leading-none mb-1.5">{event.title}</h3>
                                <span className="inline-flex items-center rounded-md bg-secondary/50 px-2 py-1 text-xs font-medium text-secondary-foreground ring-1 ring-inset ring-gray-500/10">
                                    {isPast ? "Past" : "Scheduled"}
                                </span>
                            </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex items-center gap-2 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity">
                            <form action={updateTaskStatus.bind(null, event.id, "COMPLETED")}>
                                <Button size="sm" variant="outline" className="text-green-600 hover:bg-green-50 hover:text-green-700 hover:border-green-200 h-9">
                                    <Check className="w-4 h-4 mr-1.5" /> Done
                                </Button>
                            </form>
                            
                            <form action={updateTaskStatus.bind(null, event.id, "MISSED")}>
                                <Button size="sm" variant="outline" className="text-red-600 hover:bg-red-50 hover:text-red-700 hover:border-red-200 h-9">
                                    <X className="w-4 h-4 mr-1.5" /> Missed
                                </Button>
                            </form>

                            <form action={updateTaskStatus.bind(null, event.id, "IGNORED")}>
                                <Button size="icon" variant="ghost" className="text-muted-foreground hover:text-foreground h-9 w-9" title="Ignore">
                                    <EyeOff className="w-4 h-4" />
                                </Button>
                            </form>
                        </div>
                    </div>
                );
            })
        )}
      </div>
    </div>
  );
}