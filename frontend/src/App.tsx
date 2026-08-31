import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { HeaderNav } from './components/layout/HeaderNav';
import { Login } from './pages/Login';
import { Overview } from './pages/Overview';
import { Customers } from './pages/Customers';
import { CustomerDetail } from './pages/CustomerDetail';
import { ChurnAnalytics } from './pages/ChurnAnalytics';
import { Predictions } from './pages/Predictions';
import { PredictionHistoryPage } from './pages/PredictionHistory';
import { Explainability } from './pages/Explainability';
import { Retention } from './pages/Retention';
import { Segments } from './pages/Segments';
import { ROI } from './pages/ROI';
import { ModelMonitoring } from './pages/ModelMonitoring';
import { DataManagement } from './pages/DataManagement';
import { Reports } from './pages/Reports';
import { Settings } from './pages/Settings';
import { Admin } from './pages/Admin';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const AppRoutes: React.FC = () => {
  const { role } = useAuth();

  return (
    <div className="min-h-screen bg-background text-gray-100 flex flex-col font-sans selection:bg-[#F5A623] selection:text-black">
      {/* Top Header Navigation (renders only when authenticated) */}
      <HeaderNav />

      {/* Main Workspace Container */}
      <main className="flex-1 overflow-y-auto">
        <Routes>
          {/* Public Login Route */}
          <Route path="/login" element={<Login />} />

          {/* Protected Business Routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Overview />
              </ProtectedRoute>
            }
          />
          <Route
            path="/customers"
            element={
              <ProtectedRoute>
                <Customers currentRole={role} />
              </ProtectedRoute>
            }
          />
          <Route
            path="/customers/:id"
            element={
              <ProtectedRoute>
                <CustomerDetail currentRole={role} />
              </ProtectedRoute>
            }
          />
          <Route
            path="/churn-analytics"
            element={
              <ProtectedRoute>
                <ChurnAnalytics />
              </ProtectedRoute>
            }
          />
          <Route
            path="/predictions"
            element={
              <ProtectedRoute>
                <Predictions />
              </ProtectedRoute>
            }
          />
          <Route
            path="/history"
            element={
              <ProtectedRoute>
                <PredictionHistoryPage currentRole={role} />
              </ProtectedRoute>
            }
          />
          <Route
            path="/explainability"
            element={
              <ProtectedRoute>
                <Explainability />
              </ProtectedRoute>
            }
          />
          <Route
            path="/segmentation"
            element={
              <ProtectedRoute>
                <Segments />
              </ProtectedRoute>
            }
          />
          <Route
            path="/retention"
            element={
              <ProtectedRoute>
                <Retention />
              </ProtectedRoute>
            }
          />
          <Route
            path="/roi"
            element={
              <ProtectedRoute>
                <ROI />
              </ProtectedRoute>
            }
          />
          <Route
            path="/data"
            element={
              <ProtectedRoute>
                <DataManagement />
              </ProtectedRoute>
            }
          />
          <Route
            path="/monitoring"
            element={
              <ProtectedRoute>
                <ModelMonitoring currentRole={role} />
              </ProtectedRoute>
            }
          />
          <Route
            path="/reports"
            element={
              <ProtectedRoute>
                <Reports />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <Settings />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <ProtectedRoute allowedRoles={['Admin']}>
                <Admin />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </Router>
    </QueryClientProvider>
  );
};
