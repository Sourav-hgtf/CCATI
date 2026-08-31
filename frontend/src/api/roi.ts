import { fetchApi } from './client';
import { ROISimulationInputs, ROISimulationResults } from '../types';

export const simulateROI = async (inputs: ROISimulationInputs): Promise<ROISimulationResults> => {
  return fetchApi<ROISimulationResults>(`/roi/simulate`, {
    method: 'POST',
    body: JSON.stringify(inputs),
  });
};

export const getROIWaterfall = async (): Promise<any> => {
  return fetchApi<any>(`/roi/waterfall`);
};
