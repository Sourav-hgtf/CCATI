import { fetchApi } from './client';

export interface RetentionStrategyGroup {
  risk_tier: 'Critical' | 'High' | 'Medium' | 'Low';
  customer_count: number;
  revenue_at_risk: number;
  recommended_action: string;
  action_code: string;
  estimated_cost: number;
  expected_saves: number;
  expected_roi: string;
  description: string;
}

export const getRetentionStrategies = async (): Promise<RetentionStrategyGroup[]> => {
  return fetchApi<RetentionStrategyGroup[]>(`/retention/recommendations`, {}, [
    {
      risk_tier: 'Critical',
      customer_count: 693,
      revenue_at_risk: 68937,
      recommended_action: '20% Loyalty Bill Discount + VIP Outreach',
      action_code: 'DISCOUNT_20_VIP',
      estimated_cost: 10395,
      expected_saves: 381,
      expected_roi: '2230%',
      description: 'Immediate call center priority outreach with a 20% bill credit for 6 months.',
    },
    {
      risk_tier: 'High',
      customer_count: 1250,
      revenue_at_risk: 88000,
      recommended_action: 'Free Plan Upgrade & Router Tech Check',
      action_code: 'PLAN_UPGRADE_TECH',
      estimated_cost: 12500,
      expected_saves: 560,
      expected_roi: '1850%',
      description: 'Complimentary high-speed data tier boost for 3 billing cycles.',
    },
    {
      risk_tier: 'Medium',
      customer_count: 1240,
      revenue_at_risk: 62000,
      recommended_action: 'Proactive Service Quality Review',
      action_code: 'SERVICE_QUALITY_CHECK',
      estimated_cost: 3720,
      expected_saves: 372,
      expected_roi: '1420%',
      description: 'Automated network health diagnostic with usage optimization tips.',
    },
    {
      risk_tier: 'Low',
      customer_count: 1749,
      revenue_at_risk: 35000,
      recommended_action: 'Contract Renewal Loyalty Bonus',
      action_code: 'LOYALTY_BONUS_RENEW',
      estimated_cost: 1749,
      expected_saves: 262,
      expected_roi: '950%',
      description: 'Annual contract extension invitation with 500 bonus reward points.',
    },
  ]);
};
