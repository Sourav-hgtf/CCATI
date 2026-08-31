import { fetchApi } from './client';
import { ReportItem } from '../types';

export const getReports = async (): Promise<ReportItem[]> => {
  return fetchApi<ReportItem[]>(`/reports`);
};

export const generateReport = async (reportId: string): Promise<{ status: string; download_url: string; generated_at: string }> => {
  return fetchApi<{ status: string; download_url: string; generated_at: string }>(`/reports/${reportId}/generate`, {
    method: 'POST',
  });
};
