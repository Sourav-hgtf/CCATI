import React from 'react';
import { Navigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { ShieldAlert, ArrowLeft, Lock } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactElement;
  allowedRoles?: string[];
  requiredPermission?: string;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  allowedRoles,
  requiredPermission,
}) => {
  const { isAuthenticated, isLoading, user, hasRole, hasPermission } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-4">
        <div className="w-10 h-10 border-4 border-[#F5A623] border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs text-gray-400 font-mono tracking-wider">VERIFYING AUTHENTICATION SESSION...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Role validation
  if (allowedRoles && !hasRole(allowedRoles)) {
    return (
      <div className="p-8 max-w-2xl mx-auto my-12">
        <div className="bg-[#1C1C24] border border-red-500/30 rounded-xl p-8 text-center space-y-6 shadow-2xl">
          <div className="w-16 h-16 bg-red-500/10 border border-red-500/30 rounded-2xl flex items-center justify-center mx-auto text-red-400">
            <ShieldAlert className="w-8 h-8" />
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl font-bold text-white tracking-tight">403 — Access Denied</h2>
            <p className="text-sm text-gray-400">
              Your assigned role <span className="px-2 py-0.5 bg-red-500/20 text-red-300 font-mono rounded text-xs border border-red-500/30">{user?.role}</span> lacks authorization to access this workspace.
            </p>
          </div>

          <div className="bg-black/40 border border-border rounded-lg p-4 text-left text-xs space-y-2 font-mono text-gray-400">
            <div className="flex items-center justify-between">
              <span>Required Role:</span>
              <span className="text-primary font-semibold">{allowedRoles.join(', ')}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Current User:</span>
              <span className="text-white">{user?.email}</span>
            </div>
          </div>

          <div className="pt-2">
            <Link
              to="/"
              className="inline-flex items-center space-x-2 px-5 py-2.5 bg-primary text-black font-semibold rounded-lg hover:bg-primary/90 transition text-xs"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Return to Overview</span>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Permission validation
  if (requiredPermission && !hasPermission(requiredPermission)) {
    return (
      <div className="p-8 max-w-2xl mx-auto my-12">
        <div className="bg-[#1C1C24] border border-amber-500/30 rounded-xl p-8 text-center space-y-6 shadow-2xl">
          <div className="w-16 h-16 bg-amber-500/10 border border-amber-500/30 rounded-2xl flex items-center justify-center mx-auto text-amber-400">
            <Lock className="w-8 h-8" />
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl font-bold text-white tracking-tight">Missing Required Permission</h2>
            <p className="text-sm text-gray-400">
              This action requires permission <span className="px-2 py-0.5 bg-amber-500/20 text-amber-300 font-mono rounded text-xs border border-amber-500/30">{requiredPermission}</span>.
            </p>
          </div>

          <div className="pt-2">
            <Link
              to="/"
              className="inline-flex items-center space-x-2 px-5 py-2.5 bg-primary text-black font-semibold rounded-lg hover:bg-primary/90 transition text-xs"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Return to Overview</span>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return children;
};
