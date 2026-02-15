"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";

import { DndProvider } from "@/components/dnd/DndProvider";
import { AppNav } from "@/components/navigation/AppNav";
import { PrivacyProvider } from "@/components/providers/PrivacyProvider";
import { SessionProvider } from "@/components/providers/SessionProvider";
import { SetupCheck } from "@/components/setup/SetupCheck";
import { CommandPalette } from "@/components/ui/command-palette";
import { CommandPaletteHint } from "@/components/ui/command-palette-hint";
import { CommandPaletteFab } from "@/components/ui/command-palette-fab"; // Fab added based on your snippet
import { ShortcutsModal } from "@/components/ui/shortcuts-modal";

import { usePageTitle } from "@/hooks/use-page-title";
import { useShortcutsStore } from "@/store/shortcuts";

// Dynamically import the NotificationProvider based on SAAS flag
const NotificationProvider = dynamic<{ children: React.ReactNode }>(
  () =>
    import(
      `@/components/providers/NotificationProvider${
        process.env.NEXT_PUBLIC_ENABLE_SAAS_FEATURES === "true"
          ? ".saas"
          : ".open"
      }`
    ).then((mod) => mod.NotificationProvider),
  {
    ssr: false,
    loading: () => <>{/* Render nothing while loading */}</>,
  }
);

export default function CommonLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const { isOpen: shortcutsOpen, setOpen: setShortcutsOpen } = useShortcutsStore();

  // Use the page title hook
  usePageTitle();

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setCommandPaletteOpen((open) => !open);
      } else if (e.key === "?" && !(e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setShortcutsOpen(true);
      }
    };

    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, [setShortcutsOpen]);

  return (
    <SessionProvider>
      <PrivacyProvider>
        <DndProvider>
          {/* System Checks & Modals */}
          <SetupCheck />
          
          <CommandPalette
            open={commandPaletteOpen}
            onOpenChange={setCommandPaletteOpen}
          />
          <CommandPaletteHint />
          <CommandPaletteFab /> 
          
          <ShortcutsModal
            isOpen={shortcutsOpen}
            onClose={() => setShortcutsOpen(false)}
          />

          {/* 🔥 MAIN LAYOUT STRUCTURE (Top Bar Style) */}
          {/* Changed from default flex-row to flex-col for Top Navigation */}
          <div className="flex h-screen flex-col overflow-hidden bg-background text-foreground">
            
            {/* 1. Top Navigation */}
            <AppNav />

            {/* 2. Main Content (Scrollable) */}
            <main className="flex-1 overflow-auto relative flex flex-col">
              <NotificationProvider>
                {children}
              </NotificationProvider>
            </main>
            
          </div>
        </DndProvider>
      </PrivacyProvider>
    </SessionProvider>
  );
}