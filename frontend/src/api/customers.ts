import { fetchApi } from './client';
import { CustomerPaginatedResponse, CustomerDetailResponse } from '../types';

export const getCustomers = async (params: {
  page?: number;
  page_size?: number;
  risk_tier?: string;
  plan_tier?: string;
  segment_id?: number;
  search?: string;
  sort_by?: string;
  sort_order?: string;
}): Promise<CustomerPaginatedResponse> => {
  const query = new URLSearchParams();
  if (params.page) query.append('page', params.page.toString());
  if (params.page_size) query.append('page_size', params.page_size.toString());
  if (params.risk_tier && params.risk_tier !== 'All') query.append('risk_tier', params.risk_tier);
  if (params.plan_tier) query.append('plan_tier', params.plan_tier);
  if (params.segment_id !== undefined) query.append('segment_id', params.segment_id.toString());
  if (params.search) query.append('search', params.search);
  if (params.sort_by) query.append('sort_by', params.sort_by);
  if (params.sort_order) query.append('sort_order', params.sort_order);

  return fetchApi<CustomerPaginatedResponse>(`/customers?${query.toString()}`);
};

export const getCustomerDetail = async (customerId: string, revealPii: boolean = false): Promise<CustomerDetailResponse> => {
  const query = revealPii ? '?reveal_pii=true' : '';
  return fetchApi<CustomerDetailResponse>(`/customers/${customerId}${query}`);
};

export const markCustomerActioned = async (customerId: string): Promise<{ status: string; customer_id: string; actioned_at: string }> => {
  return fetchApi<{ status: string; customer_id: string; actioned_at: string }>(`/customers/${customerId}/action`, {
    method: 'POST',
  });
};
