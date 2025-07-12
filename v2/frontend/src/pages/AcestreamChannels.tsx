// AcestreamChannels.tsx
// Page for managing Acestream channels independently
// ...existing code from Channels.tsx will be adapted here...

import React, { useState, useCallback, useEffect } from 'react';
import { Typography, Box, Button, Alert, Paper, AppBar, Toolbar, Link, useTheme, useMediaQuery, Tooltip, IconButton } from '@mui/material';
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
import AssignTVChannelDialog from '../components/AssignTVChannelDialog';
import { useAllTVChannels, PaginatedTVChannels } from '../hooks/useTVChannels';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import TvIcon from '@mui/icons-material/Tv';

// Helper type guard for paginated response
function isPaginatedChannels(obj: any): obj is { items: any[]; total: number } {
  return obj && typeof obj === 'object' && Array.isArray(obj.items) && typeof obj.total === 'number';
}

// AcestreamChannels page: manages only Acestream channels
const AcestreamChannels: React.FC = () => {
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
  const [assignDialogOpen, setAssignDialogOpen] = useState(false);
  const [assignTargetIds, setAssignTargetIds] = useState<string[]>([]);
  const [assigning, setAssigning] = useState(false);
  const [assignError, setAssignError] = useState<string|null>(null);
  const [quickEditChannel, setQuickEditChannel] = useState<any>(null);
  const [groups, setGroups] = useState<string[]>([]);
  const [catGroupLoading, setCatGroupLoading] = useState(false);
  const [catGroupError, setCatGroupError] = useState<string|null>(null);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const navigate = useNavigate();

  // Queries and mutations (Acestream channels only)
  const {
    data: channelsRaw = [],
    isLoading,
    refetch,
    error: fetchError
  } = useChannels({
    ...filters,
    page: page + 1,
    page_size: pageSize
  });
  const channels = isPaginatedChannels(channelsRaw) ? channelsRaw.items : Array.isArray(channelsRaw) ? channelsRaw : [];
  const totalCount = isPaginatedChannels(channelsRaw) ? channelsRaw.total : Array.isArray(channelsRaw) ? channelsRaw.length : 0;

  const deleteChannel = useDeleteChannel();

  // Fetch TV channels for assignment
  const { data: tvChannels } = useAllTVChannels(0, 100);

  // Handler for check status
  const handleCheckStatus = useCallback((id: string) => {
    setCheckingStatus(prev => ({ ...prev, [id]: true }));
    channelService.checkChannelStatus(id)
      .then(() => {
        setCheckingStatus(prev => ({ ...prev, [id]: false }));
        refetch();
      })
      .catch((err: any) => {
        setCheckingStatus(prev => ({ ...prev, [id]: false }));
        setError(`Failed to check status: ${getErrorMessage(err)}`);
      });
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

  // Handler to open assign dialog for single or multiple channels
  const handleOpenAssignDialog = (ids: string[]) => {
    setAssignTargetIds(ids);
    setAssignDialogOpen(true);
  };
  const handleCloseAssignDialog = () => {
    setAssignDialogOpen(false);
    setAssignTargetIds([]);
    setAssignError(null);
  };
  // Handler to assign selected Acestream channel(s) to a TV channel
  const handleAssignTVChannel = async (tvChannelId: number) => {
    setAssigning(true);
    setAssignError(null);
    try {
      // For each acestream channel, call backend assignment endpoint
      await Promise.all(assignTargetIds.map(id => channelService.assignToTVChannel(id, tvChannelId)));
      // Fetch the assigned TV channel info
      const tv = (tvChannels?.items || []).find((t: any) => t.id === tvChannelId);
      if (tv) {
        // For each acestream, update its fields with TV channel info (tvg_id, tvg_name, group, logo, etc.)
        await Promise.all(assignTargetIds.map(id => channelService.updateChannel(id, {
          tvg_id: tv.epg_id || '',
          tvg_name: tv.name,
          group: tv.category || '',
          logo: tv.logo_url || '',
          // Add more fields as needed
        })));
      }
      setAssignDialogOpen(false);
      setAssignTargetIds([]);
      refetch();
    } catch (err) {
      setAssignError(getErrorMessage(err));
    } finally {
      setAssigning(false);
    }
  };

  // Handler for filter changes
  const handleFilterChange = useCallback((newFilters: ChannelFilters) => {
    setFilters(newFilters);
    setPage(0);
  }, []);

  // Handler for sort changes
  const handleSortChange = useCallback((model: GridSortModel) => {
    setSortModel(model);
  }, []);

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
  // Handler for batch assign (group)
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
      a.download = 'acestream_channels.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to export CSV: ' + getErrorMessage(err));
    }
  };

  // Fetch groups on mount
  useEffect(() => {
    setCatGroupLoading(true);
    setCatGroupError(null);
    channelService.getGroups?.()
      .then((grps) => {
        setGroups(grps || []);
      })
      .catch((err) => {
        setCatGroupError(getErrorMessage(err));
      })
      .finally(() => setCatGroupLoading(false));
  }, []);

  return (
    <Box sx={{ width: '100%' }}>
      {/* Removed AppBar/Toolbar navigation buttons, now handled by NavBar */}
      <>
        <Box sx={{ mb: 3, display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, justifyContent: 'space-between', alignItems: { xs: 'stretch', sm: 'center' }, gap: 2 }}>
          <Typography variant="h4" component="h1" sx={{ mb: { xs: 2, sm: 0 } }}>
            Acestream Channels
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
              Add Acestream
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
            Failed to load groups: {catGroupError}
          </Alert>
        )}

        {/* Removed AdvancedSearch, all filtering is now in the table */}
        <Paper sx={{ p: { xs: 1, sm: 2 }, width: '100%', overflowX: 'auto' }}>
          {selectedIds.length > 0 && (
            <Box mb={2} display="flex" flexDirection={{ xs: 'column', sm: 'row' }} justifyContent="flex-end" gap={1}>
              <Button variant="contained" color="secondary" onClick={() => setBulkOpen(true)} fullWidth={true} sx={{ minWidth: 120 }}>
                Bulk Actions ({selectedIds.length})
              </Button>
              <Button variant="outlined" color="primary" onClick={() => setBatchAssignOpen(true)} fullWidth={true} sx={{ minWidth: 120 }}>
                Batch Assign Group
              </Button>
              <Button variant="outlined" color="primary" onClick={() => handleOpenAssignDialog(selectedIds)} fullWidth={true} sx={{ minWidth: 120 }}>
                Assign to TV Channel
              </Button>
            </Box>
          )}
          <Box sx={{ width: '100%', overflowX: 'auto' }}>
            <ChannelTable
              channels={channels}
              loading={isLoading}
              onCheckStatus={handleCheckStatus}
              onEdit={handleQuickEdit}
              onDelete={handleDelete}
              checkingStatus={checkingStatus}
              filters={filters}
              onFilterChange={handleFilterChange}
              totalCount={totalCount}
              page={page}
              pageSize={pageSize}
              onPageChange={setPage}
              onPageSizeChange={setPageSize}
              onSortChange={setSortModel}
              onSelectionChange={setSelectedIds}
              // Add assign button to each row
              extraActions={(row: any) => {
                const assignedTV = (tvChannels?.items || []).find((tv: any) => tv.id === row.tv_channel_id);
                if (row.tv_channel_id && assignedTV) {
                  return (
                    <Tooltip title={`Go to TV Channel: ${assignedTV.name}`} arrow>
                      <IconButton color="primary" onClick={() => navigate(`/tv-channels/${assignedTV.id}`)}>
                        <TvIcon />
                      </IconButton>
                    </Tooltip>
                  );
                }
                if (row.tv_channel_id && !assignedTV) {
                  return (
                    <Tooltip title={`Assigned to TV Channel #${row.tv_channel_id}`} arrow>
                      <IconButton disabled>
                        <TvIcon color="disabled" />
                      </IconButton>
                    </Tooltip>
                  );
                }
                return (
                  <Tooltip title="Assign to TV Channel" arrow>
                    <IconButton onClick={() => handleOpenAssignDialog([row.id])}>
                      <TvIcon />
                    </IconButton>
                  </Tooltip>
                );
              }}
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
        <AssignTVChannelDialog
          open={assignDialogOpen}
          onClose={handleCloseAssignDialog}
          tvChannels={tvChannels}
          onAssign={handleAssignTVChannel}
          loading={assigning}
          error={assignError}
        />
      </>
    </Box>
  );
};

export default AcestreamChannels;
