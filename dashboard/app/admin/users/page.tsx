"use client";

import { useEffect, useMemo, useState } from "react";
import { api, User } from "@/lib/api";
import { did, pid } from "@/lib/format";
import { IconUsers } from "@/components/icons";
import {
  Avatar,
  Badge,
  EmptyState,
  ErrorNote,
  PageHeader,
  SearchInput,
  Skeleton,
} from "@/components/ui";

function userDisplayId(user: User): string | null {
  if (user.role === "doctor") return did(user.id);
  if (user.role === "patient" && user.patient_id != null) return pid(user.patient_id);
  return null;
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<User[] | null>(null);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.adminUsers().then(setUsers).catch((e) => setError(e.message));
  }, []);

  const visible = useMemo(() => {
    if (users === null) return null;
    const q = query.trim().toLowerCase();
    if (!q) return users;
    return users.filter((u) =>
      [u.name, u.email, u.role, u.status, userDisplayId(u) ?? ""]
        .join(" ")
        .toLowerCase()
        .includes(q)
    );
  }, [users, query]);

  if (error) return <ErrorNote message={error} />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Users"
        subtitle={users ? `${users.length} accounts across all roles` : "Loading…"}
        action={
          <SearchInput
            value={query}
            onChange={setQuery}
            placeholder="Search by name, email, PID/DID…"
          />
        }
      />

      {visible === null ? (
        <Skeleton className="h-48" />
      ) : visible.length === 0 ? (
        <EmptyState
          title={query ? "No users match your search" : "No users yet"}
          icon={<IconUsers className="h-5 w-5" />}
        />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-line bg-surface shadow-sm">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-line text-xs uppercase tracking-wide text-ink-muted">
              <tr>
                <th className="px-4 py-3">ID</th>
                <th className="px-4 py-3">User</th>
                <th className="px-4 py-3">Role</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Joined</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {visible.map((user) => (
                <tr key={user.id} className="hover:bg-surface-soft">
                  <td className={`px-4 py-3 font-mono text-xs font-semibold ${
                    user.role === "doctor" ? "text-teal-700" : "text-emerald-700"
                  }`}>
                    {userDisplayId(user) ?? <span className="text-ink-muted">—</span>}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <Avatar name={user.name} />
                      <div>
                        <p className="font-medium text-ink">{user.name}</p>
                        <p className="text-xs text-ink-muted">{user.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <Badge kind={user.role}>{user.role}</Badge>
                  </td>
                  <td className="px-4 py-3">
                    <Badge kind={user.status}>{user.status}</Badge>
                  </td>
                  <td className="px-4 py-3 text-ink-muted">
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
