import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types";

interface AuthStore {
  user: User | null;
  token: string | null;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      setAuth: (user, token) => {
        localStorage.setItem("ag_sas_token", token);
        set({ user, token });
      },
      clearAuth: () => {
        localStorage.removeItem("ag_sas_token");
        set({ user: null, token: null });
      },
    }),
    { name: "ag-sas-auth", partialize: (s) => ({ user: s.user, token: s.token }) }
  )
);
