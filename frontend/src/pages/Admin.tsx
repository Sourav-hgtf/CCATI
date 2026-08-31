import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchApi } from '../api/client';
import { listUsersApi, createUserApi, updateUserRoleApi, updateUserStatusApi, UserRecord } from '../api/auth';
import { Shield, History, Users, UserPlus, CheckCircle2, XCircle, AlertCircle, Sparkles } from 'lucide-react';

interface AuditLogItem {
  id: number;
  timestamp: string;
  actor_email: string;
  actor_role: string;
  action: string;
  target_resource: string;
  details: string;
  status: string;
}

interface AuditResponse {
  total: number;
  logs: AuditLogItem[];
}

const AVAILABLE_ROLES = [
  'Admin',
  'RetentionManager',
  'Analyst',
  'ModelManager',
  'Operations',
  'Viewer',
];

export const Admin: React.FC = () => {
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newUser, setNewUser] = useState({
    email: '',
    username: '',
    full_name: '',
    password: '',
    role: 'Viewer',
  });
  const [formError, setFormError] = useState<string | null>(null);

  // Queries
  const { data: auditData, isLoading: auditLoading } = useQuery<AuditResponse>({
    queryKey: ['admin-audit-logs'],
    queryFn: () => fetchApi<AuditResponse>('/admin/audit-logs'),
  });

  const { data: userData, isLoading: usersLoading } = useQuery<{ total: number; users: UserRecord[] }>({
    queryKey: ['admin-users-list'],
    queryFn: () => listUsersApi(),
  });

  // Mutations
  const createUserMutation = useMutation({
    mutationFn: createUserApi,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users-list'] });
      queryClient.invalidateQueries({ queryKey: ['admin-audit-logs'] });
      setShowCreateModal(false);
      setNewUser({ email: '', username: '', full_name: '', password: '', role: 'Viewer' });
      setFormError(null);
    },
    onError: (err: any) => {
      setFormError(err.message || 'Failed to create user');
    },
  });

  const updateRoleMutation = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) => updateUserRoleApi(userId, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users-list'] });
      queryClient.invalidateQueries({ queryKey: ['admin-audit-logs'] });
    },
    onError: (err: any) => {
      alert(err.message || 'Failed to update role');
    },
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ userId, isActive }: { userId: string; isActive: boolean }) => updateUserStatusApi(userId, isActive),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users-list'] });
      queryClient.invalidateQueries({ queryKey: ['admin-audit-logs'] });
    },
    onError: (err: any) => {
      alert(err.message || 'Failed to update status');
    },
  });

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    if (newUser.password.length < 8) {
      setFormError('Password must be at least 8 characters long.');
      return;
    }
    createUserMutation.mutate(newUser);
  };

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-white flex items-center space-x-2">
            <Shield className="w-6 h-6 text-[#F5A623]" />
            <span>Admin & User Management</span>
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            System user provisioning, role assignments (RBAC), and security audit trail.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center space-x-2 px-4 py-2 bg-[#F5A623] hover:bg-[#E09612] text-black font-bold rounded-xl text-xs transition shadow-lg shadow-[#F5A623]/20"
        >
          <UserPlus className="w-4 h-4" />
          <span>Add System User</span>
        </button>
      </div>

      {/* User Management Section */}
      <div className="bg-[#18181E] border border-[#2A2A36] rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Users className="w-5 h-5 text-[#F5A623]" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              System Users & Role-Based Access Control
            </h2>
          </div>
          <span className="text-xs font-mono text-gray-400">Total Users: {userData?.total || 0}</span>
        </div>

        {usersLoading ? (
          <div className="p-8 text-center text-xs text-gray-500 font-mono">Loading users...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-gray-300">
              <thead className="bg-[#101014] text-gray-400 uppercase text-[10px] font-mono">
                <tr>
                  <th className="p-3">User ID</th>
                  <th className="p-3">Full Name</th>
                  <th className="p-3">Email</th>
                  <th className="p-3">Role</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#262632]">
                {userData?.users.map((u) => (
                  <tr key={u.user_id} className="hover:bg-white/[0.02] transition">
                    <td className="p-3 font-mono text-gray-400">{u.user_id}</td>
                    <td className="p-3 font-semibold text-white">{u.name}</td>
                    <td className="p-3 text-gray-300">{u.email}</td>
                    <td className="p-3">
                      <select
                        value={u.role}
                        onChange={(e) => updateRoleMutation.mutate({ userId: u.user_id, role: e.target.value })}
                        className="bg-[#101014] border border-[#2E2E38] rounded-lg px-2.5 py-1 text-xs text-[#F5A623] font-semibold focus:outline-none focus:border-[#F5A623]"
                      >
                        {AVAILABLE_ROLES.map((r) => (
                          <option key={r} value={r}>
                            {r}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="p-3">
                      {u.is_active ? (
                        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[10px] font-medium">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>Active</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/30 text-[10px] font-medium">
                          <XCircle className="w-3 h-3" />
                          <span>Deactivated</span>
                        </span>
                      )}
                    </td>
                    <td className="p-3">
                      <button
                        onClick={() => updateStatusMutation.mutate({ userId: u.user_id, isActive: !u.is_active })}
                        className={`text-[11px] font-semibold px-2.5 py-1 rounded-lg border transition ${
                          u.is_active
                            ? 'border-red-500/30 text-red-400 hover:bg-red-500/10'
                            : 'border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10'
                        }`}
                      >
                        {u.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Security Audit Log Table */}
      <div className="bg-[#18181E] border border-[#2A2A36] rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <History className="w-5 h-5 text-blue-400" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              Immutable Security Audit Trail
            </h2>
          </div>
          <span className="text-xs font-mono text-gray-400">Total Entries: {auditData?.total || 0}</span>
        </div>

        {auditLoading ? (
          <div className="p-8 text-center text-xs text-gray-500 font-mono">Loading audit logs...</div>
        ) : (
          <div className="overflow-x-auto max-h-96">
            <table className="w-full text-left text-xs text-gray-300">
              <thead className="sticky top-0 bg-[#101014] text-gray-400 uppercase text-[10px] font-mono">
                <tr>
                  <th className="p-3">Log ID</th>
                  <th className="p-3">Timestamp (UTC)</th>
                  <th className="p-3">Actor Email</th>
                  <th className="p-3">Actor Role</th>
                  <th className="p-3">Action Event</th>
                  <th className="p-3">Target Resource</th>
                  <th className="p-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#262632]">
                {auditData?.logs.map((log) => (
                  <tr key={log.id} className="hover:bg-white/[0.02] transition">
                    <td className="p-3 font-mono text-gray-500">#{log.id}</td>
                    <td className="p-3 font-mono text-gray-400">{new Date(log.timestamp).toLocaleString()}</td>
                    <td className="p-3 text-blue-400 font-medium">{log.actor_email}</td>
                    <td className="p-3 font-mono text-xs">{log.actor_role}</td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 font-mono text-[10px] border border-blue-500/30">
                        {log.action}
                      </span>
                    </td>
                    <td className="p-3 font-mono text-gray-400">{log.target_resource}</td>
                    <td className="p-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                          log.status === 'SUCCESS'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                            : 'bg-red-500/10 text-red-400 border border-red-500/30'
                        }`}
                      >
                        {log.status || 'SUCCESS'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create User Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#18181E] border border-[#2A2A36] rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white">Create New System User</h3>
              <button onClick={() => setShowCreateModal(false)} className="text-gray-400 hover:text-white">
                ✕
              </button>
            </div>

            {formError && (
              <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-xl flex items-start space-x-2 text-xs text-red-400">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleCreateSubmit} className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-gray-300">Full Name</label>
                <input
                  type="text"
                  required
                  value={newUser.full_name}
                  onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })}
                  placeholder="e.g. Jane Doe"
                  className="w-full mt-1 bg-[#101014] border border-[#2E2E38] rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-[#F5A623]"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-gray-300">Username</label>
                <input
                  type="text"
                  required
                  value={newUser.username}
                  onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                  placeholder="e.g. jdoe"
                  className="w-full mt-1 bg-[#101014] border border-[#2E2E38] rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-[#F5A623]"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-gray-300">Email Address</label>
                <input
                  type="email"
                  required
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  placeholder="jdoe@telecom.com"
                  className="w-full mt-1 bg-[#101014] border border-[#2E2E38] rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-[#F5A623]"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-gray-300">Password (min 8 chars)</label>
                <input
                  type="password"
                  required
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  placeholder="••••••••••••"
                  className="w-full mt-1 bg-[#101014] border border-[#2E2E38] rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-[#F5A623]"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-gray-300">Assigned Role</label>
                <select
                  value={newUser.role}
                  onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                  className="w-full mt-1 bg-[#101014] border border-[#2E2E38] rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-[#F5A623]"
                >
                  {AVAILABLE_ROLES.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </div>

              <div className="pt-3 flex items-center justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3 py-2 bg-[#22222A] hover:bg-[#2A2A34] text-gray-300 rounded-xl text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createUserMutation.isPending}
                  className="px-4 py-2 bg-[#F5A623] hover:bg-[#E09612] text-black font-bold rounded-xl text-xs shadow-lg shadow-[#F5A623]/20 disabled:opacity-50"
                >
                  {createUserMutation.isPending ? 'Creating...' : 'Create User'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
