import Link from "next/link";
import { UserSwitcher } from "./UserSwitcher";
import { LocationStatus } from "./LocationStatus";

export function Nav() {
  return (
    <header className="flex items-center justify-between border-b border-zinc-200 px-6 py-3 dark:border-zinc-800">
      <div className="flex items-center gap-6">
        <span className="font-semibold">giselle</span>
        <nav className="flex gap-4 text-sm text-zinc-600 dark:text-zinc-300">
          <Link href="/" className="hover:underline">
            Recommended
          </Link>
          <Link href="/favorites" className="hover:underline">
            Pick favorites
          </Link>
        </nav>
      </div>
      <div className="flex items-center gap-3">
        <LocationStatus />
        <UserSwitcher />
      </div>
    </header>
  );
}
