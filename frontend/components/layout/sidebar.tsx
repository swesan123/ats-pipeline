"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/jobs", label: "Jobs" },
  { href: "/experience", label: "Experience" },
  { href: "/projects", label: "Projects" },
  { href: "/skills", label: "Skills" },
  { href: "/resumes", label: "Resumes and Cover Letters" },
  { href: "/analytics", label: "Analytics" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r bg-sidebar" aria-label="Main navigation">
      <div className="p-4 border-b">
        <h1 className="text-xl font-semibold">ATS Pipeline</h1>
      </div>
      <nav className="p-2" aria-label="Main navigation">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "block px-4 py-2 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
                    isActive
                      ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                      : "text-sidebar-foreground hover:bg-sidebar-accent/50"
                  )}
                  aria-current={isActive ? "page" : undefined}
                >
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </aside>
  );
}
