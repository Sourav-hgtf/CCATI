import { fetchApi } from './client';
import { ROISimulationInputs, ROISimulationResults } from '../types';
import { calculateROISimulation, mockROIWaterfallData } from '../mocks/roi';

export const simulateROI = async (inputs: ROISimulationInputs): Promise<ROISimulationResults> => {
  return fetchApi<ROISimulationResults>(`/roi/simulate`, {
    method: 'POST',
    body: JSON.stringify(inputs),
  }, calculateROISimulation(inputs));
};

export const getROIWaterfall = async (): Promise<typeof mockROIWaterfallData> => {
  return fetchApi<typeof mockROIWaterfallData>(`/roi/waterfall`, {}, mockROIWaterfallData);
};
