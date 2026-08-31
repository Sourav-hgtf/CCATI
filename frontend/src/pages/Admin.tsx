import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '../lib/apiClient';
import { Shield, ShieldAlert, History, Users } from 'lucide-react';

interface AuditLogItem {
  id: number;
  timestamp: string;
  actor_email: string;
  actor_role: string;
  action: string;
  target_resource: string;
  details: string;
}

interface AuditResponse {
  total: number;
  logs: AuditLogItem[];
}

export const Admin: React.FC = () => {
  const { data: auditData, isLoading } = useQuery<AuditResponse>({
    queryKey: ['admin-audit-logs'],
    queryFn: () => fetchApi<AuditResponse>('/admin/audit-logs'),
  });

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">System Admin & Audit Logs</h1>
        <p className="text-sm text-gray-400 mt-1">User role assignments, security audit trail, and system permissions.</p>
      </div>

      {/* Security Audit Log Table */}
      <div className="bg-surface border border-border rounded-xl p-6 shadow-lg space-y-4">
        <div className="flex items-center space-x-2">
          <History className="w-5 h-5 text-blue-400" />
          <h2 className="text-lg font-bold text-white">Security Audit Log Trail (PII Reveals, Exports, Model Promotions)</h2>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-gray-400">Loading audit logs...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-300">
              <thead className="bg-background text-gray-400 uppercase text-xs">
                <tr>
                  <th className="p-3">Log ID</th>
                  <th className="p-3">Timestamp</th>
                  <th className="p-3">Actor Email</th>
                  <th className="p-3">Role</th>
                  <th className="p-3">Action</th>
                  <th className="p-3">Target Resource</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {auditData?.logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-800/50">
                    <td className="p-3 font-mono text-xs text-gray-400">#{log.id}</td>
                    <td className="p-3 font-mono text-xs">{new Date(log.timestamp).toLocaleString()}</td>
                    <td className="p-3 text-blue-400 font-medium">{log.actor_email}</td>
                    <td className="p-3 font-semibold">{log.actor_role}</td>
                    <td className="p-3">
                      <span className="px-2 py-1 rounded bg-blue-500/20 text-blue-300 font-mono text-xs border border-blue-500/30">
                        {log.action}
                      </span>
                    </td>
                    <td className="p-3 font-mono text-xs text-gray-400">{log.target_resource}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
