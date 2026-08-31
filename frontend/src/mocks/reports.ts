import { ReportItem } from '../types';

export const mockReportItems: ReportItem[] = [
  {
    id: 'rep-101',
    title: 'Executive Churn Overview Report',
    category: 'Executive',
    description: 'High-level executive summary of customer retention KPIs, churn probability trends, and revenue exposure.',
    last_generated: '2026-08-31 09:30 AM',
    file_format: 'PDF',
    size: '2.4 MB',
  },
  {
    id: 'rep-102',
    title: 'Retention Strategy Performance Audit',
    category: 'Retention',
    description: 'Detailed analysis of retention offer save rates, campaign ROI, and customer engagement per risk tier.',
    last_generated: '2026-08-30 05:15 PM',
    file_format: 'PDF',
    size: '3.8 MB',
  },
  {
    id: 'rep-103',
    title: 'ML Model Performance & Feature Drift Report',
    category: 'Model',
    description: 'Technical evaluation metrics (Precision, Recall, ROC-AUC) and feature drift diagnostics for Candidate_RandomForest.',
    last_generated: '2026-08-31 01:00 PM',
    file_format: 'CSV',
    size: '1.1 MB',
  },
  {
    id: 'rep-104',
    title: 'Customer Lifetime Value & ROI Financial Audit',
    category: 'ROI',
    description: 'Financial waterfall breakdown of retention investments vs expected gross and net saved revenue.',
    last_generated: '2026-08-29 11:45 AM',
    file_format: 'XLSX',
    size: '4.2 MB',
  },
  {
    id: 'rep-105',
    title: 'High-Risk Customer Target Roster',
    category: 'Risk',
    description: 'Complete exportable customer roster for subscribers with Churn Probability >= 70% and priority scores.',
    last_generated: '2026-08-31 02:20 PM',
    file_format: 'CSV',
    size: '850 KB',
  },
];
