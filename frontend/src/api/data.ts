import { fetchApi } from './client';
import { DataOverviewMetrics } from '../types';
import { mockDataOverviewMetrics } from '../mocks/data';

export const getDataOverview = async (): Promise<DataOverviewMetrics> => {
  return fetchApi<DataOverviewMetrics>(`/data/overview`, {}, mockDataOverviewMetrics);
};

export const triggerDataRefresh = async (): Promise<{ status: string; records_ingested: number; message: string }> => {
  return fetchApi<{ status: string; records_ingested: number; message: string }>(`/scoring-jobs`, {
    method: 'POST',
    body: JSON.stringify({ job_type: 'ingestion', force_ingestion: true }),
  }, {
    status: 'completed',
    records_ingested: 1500,
    message: 'Data ingestion and quality check completed successfully.',
  });
};
