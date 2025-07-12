import React, { useState, useCallback, useEffect } from 'react';
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
import BatchAssignDialog from '../components/BatchAssignDialog';
import QuickEditDialog from '../components/QuickEditDialog';

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
  const [batchAssignOpen, setBatchAssignOpen] = useState(false);
  const [quickEditOpen, setQuickEditOpen] = useState(false);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [quickEditChannel, setQuickEditChannel] = useState<any>(null);

  // State for categories/groups
  const [categories, setCategories] = useState<string[]>([]);
  const [groups, setGroups] = useState<string[]>([]);
  const [catGroupLoading, setCatGroupLoading] = useState(false);
  const [catGroupError, setCatGroupError] = useState<string|null>(null);

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
    // Convert string values to booleans for is_active and is_online
    const newFilters: ChannelFilters = { ...filters };
    if (adv.is_active !== undefined) {
      if (adv.is_active === '') newFilters.is_active = undefined;
      else newFilters.is_active = adv.is_active === 'true';
    }
    if (adv.is_online !== undefined) {
      if (adv.is_online === '') newFilters.is_online = undefined;
      else newFilters.is_online = adv.is_online === 'true';
    }
    if (adv.country !== undefined) newFilters.country = adv.country;
    if (adv.language !== undefined) newFilters.language = adv.language;
    if (adv.group !== undefined) newFilters.group = adv.group;
    if (adv.search !== undefined) newFilters.search = adv.search;
    setFilters(newFilters);
    setPage(0);
  };

  // Convert ChannelFilters to AdvancedSearchFilters for UI
  const filtersForAdvancedSearch: AdvancedSearchFilters = {
    ...filters,
    is_active: typeof filters.is_active === 'boolean' ? String(filters.is_active) : '',
    is_online: typeof filters.is_online === 'boolean' ? String(filters.is_online) : '',
  };

  // Bulk action handlers
  const handleBulkEdit = async (updates: any) => {
    await channelService.bulkEditChannels(selectedIds, updates);
    refetch();
  };
  const handleBulkDelete = async () => {
    await channelService.bulkDeleteChannels(selectedIds);
    refetch();
  };
  const handleBulkActivate = async (active: boolean) => {
    await channelService.bulkActivateChannels(selectedIds, active);
    refetch();
  };
  // Handler for batch assign
  const handleBatchAssign = async (group: string) => {
    await channelService.bulkEditChannels(selectedIds, { group });
    refetch();
  };

  // Handler for CSV export
  const handleExportCSV = async () => {
    try {
      const blob = await channelService.exportChannelsCSV();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'channels.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to export CSV: ' + getErrorMessage(err));
    }
  };

  // Fetch categories and groups on mount
  useEffect(() => {
    setCatGroupLoading(true);
    setCatGroupError(null);
    Promise.all([
      channelService.getCategories?.() ?? Promise.resolve([]),
      channelService.getGroups?.() ?? Promise.resolve([])
    ])
      .then(([cats, grps]) => {
        setCategories(cats || []);
        setGroups(grps || []);
      })
      .catch((err) => {
        setCatGroupError(getErrorMessage(err));
      })
      .finally(() => setCatGroupLoading(false));
  }, []);

  // Handler for quick edit
  const handleQuickEdit = (channel: any) => {
    setQuickEditChannel(channel);
    setQuickEditOpen(true);
  };
  const handleQuickEditSave = async (updates: any) => {
    await channelService.updateChannel(quickEditChannel.id, updates);
    setQuickEditOpen(false);
    setQuickEditChannel(null);
    refetch();
  };

  // Handler for add channel
  const handleAddChannel = () => {
    setQuickEditChannel({
      name: '',
      group: '',
      logo: '',
      is_active: true
    });
    setAddDialogOpen(true);
  };
  const handleAddChannelSave = async (values: any) => {
    await channelService.createChannel(values);
    setAddDialogOpen(false);
    setQuickEditChannel(null);
    refetch();
  };

  return (
    <Box sx={{ width: '100%' }}>
      <>
        <Box sx={{ mb: 3, display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, justifyContent: 'space-between', alignItems: { xs: 'stretch', sm: 'center' }, gap: 2 }}>
          <Typography variant="h4" component="h1" sx={{ mb: { xs: 2, sm: 0 } }}>
            Channels
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: 1, width: { xs: '100%', sm: 'auto' } }}>
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={() => refetch()}
              fullWidth={true}
              sx={{ minWidth: 120 }}
            >
              Refresh
            </Button>
            <Button
              variant="outlined"
              onClick={handleExportCSV}
              fullWidth={true}
              sx={{ minWidth: 120 }}
            >
              Download CSV
            </Button>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={handleAddChannel}
              fullWidth={true}
              sx={{ minWidth: 120 }}
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

        {catGroupError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to load categories/groups: {catGroupError}
          </Alert>
        )}

        <AdvancedSearch
          filters={filtersForAdvancedSearch}
          onChange={handleAdvancedSearch}
          categories={categories}
          groups={groups}
        />
        <Paper sx={{ p: { xs: 1, sm: 2 }, width: '100%', overflowX: 'auto' }}>
          {selectedIds.length > 0 && (
            <Box mb={2} display="flex" flexDirection={{ xs: 'column', sm: 'row' }} justifyContent="flex-end" gap={1}>
              <Button variant="contained" color="secondary" onClick={() => setBulkOpen(true)} fullWidth={true} sx={{ minWidth: 120 }}>
                Bulk Actions ({selectedIds.length})
              </Button>
              <Button variant="outlined" color="primary" onClick={() => setBatchAssignOpen(true)} fullWidth={true} sx={{ minWidth: 120 }}>
                Batch Assign Group
              </Button>
            </Box>
          )}
          <Box sx={{ width: '100%', overflowX: 'auto' }}>
            <ChannelTable
              channels={channels || []}
              loading={isLoading}
              onCheckStatus={handleCheckStatus}
              onEdit={handleQuickEdit}
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
          </Box>
        </Paper>
        <BulkOperations
          open={bulkOpen}
          onClose={() => setBulkOpen(false)}
          selectedChannels={channels.filter((c: any) => selectedIds.includes(c.id))}
          onBulkEdit={handleBulkEdit}
          onBulkDelete={handleBulkDelete}
          onBulkActivate={handleBulkActivate}
        />
        <BatchAssignDialog
          open={batchAssignOpen}
          onClose={() => setBatchAssignOpen(false)}
          selectedChannels={channels.filter((c: any) => selectedIds.includes(c.id))}
          groups={groups}
          onAssign={handleBatchAssign}
        />
        <QuickEditDialog
          open={quickEditOpen}
          onClose={() => setQuickEditOpen(false)}
          channel={quickEditChannel}
          onSave={handleQuickEditSave}
          fullScreen={window.innerWidth < 600}
        />
        <QuickEditDialog
          open={addDialogOpen}
          onClose={() => setAddDialogOpen(false)}
          channel={quickEditChannel}
          onSave={handleAddChannelSave}
          fullScreen={window.innerWidth < 600}
        />
      </>
    </Box>
  );
};

export default Channels;
