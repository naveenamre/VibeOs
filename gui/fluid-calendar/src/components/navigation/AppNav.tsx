"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  Calendar, 
  CheckSquare, 
  Zap, 
  Search, 
  Keyboard 
} from "lucide-react"; // ✅ Switched to Lucide for consistency

import { cn } from "@/lib/utils";
import { useShortcutsStore } from "@/store/shortcuts";
import { ThemeToggle } from "./ThemeToggle";
import { UserMenu } from "./UserMenu";

interface AppNavProps {
  className?: string;
}

export function AppNav({ className }: AppNavProps) {
  const pathname = usePathname();
  const { setOpen: setShortcutsOpen } = useShortcutsStore();

  // Function to trigger command palette
  const openCommandPalette = () => {
    // Simulate Cmd+K / Ctrl+K
    const event = new KeyboardEvent("keydown", {
      key: "k",
      metaKey: true,
      ctrlKey: true, // Support Windows/Linux too
      bubbles: true,
    });
    document.dispatchEvent(event);
  };

  const links = [
    { href: "/calendar", label: "Calendar", icon: Calendar },
    { href: "/tasks", label: "Tasks", icon: CheckSquare },
    { href: "/focus", label: "Focus", icon: Zap, highlight: true }, // 🔥 Kept the highlight logic
  ];

  return (
    <nav
      className={cn(
        "z-10 h-16 flex-none border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60",
        className
      )}
    >
      <div className="h-full px-4 max-w-7xl mx-auto">
        <div className="flex h-full items-center justify-between">
          
          {/* LEFT: Logo & Links */}
          <div className="flex items-center gap-8">
            <Link
              href="/focus"
              className={cn(
                "flex items-center gap-2 mr-4 transition-opacity hover:opacity-80"
              )}
            >
              {/* VibeOS Logo Style */}
              <div className="h-8 w-8 bg-orange-500 rounded-lg flex items-center justify-center shadow-sm">
                <span className="text-white font-bold text-lg">V</span>
              </div>
              <span className="font-bold text-xl tracking-tight hidden md:block">VibeOS</span>
            </Link>

            {/* Navigation Links */}
            <div className="hidden md:flex items-center gap-1">
              {links.map((link) => {
                const Icon = link.icon;
                const isActive = pathname === link.href;

                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={cn(
                      "inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                      isActive
                        ? "bg-primary/10 text-primary"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground",
                      // Focus Mode Highlight Logic (Vibe Check)
                      link.highlight && !isActive && "text-orange-500 hover:text-orange-600 hover:bg-orange-50"
                    )}
                  >
                    <Icon className={cn("h-4 w-4", link.highlight && "text-orange-500")} />
                    {link.label}
                  </Link>
                );
              })}
            </div>
          </div>

          {/* RIGHT: Actions */}
          <div className="flex items-center gap-2">
            
            {/* Search Trigger */}
            <button
              onClick={openCommandPalette}
              className="flex items-center gap-1.5 rounded-md border border-input bg-transparent px-3 py-1.5 text-xs font-medium text-muted-foreground shadow-sm hover:bg-accent hover:text-accent-foreground"
              title="Search (⌘K)"
            >
              <Search className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Search</span>
              <kbd className="hidden rounded bg-muted px-1.5 font-mono text-[10px] font-medium opacity-100 sm:inline-flex">
                ⌘K
              </kbd>
            </button>

            <ThemeToggle />

            {/* Shortcuts Trigger */}
            <button
              onClick={() => setShortcutsOpen(true)}
              className="flex items-center justify-center rounded-md w-8 h-8 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
              title="Keyboard Shortcuts (?)"
            >
              <Keyboard className="h-4 w-4" />
            </button>

            <UserMenu />
          </div>
        </div>
      </div>
    </nav>
  );
}