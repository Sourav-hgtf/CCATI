import { fetchApi } from './client';
import { DataOverviewMetrics } from '../types';

export const getDataOverview = async (): Promise<DataOverviewMetrics> => {
  return fetchApi<DataOverviewMetrics>(`/data/overview`);
};

export const triggerDataRefresh = async (): Promise<{ status: string; records_ingested: number; message: string }> => {
  return fetchApi<{ status: string; records_ingested: number; message: string }>(`/scoring-jobs`, {
    method: 'POST',
    body: JSON.stringify({ job_type: 'ingestion', force_ingestion: true }),
  });
};
