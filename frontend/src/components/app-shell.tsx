import { Link, useRouterState } from "@tanstack/react-router";
import {
  LayoutDashboard,
  FilePlus2,
  History,
  Settings,
  ShieldCheck,
  UserCircle2,
} from "lucide-react";
import type { ReactNode } from "react";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, exact: true },
  { to: "/nouveau", label: "Nouveau dossier", icon: FilePlus2 },
  { to: "/historique", label: "Historique", icon: History },
  { to: "/parametres", label: "Paramètres", icon: Settings },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <div className="flex min-h-screen w-full bg-background text-foreground">
      <aside className="hidden md:flex w-64 flex-col bg-sidebar text-sidebar-foreground border-r border-sidebar-border">
        <div className="flex items-center gap-2 px-5 py-6 border-b border-sidebar-border">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-sidebar-primary text-sidebar-primary-foreground">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div className="leading-tight">
            <div className="text-sm font-semibold tracking-tight">InsuranceDV</div>
            <div className="text-[11px] text-sidebar-foreground/60">
              Document Validation
            </div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map((item) => {
            const active = item.exact
              ? pathname === item.to
              : pathname.startsWith(item.to);
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
                  active
                    ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                    : "text-sidebar-foreground/80 hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground"
                }`}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="px-4 py-4 border-t border-sidebar-border text-[11px] text-sidebar-foreground/50">
          v0.1 · Tunisie
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 border-b border-border bg-card/50 backdrop-blur px-6 flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            Vérification automatique des dossiers d'assurance auto
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right leading-tight">
              <div className="text-sm font-medium">Sami Trabelsi</div>
              <div className="text-[11px] text-muted-foreground">
                Agent · Agence Tunis Centre
              </div>
            </div>
            <div className="h-9 w-9 rounded-full bg-primary/10 text-primary flex items-center justify-center">
              <UserCircle2 className="h-5 w-5" />
            </div>
          </div>
        </header>

        <main className="flex-1 min-w-0">{children}</main>
      </div>
    </div>
  );
}