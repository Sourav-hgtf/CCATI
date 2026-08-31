import { fetchApi } from './client';
import { ReportItem } from '../types';
import { mockReportItems } from '../mocks/reports';

export const getReports = async (): Promise<ReportItem[]> => {
  return fetchApi<ReportItem[]>(`/reports`, {}, mockReportItems);
};

export const generateReport = async (reportId: string): Promise<{ status: string; download_url: string; generated_at: string }> => {
  return fetchApi<{ status: string; download_url: string; generated_at: string }>(`/reports/${reportId}/generate`, {
    method: 'POST',
  }, {
    status: 'success',
    download_url: `/api/v1/export/customers`,
    generated_at: new Date().toISOString(),
  });
};
