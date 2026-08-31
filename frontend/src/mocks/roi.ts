import { ROISimulationInputs, ROISimulationResults } from '../types';

export const calculateROISimulation = (inputs: ROISimulationInputs): ROISimulationResults => {
  const total_offer_cost = inputs.target_customers * inputs.offer_cost_per_customer;
  const total_investment = total_offer_cost + inputs.campaign_cost;
  
  const expected_saves = Math.round(inputs.target_customers * inputs.expected_success_rate);
  const expected_revenue_saved = expected_saves * (inputs.avg_customer_clv * 0.4); // 40% of CLV retained
  const net_benefit = expected_revenue_saved - total_investment;
  
  const roi_ratio = total_investment > 0 ? Number((expected_revenue_saved / total_investment).toFixed(2)) : 0;
  const roi_pct = total_investment > 0 ? Number(((net_benefit / total_investment) * 100).toFixed(1)) : 0;

  return {
    total_investment,
    expected_saves,
    expected_revenue_saved,
    net_benefit,
    roi_ratio,
    roi_pct,
  };
};

export const mockROIWaterfallData = [
  { stage: 'Campaign Cost', amount: -50000, type: 'cost' },
  { stage: 'Retention Offers', amount: -150000, type: 'cost' },
  { stage: 'Total Investment', amount: -200000, type: 'subtotal' },
  { stage: 'Gross Revenue Saved', amount: 760000, type: 'revenue' },
  { stage: 'Net Retained Value', amount: 560000, type: 'net' },
];
