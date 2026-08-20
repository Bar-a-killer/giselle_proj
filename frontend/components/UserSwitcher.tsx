"use client";

import { useState } from "react";
import { useCurrentUser } from "@/lib/currentUser";

export function UserSwitcher() {
  const { users, currentUserId, setCurrentUserId, createUser, loading } = useCurrentUser();
  const [newName, setNewName] = useState("");
  const [creating, setCreating] = useState(false);

  if (loading) return <div className="text-sm text-zinc-400">Loading...</div>;

  return (
    <div className="flex items-center gap-2 text-sm">
      {users.length > 0 && (
        <select
          value={currentUserId ?? ""}
          onChange={(e) => setCurrentUserId(Number(e.target.value))}
          className="rounded-md border border-zinc-300 bg-transparent px-2 py-1 dark:border-zinc-700"
        >
          {users.map((u) => (
            <option key={u.id} value={u.id}>
              {u.name}
            </option>
          ))}
        </select>
      )}
      {creating ? (
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            if (!newName.trim()) return;
            await createUser(newName.trim());
            setNewName("");
            setCreating(false);
          }}
          className="flex items-center gap-1"
        >
          <input
            autoFocus
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Your name"
            className="w-28 rounded-md border border-zinc-300 px-2 py-1 dark:border-zinc-700 dark:bg-zinc-900"
          />
          <button type="submit" className="rounded-md bg-zinc-900 px-2 py-1 text-white dark:bg-zinc-100 dark:text-zinc-900">
            Add
          </button>
        </form>
      ) : (
        <button onClick={() => setCreating(true)} className="text-zinc-500 hover:underline">
          + new person
        </button>
      )}
    </div>
  );
}
