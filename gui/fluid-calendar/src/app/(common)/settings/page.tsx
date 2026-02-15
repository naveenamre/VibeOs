"use client";

import { useEffect, useMemo, useState } from "react";
// Removed Waitlist Imports to fix build error (since files were deleted)

import { AccountManager } from "@/components/settings/AccountManager";
import { AutoScheduleSettings } from "@/components/settings/AutoScheduleSettings";
import { CalendarSettings } from "@/components/settings/CalendarSettings";
import { ImportExportSettings } from "@/components/settings/ImportExportSettings";
import { LogViewer } from "@/components/settings/LogViewer";
import { NotificationSettings } from "@/components/settings/NotificationSettings";
import { SystemSettings } from "@/components/settings/SystemSettings";
import { TaskSyncSettings } from "@/components/settings/TaskSyncSettings";
import { UserManagement } from "@/components/settings/UserManagement";
import { UserSettings } from "@/components/settings/UserSettings";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

import { cn } from "@/lib/utils";

import { useAdmin } from "@/hooks/use-admin";

import { useSettingsStore } from "@/store/settings";

// --- TYPES ---
type SettingsTab =
  | "accounts"
  | "user"
  | "calendar"
  | "auto-schedule"
  | "system"
  | "task-sync"
  | "logs"
  | "user-management"
  | "import-export"
  | "admin-dashboard"
  | "notifications";

export default function SettingsPage() {
  const [isHydrated, setIsHydrated] = useState(false);
  const { isAdmin, isLoading: isAdminLoading } = useAdmin();
  const { initializeSettings } = useSettingsStore();

  // Always initialize settings on mount
  useEffect(() => {
    initializeSettings();
  }, [initializeSettings]);

  // --- TABS CONFIGURATION ---
  const tabs = useMemo(() => {
    const baseTabs = [
      { id: "accounts", label: "Accounts" },
      { id: "user", label: "User" },
      { id: "calendar", label: "Calendar" },
      { id: "auto-schedule", label: "Auto-Schedule" },
      { id: "task-sync", label: "Task Sync" },
      { id: "notifications", label: "Notifications" },
      { id: "import-export", label: "Import/Export" },
    ] as const;

    // Add admin-only tabs
    if (isAdmin) {
      const adminTabs = [
        { id: "system", label: "System" },
        { id: "logs", label: "Logs" },
        { id: "user-management", label: "Users" },
      ] as const;

      // Note: Waitlist removed from here because files are deleted
      
      return [...baseTabs, ...adminTabs] as const;
    }

    return baseTabs;
  }, [isAdmin]);

  const [activeTab, setActiveTab] = useState<SettingsTab>("accounts");

  // --- HASH HANDLING ---
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.slice(1) as SettingsTab;

      const allPossibleTabIds: SettingsTab[] = [
        "accounts",
        "user",
        "calendar",
        "auto-schedule",
        "task-sync",
        "system",
        "logs",
        "user-management",
        "import-export",
        "admin-dashboard",
        "notifications",
      ];

      if (allPossibleTabIds.includes(hash)) {
        setActiveTab(hash);
      }
    };

    handleHashChange();
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    if (isHydrated) {
      window.location.hash = activeTab;
    }
  }, [activeTab, isHydrated]);

  // --- CONTENT RENDERER ---
  const renderContent = () => {
    const adminOnlyTabs = [
      "system",
      "logs",
      "user-management",
      "admin-dashboard",
    ];

    if (adminOnlyTabs.includes(activeTab) && isAdminLoading) {
      return (
        <div className="flex flex-col items-center justify-center p-8 text-center">
          <p className="text-muted-foreground">Checking access privileges...</p>
        </div>
      );
    }

    if (adminOnlyTabs.includes(activeTab) && !isAdmin) {
      return (
        <div className="flex flex-col items-center justify-center p-8 text-center">
          <h2 className="mb-4 text-2xl font-bold">Admin Access Required</h2>
          <p className="text-muted-foreground">
            You need administrator privileges to access this section.
          </p>
        </div>
      );
    }

    switch (activeTab) {
      case "accounts":
        return <AccountManager />;
      case "user":
        return <UserSettings />;
      case "calendar":
        return <CalendarSettings />;
      case "auto-schedule":
        return <AutoScheduleSettings />;
      case "task-sync":
        return <TaskSyncSettings />;
      case "notifications":
        return <NotificationSettings />;
      case "system":
        return <SystemSettings />;
      case "logs":
        return <LogViewer />;
      case "user-management":
        return <UserManagement />;
      case "import-export":
        return <ImportExportSettings />;
      case "admin-dashboard":
        return (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <h2 className="mb-4 text-2xl font-bold">Admin Dashboard</h2>
            <p className="mb-4 text-muted-foreground">
              Access the full admin dashboard to manage the application.
            </p>
            <Button asChild>
              <a href="/admin">Go to Admin Dashboard</a>
            </Button>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="container py-6">
      <div className="flex flex-col lg:flex-row lg:space-x-12 lg:space-y-0">
        
        {/* Sidebar Navigation */}
        <aside className="lg:w-1/5">
          <Card>
            <nav className="space-y-1 p-1">
              {tabs.map((tab) => (
                <a
                  key={tab.id}
                  href={`#${tab.id}`}
                  onClick={(e) => {
                    e.preventDefault();
                    setActiveTab(tab.id as SettingsTab);
                  }}
                  className={cn(
                    "flex w-full items-center rounded-md px-3 py-2 text-sm font-medium transition-colors",
                    !isHydrated && "duration-0",
                    activeTab === tab.id
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                >
                  {tab.label}
                </a>
              ))}
            </nav>
          </Card>
        </aside>

        {/* Content Area */}
        <div className="mt-6 flex-1 lg:mt-0">
          <div className="space-y-6">
            <div className={cn("space-y-8", !isHydrated && "opacity-0")}>
              {renderContent()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}