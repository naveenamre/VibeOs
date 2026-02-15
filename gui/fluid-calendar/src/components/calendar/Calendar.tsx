"use client";

import { useEffect } from "react";
import { HiMenu } from "react-icons/hi";
import { IoChevronBack, IoChevronForward } from "react-icons/io5";

import { DayView } from "@/components/calendar/DayView";
import { FeedManager } from "@/components/calendar/FeedManager";
import { MonthView } from "@/components/calendar/MonthView";
import { MultiMonthView } from "@/components/calendar/MultiMonthView";
import { WeekView } from "@/components/calendar/WeekView";

import { addDays, formatDate, newDate, subDays } from "@/lib/date-utils";
import { cn } from "@/lib/utils";

import {
  useCalendarStore,
  useCalendarUIStore,
  useViewStore,
} from "@/store/calendar";
import { useTaskStore } from "@/store/task";

import { CalendarEvent, CalendarFeed } from "@/types/calendar";

// --- INTERFACE ---
interface CalendarProps {
  initialFeeds?: CalendarFeed[];
  initialEvents?: CalendarEvent[];
}

export function Calendar({
  initialFeeds = [],
  initialEvents = [],
}: CalendarProps) {
  const { date: currentDate, setDate, view, setView } = useViewStore();
  const { isSidebarOpen, setSidebarOpen, isHydrated } = useCalendarUIStore();
  // Note: Auto-schedule logic removed as python engine handles it
  const { setFeeds, setEvents } = useCalendarStore();

  // --- HYDRATION & SYNC ---
  useEffect(() => {
    if (initialFeeds.length > 0) setFeeds(initialFeeds);
    if (initialEvents.length > 0) setEvents(initialEvents);

    // Fetch fresh data if needed
    if (!initialFeeds.length || !initialEvents.length) {
      useCalendarStore.getState().loadFromDatabase();
    }

    // Always fetch tasks for the list view
    useTaskStore.getState().fetchTasks();
  }, [initialFeeds, initialEvents, setFeeds, setEvents]);

  // --- NAVIGATION HANDLERS ---
  const handlePrevWeek = () => {
    if (view === "month" || view === "multiMonth") {
      const newDateVal = new Date(currentDate);
      newDateVal.setMonth(newDateVal.getMonth() - 1);
      setDate(newDateVal);
    } else {
      const days = view === "day" ? 1 : 7;
      setDate(subDays(currentDate, days));
    }
  };

  const handleNextWeek = () => {
    if (view === "month" || view === "multiMonth") {
      const newDateVal = new Date(currentDate);
      newDateVal.setMonth(newDateVal.getMonth() + 1);
      setDate(newDateVal);
    } else {
      const days = view === "day" ? 1 : 7;
      setDate(addDays(currentDate, days));
    }
  };

  return (
    <div className="flex h-full w-full bg-background text-foreground">
      
      {/* --- SIDEBAR --- */}
      <aside
        className={cn(
          "h-full w-80 flex-none border-r border-border bg-card",
          "transform transition-transform duration-300 ease-in-out z-20",
          !isHydrated && "opacity-0 duration-0",
          isSidebarOpen ? "translate-x-0" : "-translate-x-full absolute md:relative md:translate-x-0 md:ml-[-20rem]" 
          // Note: Adjusted sidebar logic to behave like original but removed hardcoded style marginLeft
        )}
        style={{ marginLeft: isSidebarOpen ? 0 : "-20rem" }}
      >
        <div className="flex h-full flex-col">
          <div className="p-4 border-b border-border">
             <h2 className="font-semibold text-lg">Calendars</h2>
          </div>
          <div className="flex-1 overflow-y-auto p-2">
            <FeedManager />
          </div>
          {/* SponsorshipBanner Removed - Clean Look */}
        </div>
      </aside>

      {/* --- MAIN CALENDAR AREA --- */}
      <main className="flex min-w-0 flex-1 flex-col bg-background">
        
        {/* LifetimeAccessBanner Removed - Clean Look */}

        {/* HEADER */}
        <header className="flex h-16 flex-none items-center border-b border-border px-4 justify-between">
          
          {/* Left: Menu & Nav */}
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(!isSidebarOpen)}
              className="rounded-lg p-2 text-foreground hover:bg-muted transition-colors"
              title="Toggle Sidebar (b)"
            >
              <HiMenu className="h-5 w-5" />
            </button>

            <div className="flex items-center gap-2 rounded-md border border-input bg-background shadow-sm">
                <button
                  onClick={handlePrevWeek}
                  className="p-2 hover:bg-muted rounded-l-md border-r border-input"
                  title="Previous"
                >
                  <IoChevronBack className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setDate(newDate())}
                  className="px-4 py-1.5 text-sm font-medium hover:bg-muted"
                  title="Go to Today"
                >
                  Today
                </button>
                <button
                  onClick={handleNextWeek}
                  className="p-2 hover:bg-muted rounded-r-md border-l border-input"
                  title="Next"
                >
                  <IoChevronForward className="h-4 w-4" />
                </button>
            </div>

            <h1 className="text-xl font-bold text-foreground hidden md:block ml-2">
              {formatDate(currentDate)}
            </h1>
          </div>

          {/* Right: View Switcher */}
          <div className="flex items-center gap-1 bg-muted p-1 rounded-lg">
            {(['day', 'week', 'month', 'multiMonth'] as const).map((v) => (
                <button
                key={v}
                onClick={() => setView(v)}
                className={cn(
                    "rounded-md px-3 py-1.5 text-sm font-medium transition-all capitalize",
                    view === v
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                )}
                >
                {v === 'multiMonth' ? 'Year' : v}
                </button>
            ))}
          </div>
        </header>

        {/* CALENDAR GRID */}
        <div className="flex-1 overflow-hidden relative">
          {view === "day" ? (
            <DayView currentDate={currentDate} onDateClick={setDate} />
          ) : view === "week" ? (
            <WeekView currentDate={currentDate} onDateClick={setDate} />
          ) : view === "month" ? (
            <MonthView currentDate={currentDate} onDateClick={setDate} />
          ) : (
            <MultiMonthView currentDate={currentDate} onDateClick={setDate} />
          )}
        </div>
      </main>
    </div>
  );
}