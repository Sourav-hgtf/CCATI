import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HeaderNav } from './components/layout/HeaderNav';
import { Overview } from './pages/Overview';
import { Customers } from './pages/Customers';
import { CustomerDetail } from './pages/CustomerDetail';
import { ChurnAnalytics } from './pages/ChurnAnalytics';
import { Predictions } from './pages/Predictions';
import { Explainability } from './pages/Explainability';
import { Retention } from './pages/Retention';
import { Segments } from './pages/Segments';
import { ROI } from './pages/ROI';
import { ModelMonitoring } from './pages/ModelMonitoring';
import { DataManagement } from './pages/DataManagement';
import { Reports } from './pages/Reports';
import { Settings } from './pages/Settings';
import { Admin } from './pages/Admin';

const queryClient = new QueryClient();

export const App: React.FC = () => {
  const [currentRole] = useState<string>('Admin');

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-background text-gray-100 flex flex-col font-sans selection:bg-[#F5A623] selection:text-black">
          {/* Reference Design Shell: Top Compact Pill Header Navigation */}
          <HeaderNav />

          {/* Main Workspace Container */}
          <main className="flex-1 overflow-y-auto">
            <Routes>
              <Route path="/" element={<Overview />} />
              <Route path="/customers" element={<Customers currentRole={currentRole} />} />
              <Route path="/customers/:id" element={<CustomerDetail currentRole={currentRole} />} />
              <Route path="/churn-analytics" element={<ChurnAnalytics />} />
              <Route path="/predictions" element={<Predictions />} />
              <Route path="/explainability" element={<Explainability />} />
              <Route path="/segmentation" element={<Segments />} />
              <Route path="/retention" element={<Retention />} />
              <Route path="/roi" element={<ROI />} />
              <Route path="/data" element={<DataManagement />} />
              <Route path="/monitoring" element={<ModelMonitoring currentRole={currentRole} />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/admin" element={<Admin />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </Router>
    </QueryClientProvider>
  );
};
