"use client";

import { createContext, useCallback, useContext, useEffect, useState, ReactNode } from "react";
import { api, User } from "./api";

const STORAGE_KEY = "giselle:currentUserId";

function readStoredUserId(): number | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(STORAGE_KEY);
  return raw ? Number(raw) : null;
}

function writeStoredUserId(id: number | null) {
  if (typeof window === "undefined") return;
  if (id === null) window.localStorage.removeItem(STORAGE_KEY);
  else window.localStorage.setItem(STORAGE_KEY, String(id));
}

type CurrentUserContextValue = {
  users: User[];
  currentUserId: number | null;
  setCurrentUserId: (id: number) => void;
  createUser: (name: string) => Promise<User>;
  loading: boolean;
};

const CurrentUserContext = createContext<CurrentUserContextValue | null>(null);

/** No real auth here on purpose - this is a 1-2 person local prototype. */
export function CurrentUserProvider({ children }: { children: ReactNode }) {
  const [users, setUsers] = useState<User[]>([]);
  const [currentUserId, setCurrentUserIdState] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUsers = useCallback(async () => {
    const list = await api.listUsers();
    setUsers(list);
    return list;
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const list = await refreshUsers();
      if (cancelled) return;
      const stored = readStoredUserId();
      if (stored && list.some((u) => u.id === stored)) {
        setCurrentUserIdState(stored);
      } else if (list.length > 0) {
        setCurrentUserIdState(list[0].id);
        writeStoredUserId(list[0].id);
      }
      setLoading(false);
    })();
    return () => {
      cancelled = true;
    };
  }, [refreshUsers]);

  const setCurrentUserId = useCallback((id: number) => {
    setCurrentUserIdState(id);
    writeStoredUserId(id);
  }, []);

  const createUser = useCallback(
    async (name: string) => {
      const user = await api.createUser(name);
      await refreshUsers();
      setCurrentUserId(user.id);
      return user;
    },
    [refreshUsers, setCurrentUserId]
  );

  return (
    <CurrentUserContext.Provider value={{ users, currentUserId, setCurrentUserId, createUser, loading }}>
      {children}
    </CurrentUserContext.Provider>
  );
}

export function useCurrentUser(): CurrentUserContextValue {
  const ctx = useContext(CurrentUserContext);
  if (!ctx) throw new Error("useCurrentUser must be used within a CurrentUserProvider");
  return ctx;
}
