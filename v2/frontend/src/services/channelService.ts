/**
 * Channel API service
 */
import apiClient from './apiClient';

/**
 * Channel model interface
 */
export interface Channel {
  id: string;
  name: string;
  last_seen: string;
  last_processed?: string;
  status: string;
  source_url?: string;
  scraped_url_id?: number;
  group?: string;
  logo?: string;
  tvg_id?: string;
  tvg_name?: string;
  m3u_source?: string;
  original_url?: string;
  is_online: boolean;
  last_checked?: string;
  check_error?: string;
  epg_update_protected: boolean;
  tv_channel_id?: number;
  is_active?: boolean; // Added for inline edit/quick actions
}

/**
 * Channel creation DTO
 */
export interface CreateChannelDTO {
  name: string;
  source_url?: string;
  group?: string;
  logo?: string;
  tvg_id?: string;
  tvg_name?: string;
  original_url?: string;
  epg_update_protected?: boolean;
  tv_channel_id?: number;
}

/**
 * Channel update DTO
 */
export interface UpdateChannelDTO {
  name?: string;
  source_url?: string;
  group?: string;
  logo?: string;
  tvg_id?: string;
  tvg_name?: string;
  original_url?: string;
  epg_update_protected?: boolean;
  tv_channel_id?: number;
  is_online?: boolean; // For online/offline status
  is_active?: boolean; // For activation/deactivation (matches backend)
}

/**
 * Channel filter parameters
 */
export interface ChannelFilters {
  search?: string;
  group?: string;
  is_active?: boolean;
  is_online?: boolean;
  id?: string; // Added for Acestream ID filter
  country?: string;
  language?: string;
  page?: number;
  page_size?: number;
  active_only?: boolean; // Added to support backend override
}

/**
 * Channel API service
 */
const channelService = {
  /**
   * Get all channels with optional filtering
   */
  getChannels: async (filters?: ChannelFilters): Promise<Channel[]> => {
    // Convert string values for is_online and is_active to booleans if present
    const params = { ...filters };
    if (typeof params.is_online === 'string') {
      params.is_online = params.is_online === 'true';
    }
    if (typeof params.is_active === 'string') {
      params.is_active = params.is_active === 'true';
    }
    // Only set active_only if is_active is explicitly true or false
    if (params.is_active === true || params.is_active === false) {
      params.active_only = false;
    } else {
      delete params.is_active;
      delete params.active_only;
    }
    const { data } = await apiClient.get('/v1/channels', { params });
    return data;
  },

  /**
   * Get a channel by ID
   */
  getChannel: async (id: string): Promise<Channel> => {
    const { data } = await apiClient.get(`/v1/channels/${id}`);
    return data;
  },

  /**
   * Create a new channel
   */
  createChannel: async (channelData: CreateChannelDTO): Promise<Channel> => {
    const { data } = await apiClient.post('/v1/channels', channelData);
    return data;
  },

  /**
   * Update a channel
   */
  updateChannel: async (id: string, channelData: UpdateChannelDTO): Promise<Channel> => {
    const { data } = await apiClient.put(`/v1/channels/${id}`, channelData);
    return data;
  },

  /**
   * Delete a channel
   */
  deleteChannel: async (id: string): Promise<void> => {
    await apiClient.delete(`/v1/channels/${id}`);
  },

  /**
   * Check channel status
   */
  checkChannelStatus: async (id: string): Promise<Channel> => {
    const { data } = await apiClient.post(`/v1/channels/${id}/check_status`);
    return data;
  },

  /**
   * Get all unique channel categories
   */
  getCategories: async () => {
    try {
      const { data: categories } = await apiClient.get('/v1/channels/categories');
      return categories as string[];
    } catch {
      const { data: channels } = await apiClient.get('/v1/channels');
      const categories = Array.from(new Set((channels || []).map((c: any) => String(c.category)).filter((v: string) => !!v)));
      return categories.map(String); // Ensure string[]
    }
  },

  /**
   * Get all unique channel groups
   */
  getGroups: async (): Promise<string[]> => {
    const { data } = await apiClient.get('/v1/channels/groups');
    return data;
  },

  /**
   * Bulk delete channels
   */
  bulkDeleteChannels: async (ids: string[]): Promise<void> => {
    await apiClient.post('/v1/channels/bulk_delete', { channel_ids: ids });
  },

  /**
   * Bulk edit channels
   */
  bulkEditChannels: async (ids: string[], fields: any): Promise<any[]> => {
    const { data } = await apiClient.put('/v1/channels/bulk_edit', { channel_ids: ids, fields });
    return data;
  },

  /**
   * Bulk activate/deactivate channels
   */
  bulkActivateChannels: async (ids: string[], active: boolean): Promise<any[]> => {
    const { data } = await apiClient.post('/v1/channels/bulk_activate', { channel_ids: ids, active });
    return data;
  },

  /**
   * Export all channels as CSV
   */
  exportChannelsCSV: async (): Promise<Blob> => {
    const response = await apiClient.get('/v1/channels/export_csv', { responseType: 'blob' });
    return response.data;
  },

  /**
   * Get activity log for a specific channel
   */
  getChannelActivityLog: async (
    channelId: string,
    params?: { days?: number; type?: string; page?: number; page_size?: number }
  ): Promise<any> => {
    const { data } = await apiClient.get(`/v1/activity/channels/${channelId}/activity_log`, { params });
    return data;
  },

  /**
   * Assign an Acestream channel to a TV channel
   */
  assignToTVChannel: async (acestreamChannelId: string, tvChannelId: number) => {
    return apiClient.post(`/tv-channels/${tvChannelId}/acestreams`, {
      acestream_channel_id: acestreamChannelId
    });
  },
};

export { channelService };
export default channelService;
