import { useMutation, useQuery, UseQueryOptions } from 'react-query';
import { 
  searchService, 
  SearchResponse, 
  AddChannelRequest, 
  AddChannelResponse, 
  AddMultipleResponse 
} from '../services/searchService';

export const useSearch = (
  query: string = '', 
  page: number = 1, 
  pageSize: number = 10,
  category?: string,
  options?: UseQueryOptions<SearchResponse>
) => {
  return useQuery<SearchResponse>(
    ['search', query, page, pageSize, category],
    () => searchService.search(query, page, pageSize, category),
    {
      keepPreviousData: true,
      ...options
    }
  );
};

export const useAddChannel = () => {
  return useMutation<AddChannelResponse, Error, AddChannelRequest>(
    (channel: AddChannelRequest) => searchService.addChannel(channel)
  );
};

export const useAddMultipleChannels = () => {
  return useMutation<AddMultipleResponse, Error, AddChannelRequest[]>(
    (channels: AddChannelRequest[]) => searchService.addMultipleChannels(channels)
  );
};
