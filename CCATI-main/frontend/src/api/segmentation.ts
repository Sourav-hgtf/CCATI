import { fetchApi } from './client';
import { SegmentOverviewResponse } from '../types';

export const getSegmentsOverview = async (): Promise<SegmentOverviewResponse> => {
  return fetchApi<SegmentOverviewResponse>(`/segments`);
};
