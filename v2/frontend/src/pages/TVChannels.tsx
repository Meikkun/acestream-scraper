import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
  Pagination,
  CircularProgress,
  TextField,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControlLabel,
  Switch,
  AppBar,
  Toolbar,
  Link,
  useTheme,
  useMediaQuery,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Avatar
} from '@mui/material';
import { Edit as EditIcon, Delete as DeleteIcon, PlayArrow as PlayIcon } from '@mui/icons-material';
import { useAllTVChannels, useDeleteTVChannel, useCreateTVChannel, useUpdateTVChannel } from '../hooks/useTVChannels';
import { TVChannel, TVChannelCreate, TVChannelUpdate } from '../types/tvChannelTypes';
import { Link as RouterLink } from 'react-router-dom';
import './TVChannels.css';

const ITEMS_PER_PAGE = 12;

const TVChannels: React.FC = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [openCreateDialog, setOpenCreateDialog] = useState(false);
  const [openEditDialog, setOpenEditDialog] = useState(false);
  const [selectedChannel, setSelectedChannel] = useState<TVChannel | null>(null);
  const [formData, setFormData] = useState<TVChannelCreate | TVChannelUpdate>({
    name: '',
    logo_url: '',
    description: '',
    category: '',
    country: '',
    language: '',
    is_active: true
  });

  const skip = (page - 1) * ITEMS_PER_PAGE;
  const { data: channels, isLoading, isError } = useAllTVChannels(skip, ITEMS_PER_PAGE);
  const deleteMutation = useDeleteTVChannel();
  const createMutation = useCreateTVChannel();
  const updateMutation = useUpdateTVChannel();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const handlePageChange = (_event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };

  const handleOpenCreateDialog = () => {
    setFormData({
      name: '',
      logo_url: '',
      description: '',
      category: '',
      country: '',
      language: '',
      is_active: true,
      is_favorite: false
    });
    setOpenCreateDialog(true);
  };

  const handleOpenEditDialog = (channel: TVChannel) => {
    setSelectedChannel(channel);
    setFormData({
      name: channel.name,
      logo_url: channel.logo_url || '',
      description: channel.description || '',
      category: channel.category || '',
      country: channel.country || '',
      language: channel.language || '',
      is_active: channel.is_active,
      is_favorite: channel.is_favorite,
      epg_id: channel.epg_id || '',
      channel_number: channel.channel_number
    });
    setOpenEditDialog(true);
  };

  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const handleCreate = async () => {
    try {
      await createMutation.mutateAsync(formData as TVChannelCreate);
      setOpenCreateDialog(false);
    } catch (error) {
      console.error('Error creating TV channel:', error);
    }
  };

  const handleUpdate = async () => {
    if (!selectedChannel) return;

    try {
      await updateMutation.mutateAsync({
        id: selectedChannel.id,
        updates: formData as TVChannelUpdate
      });
      setOpenEditDialog(false);
    } catch (error) {
      console.error('Error updating TV channel:', error);
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this TV channel?')) {
      try {
        await deleteMutation.mutateAsync(id);
      } catch (error) {
        console.error('Error deleting TV channel:', error);
      }
    }
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress />
      </Box>
    );
  }

  if (isError) {
    return (
      <Box p={3}>
        <Typography color="error">Error loading TV channels.</Typography>
      </Box>
    );
  }

  const totalPages = Math.ceil((channels?.total || 0) / ITEMS_PER_PAGE);

  return (
    <Box sx={{ width: '100%' }}>
      {/* Removed AppBar/Toolbar navigation buttons, now handled by NavBar */}
      <Box p={isMobile ? 1 : 3}>
        <Box display="flex" flexDirection={isMobile ? 'column' : 'row'} justifyContent="space-between" alignItems={isMobile ? 'stretch' : 'center'} mb={3} gap={2}>
          <Typography variant="h4">TV Channels</Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={handleOpenCreateDialog}
            sx={{ width: isMobile ? '100%' : 'auto' }}
          >
            Add TV Channel
          </Button>
        </Box>
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Logo</TableCell>
                <TableCell>Name</TableCell>
                <TableCell>Number</TableCell>
                <TableCell>Category</TableCell>
                <TableCell>Language</TableCell>
                <TableCell>Country</TableCell>
                <TableCell>Streams</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(channels?.items || []).map((channel) => (
                <TableRow key={channel.id} hover sx={{ cursor: 'pointer' }} onClick={() => navigate(`/tv-channels/${channel.id}`)}>
                  <TableCell>
                    {channel.logo_url ? <Avatar src={channel.logo_url} alt={channel.name} /> : null}
                  </TableCell>
                  <TableCell>{channel.name}</TableCell>
                  <TableCell>{channel.channel_number ?? '—'}</TableCell>
                  <TableCell>{channel.category || '-'}</TableCell>
                  <TableCell>{channel.language || '-'}</TableCell>
                  <TableCell>{channel.country || '-'}</TableCell>
                  <TableCell>{Array.isArray(channel.acestream_channels) ? channel.acestream_channels.length : '—'}</TableCell>
                  <TableCell>
                    <Typography variant="body2" color={channel.is_active ? 'primary' : 'error'}>
                      {channel.is_active ? 'Active' : 'Inactive'}
                    </Typography>
                  </TableCell>
                  <TableCell onClick={e => e.stopPropagation()}>
                    <IconButton size="small" onClick={() => handleOpenEditDialog(channel)}>
                      <EditIcon />
                    </IconButton>
                    <IconButton size="small" onClick={() => handleDelete(channel.id)}>
                      <DeleteIcon />
                    </IconButton>
                    <IconButton size="small" color="primary" disabled={channel.acestream_channels.length === 0} onClick={() => navigate(`/tv-channels/${channel.id}`)}>
                      <PlayIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        <Box display="flex" justifyContent="center" mt={4}>
          <Pagination
            count={totalPages}
            page={page}
            onChange={handlePageChange}
            color="primary"
          />
        </Box>

        {/* Create TV Channel Dialog */}
        <Dialog open={openCreateDialog} onClose={() => setOpenCreateDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Add TV Channel</DialogTitle>
          <DialogContent>
            <Box my={2}>
              <TextField
                autoFocus
                name="name"
                label="Channel Name"
                fullWidth
                value={formData.name}
                onChange={handleFormChange}
                required
                margin="dense"
              />
              <TextField
                name="logo_url"
                label="Logo URL"
                fullWidth
                value={formData.logo_url}
                onChange={handleFormChange}
                margin="dense"
              />
              <TextField
                name="description"
                label="Description"
                fullWidth
                value={formData.description || ''}
                onChange={handleFormChange}
                margin="dense"
                multiline
                rows={3}
              />
              <TextField
                name="category"
                label="Category"
                fullWidth
                value={formData.category || ''}
                onChange={handleFormChange}
                margin="dense"
              />
              <TextField
                name="country"
                label="Country"
                fullWidth
                value={formData.country || ''}
                onChange={handleFormChange}
                margin="dense"
              />
              <TextField
                name="language"
                label="Language"
                fullWidth
                value={formData.language || ''}
                onChange={handleFormChange}
                margin="dense"
              />
              <TextField
                name="channel_number"
                label="Channel Number"
                type="number"
                fullWidth
                value={formData.channel_number || ''}
                onChange={handleFormChange}
                margin="dense"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_active === true}
                    onChange={handleFormChange}
                    name="is_active"
                    color="primary"
                  />
                }
                label="Active"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_favorite === true}
                    onChange={handleFormChange}
                    name="is_favorite"
                    color="primary"
                  />
                }
                label="Favorite"
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenCreateDialog(false)} color="inherit">
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              color="primary"
              variant="contained"
              disabled={!formData.name}
            >
              Create
            </Button>
          </DialogActions>
        </Dialog>

        {/* Edit TV Channel Dialog */}
        <Dialog open={openEditDialog} onClose={() => setOpenEditDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Edit TV Channel</DialogTitle>
          <DialogContent>
            <Box my={2}>
              <TextField
                autoFocus
                name="name"
                label="Channel Name"
                fullWidth
                value={formData.name}
                onChange={handleFormChange}
                required
                margin="dense"
              />
              <TextField
                name="logo_url"
                label="Logo URL"
                fullWidth
                value={formData.logo_url}
                onChange={handleFormChange}
                margin="dense"
              />
              <TextField
                name="description"
                label="Description"
                fullWidth
                value={formData.description || ''}
                onChange={handleFormChange}
                margin="dense"
                multiline
                rows={3}
              />
              <TextField
                name="category"
                label="Category"
                fullWidth
                value={formData.category || ''}
                onChange={handleFormChange}
                margin="dense"
              />
              <TextField
                name="country"
                label="Country"
                fullWidth
                value={formData.country || ''}
                onChange={handleFormChange}
                margin="dense"
              />
              <TextField
                name="language"
                label="Language"
                fullWidth
                value={formData.language || ''}
                onChange={handleFormChange}
                margin="dense"
              />
              <TextField
                name="epg_id"
                label="EPG ID"
                fullWidth
                value={formData.epg_id || ''}
                onChange={handleFormChange}
                margin="dense"
              />
              <TextField
                name="channel_number"
                label="Channel Number"
                type="number"
                fullWidth
                value={formData.channel_number || ''}
                onChange={handleFormChange}
                margin="dense"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_active === true}
                    onChange={handleFormChange}
                    name="is_active"
                    color="primary"
                  />
                }
                label="Active"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_favorite === true}
                    onChange={handleFormChange}
                    name="is_favorite"
                    color="primary"
                  />
                }
                label="Favorite"
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenEditDialog(false)} color="inherit">
              Cancel
            </Button>
            <Button
              onClick={handleUpdate}
              color="primary"
              variant="contained"
              disabled={!formData.name}
            >
              Update
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </Box>
  );
};

export default TVChannels;
