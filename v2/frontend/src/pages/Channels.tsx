import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Typography, Box, Button, Alert, Paper } from '@mui/material';
import { Add, Refresh } from '@mui/icons-material';
import { GridSortModel } from '@mui/x-data-grid';
import ChannelTable from '../components/ChannelTable';
import { useChannels, useCheckChannelStatus, useDeleteChannel } from '../hooks/useChannels';
import { ChannelFilters, channelService } from '../services/channelService';
import { getErrorMessage } from '../utils/errorUtils';
import BulkOperations from '../components/BulkOperations';
import AdvancedSearch, { AdvancedSearchFilters } from '../components/AdvancedSearch';

/**
 * Channels page component
 */
const Channels: React.FC = () => {
  // State for pagination and sorting
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [sortModel, setSortModel] = useState<GridSortModel>([]);
  const [filters, setFilters] = useState<ChannelFilters>({});
  const [checkingStatus, setCheckingStatus] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [bulkOpen, setBulkOpen] = useState(false);

  // Queries and mutations
  const {
    data: channels = [],
    isLoading,
    refetch,
    error: fetchError
  } = useChannels({
    ...filters,
    page: page + 1, // Backend uses 1-based indexing
    page_size: pageSize
  });

  const deleteChannel = useDeleteChannel();

  // Handler for check status
  const handleCheckStatus = useCallback((id: string) => {
    setCheckingStatus(prev => ({ ...prev, [id]: true }));

    channelService.checkChannelStatus(id)
      .then(() => {
        setCheckingStatus(prev => ({ ...prev, [id]: false }));
        // Refetch channels to get updated status
        refetch();
      })
      .catch((err: any) => {
        setCheckingStatus(prev => ({ ...prev, [id]: false }));
        setError(`Failed to check status: ${getErrorMessage(err)}`);
      });
  }, []);

  // Handler for editing a channel
  const navigate = useNavigate();

  const handleEdit = useCallback((channel: any) => {
    navigate(`/channels/${channel.id}`);
  }, [navigate]);

  // Handler for deleting a channel
  const handleDelete = useCallback((id: string) => {
    if (window.confirm('Are you sure you want to delete this channel?')) {
      deleteChannel.mutate(id, {
        onError: (err) => {
          setError(`Failed to delete channel: ${getErrorMessage(err)}`);
        }
      });
    }
  }, [deleteChannel]);

  // Handler for filter changes
  const handleFilterChange = useCallback((newFilters: ChannelFilters) => {
    setFilters(newFilters);
    setPage(0); // Reset to first page on filter change
  }, []);

  // Handler for sort changes
  const handleSortChange = useCallback((model: GridSortModel) => {
    setSortModel(model);
    // Implement server-side sorting logic here
  }, []);

  // Handler for advanced search/filter changes
  const handleAdvancedSearch = (adv: AdvancedSearchFilters) => {
    setFilters({ ...filters, ...adv });
    setPage(0);
  };

  // Bulk action handlers (stubbed for now)
  const handleBulkEdit = async (updates: any) => {
    await Promise.all(selectedIds.map(id => channelService.updateChannel(id, updates)));
    refetch();
  };
  const handleBulkDelete = async () => {
    await Promise.all(selectedIds.map(id => channelService.deleteChannel(id)));
    refetch();
  };
  const handleBulkActivate = async (active: boolean) => {
    await Promise.all(selectedIds.map(id => channelService.updateChannel(id, { is_active: active })));
    refetch();
  };

  return (
    <Box sx={{ width: '100%' }}>
      <>
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h4" component="h1">
            Channels
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={() => refetch()}
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => {/* To be implemented - open add channel dialog */}}
            >
              Add Channel
            </Button>
          </Box>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {fetchError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {typeof fetchError === 'string' ? fetchError : getErrorMessage(fetchError)}
          </Alert>
        )}

        <AdvancedSearch
          filters={filters}
          onChange={handleAdvancedSearch}
          categories={[]} // TODO: fetch categories from API or state
          groups={[]}     // TODO: fetch groups from API or state
        />
        <Paper sx={{ p: 2 }}>
          {selectedIds.length > 0 && (
            <Box mb={2} display="flex" justifyContent="flex-end">
              <Button variant="contained" color="secondary" onClick={() => setBulkOpen(true)}>
                Bulk Actions ({selectedIds.length})
              </Button>
            </Box>
          )}
          <ChannelTable
            channels={channels || []}
            loading={isLoading}
            onCheckStatus={handleCheckStatus}
            onEdit={handleEdit}
            onDelete={handleDelete}
            checkingStatus={checkingStatus}
            filters={filters}
            onFilterChange={handleFilterChange}
            totalCount={100} // This should come from API
            page={page}
            pageSize={pageSize}
            onPageChange={setPage}
            onPageSizeChange={setPageSize}
            onSortChange={handleSortChange}
            onSelectionChange={setSelectedIds}
          />
        </Paper>
        <BulkOperations
          open={bulkOpen}
          onClose={() => setBulkOpen(false)}
          selectedChannels={channels.filter((c: any) => selectedIds.includes(c.id))}
          onBulkEdit={handleBulkEdit}
          onBulkDelete={handleBulkDelete}
          onBulkActivate={handleBulkActivate}
        />
      </>
    </Box>
  );
};

export default Channels;
