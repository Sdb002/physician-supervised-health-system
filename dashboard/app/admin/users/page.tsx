"use client";

import { useEffect, useMemo, useState } from "react";
import { api, User } from "@/lib/api";
import { formatDate } from "@/lib/clinical-terms";
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
        subtitle={users ? `${users.length} accounts across all roles` : undefined}
        action={
          <SearchInput
            value={query}
            onChange={setQuery}
            placeholder="Search name, email, PID or DID"
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
        <div className="overflow-x-auto rounded-xl border border-line bg-surface">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-line bg-surface-soft text-ink-muted">
              <tr>
                <th scope="col" className="px-5 py-3 font-semibold">User</th>
                <th scope="col" className="px-4 py-3 font-semibold">Role</th>
                <th scope="col" className="px-4 py-3 font-semibold">Status</th>
                <th scope="col" className="px-4 py-3 font-semibold">Joined</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {visible.map((user) => (
                <tr key={user.id} className="hover:bg-surface-soft">
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-3">
                      <Avatar name={user.name} />
                      <div className="min-w-0">
                        <p className="font-semibold text-ink">{user.name}</p>
                        <p className="text-ink-muted">
                          {userDisplayId(user) && <span>{userDisplayId(user)}, </span>}
                          {user.email}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <Badge kind={user.role}>{user.role}</Badge>
                  </td>
                  <td className="px-4 py-3">
                    <Badge kind={user.status}>{user.status}</Badge>
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-ink-muted">
                    {formatDate(user.created_at)}
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
