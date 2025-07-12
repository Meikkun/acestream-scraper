import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography,
  Box,
  Paper,
  Grid,
  Button,
  TextField,
  FormControlLabel,
  Switch,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  CardActions,
  Divider,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  SelectChangeEvent,
  Chip
} from '@mui/material';
import {
  Save,
  Delete,
  ArrowBack,
  Refresh,
  Link as LinkIcon,
  CheckCircle,
  Cancel
} from '@mui/icons-material';
import { useChannel, useUpdateChannel, useDeleteChannel, useCheckChannelStatus } from '../hooks/useChannels';
import { getErrorMessage } from '../utils/errorUtils';
import { useAllTVChannels } from '../hooks/useTVChannels';
import { formatDate } from '../utils/errorUtils';

/**
 * Channel detail page component for viewing and editing a channel
 */
const ChannelDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // States
  const [formData, setFormData] = useState({
    name: '',
    group: '',
    logo: '',
    tvg_id: '',
    tvg_name: '',
    source_url: '',
    epg_update_protected: false,
    tv_channel_id: ''
  });
  const [isEditing, setIsEditing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Queries and mutations
  const {
    data: channel,
    isLoading,
    error: fetchError,
    refetch
  } = useChannel(id || '');

  const updateChannel = useUpdateChannel(id || '');
  const deleteChannel = useDeleteChannel();
  const checkStatus = useCheckChannelStatus(id || '');
  const { data: tvChannels } = useAllTVChannels();

  // Set form data when channel data is loaded
  useEffect(() => {
    if (channel) {
      setFormData({
        name: channel.name || '',
        group: channel.group || '',
        logo: channel.logo || '',
        tvg_id: channel.tvg_id || '',
        tvg_name: channel.tvg_name || '',
        source_url: channel.source_url || '',
        epg_update_protected: channel.epg_update_protected || false,
        tv_channel_id: channel.tv_channel_id?.toString() || ''
      });
    }
  }, [channel]);

  // Handle input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // Handle switch changes
  const handleSwitchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = e.target;
    setFormData(prev => ({ ...prev, [name]: checked }));
  };

  // Handle select changes
  const handleSelectChange = (e: SelectChangeEvent) => {
    const name = e.target.name as string;
    const value = e.target.value;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // Handle save
  const handleSave = async () => {
    try {
      await updateChannel.mutateAsync({
        name: formData.name,
        group: formData.group,
        logo: formData.logo,
        tvg_id: formData.tvg_id,
        tvg_name: formData.tvg_name,
        source_url: formData.source_url,
        epg_update_protected: formData.epg_update_protected,
        tv_channel_id: formData.tv_channel_id ? parseInt(formData.tv_channel_id) : undefined
      });

      setSuccess('Channel updated successfully');
      setIsEditing(false);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(`Failed to update channel: ${getErrorMessage(err)}`);
    }
  };

  // Handle delete
  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this channel?')) {
      try {
        await deleteChannel.mutateAsync(id || '');
        navigate('/channels');
      } catch (err) {
        setError(`Failed to delete channel: ${getErrorMessage(err)}`);
      }
    }
  };

  // Handle check status
  const handleCheckStatus = async () => {
    try {
      await checkStatus.mutateAsync();
      setSuccess('Channel status checked successfully');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(`Failed to check channel status: ${getErrorMessage(err)}`);
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (fetchError) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {getErrorMessage(fetchError)}
      </Alert>
    );
  }

  if (!channel) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        Channel not found
      </Alert>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      {/* Header with actions */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Button
            startIcon={<ArrowBack />}
            onClick={() => navigate('/channels')}
            sx={{ mr: 2 }}
          >
            Back
          </Button>
          <Typography variant="h4" component="h1">
            Channel Details
          </Typography>
        </Box>
        <Box>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleCheckStatus}
            disabled={checkStatus.isLoading}
            sx={{ mr: 1 }}
          >
            Check Status
          </Button>
          {isEditing ? (
            <>
              <Button
                variant="contained"
                color="primary"
                startIcon={<Save />}
                onClick={handleSave}
                disabled={updateChannel.isLoading}
                sx={{ mr: 1 }}
              >
                Save
              </Button>
              <Button
                variant="outlined"
                onClick={() => {
                  setIsEditing(false);
                  // Reset form data to original channel data
                  if (channel) {
                    setFormData({
                      name: channel.name || '',
                      group: channel.group || '',
                      logo: channel.logo || '',
                      tvg_id: channel.tvg_id || '',
                      tvg_name: channel.tvg_name || '',
                      source_url: channel.source_url || '',
                      epg_update_protected: channel.epg_update_protected || false,
                      tv_channel_id: channel.tv_channel_id?.toString() || ''
                    });
                  }
                }}
                sx={{ mr: 1 }}
              >
                Cancel
              </Button>
            </>
          ) : (
            <Button
              variant="contained"
              onClick={() => setIsEditing(true)}
              sx={{ mr: 1 }}
            >
              Edit
            </Button>
          )}
          <Button
            variant="outlined"
            color="error"
            startIcon={<Delete />}
            onClick={handleDelete}
            disabled={deleteChannel.isLoading}
          >
            Delete
          </Button>
        </Box>
      </Box>

      {/* Messages */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Channel status card */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                Status
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <Chip
                  label={channel.status}
                  color={channel.status === 'active' ? 'success' : 'default'}
                  size="small"
                  sx={{ mr: 2 }}
                />
                {channel.is_online === null ? (
                  <Chip label="Not checked" size="small" color="default" />
                ) : channel.is_online ? (
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <CheckCircle color="success" sx={{ mr: 0.5 }} />
                    <Typography>Online</Typography>
                  </Box>
                ) : (
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Cancel color="error" sx={{ mr: 0.5 }} />
                    <Typography>Offline</Typography>
                  </Box>
                )}
              </Box>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                Last Checked
              </Typography>
              <Typography>
                {channel.last_checked ? formatDate(channel.last_checked) : 'Never'}
              </Typography>
              {channel.check_error && (
                <Typography color="error" variant="body2" sx={{ mt: 1 }}>
                  Error: {channel.check_error}
                </Typography>
              )}
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Channel details form */}
      <Paper sx={{ p: 3 }}>
        <Grid container spacing={3}>
          {/* Basic info */}
          <Grid item xs={12}>
            <Typography variant="h6" sx={{ mb: 2 }}>Basic Information</Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Name"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  fullWidth
                  disabled={!isEditing}
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Group"
                  name="group"
                  value={formData.group}
                  onChange={handleInputChange}
                  fullWidth
                  disabled={!isEditing}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="Logo URL"
                  name="logo"
                  value={formData.logo}
                  onChange={handleInputChange}
                  fullWidth
                  disabled={!isEditing}
                />
              </Grid>
            </Grid>
          </Grid>

          <Grid item xs={12}>
            <Divider />
          </Grid>

          {/* EPG info */}
          <Grid item xs={12}>
            <Typography variant="h6" sx={{ mb: 2 }}>EPG Information</Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="TVG ID"
                  name="tvg_id"
                  value={formData.tvg_id}
                  onChange={handleInputChange}
                  fullWidth
                  disabled={!isEditing}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="TVG Name"
                  name="tvg_name"
                  value={formData.tvg_name}
                  onChange={handleInputChange}
                  fullWidth
                  disabled={!isEditing}
                />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.epg_update_protected}
                      onChange={handleSwitchChange}
                      name="epg_update_protected"
                      disabled={!isEditing}
                    />
                  }
                  label="Protect from automatic EPG updates"
                />
              </Grid>
            </Grid>
          </Grid>

          <Grid item xs={12}>
            <Divider />
          </Grid>

          {/* Source info */}
          <Grid item xs={12}>
            <Typography variant="h6" sx={{ mb: 2 }}>Source Information</Typography>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  label="Source URL"
                  name="source_url"
                  value={formData.source_url}
                  onChange={handleInputChange}
                  fullWidth
                  disabled={!isEditing}
                  InputProps={{
                    startAdornment: <LinkIcon sx={{ mr: 1, color: 'text.secondary' }} />
                  }}
                />
              </Grid>
            </Grid>
          </Grid>

          <Grid item xs={12}>
            <Divider />
          </Grid>

          {/* TV Channel Association */}
          <Grid item xs={12}>
            <Typography variant="h6" sx={{ mb: 2 }}>TV Channel Association</Typography>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <FormControl fullWidth disabled={!isEditing}>
                  <InputLabel id="tv-channel-label">Associated TV Channel</InputLabel>
                  <Select
                    labelId="tv-channel-label"
                    name="tv_channel_id"
                    value={formData.tv_channel_id}
                    onChange={handleSelectChange}
                    label="Associated TV Channel"
                  >
                    <MenuItem value="">
                      <em>None</em>
                    </MenuItem>
                    {(tvChannels?.items || []).map((tvChannel: any) => (
                      <MenuItem key={tvChannel.id} value={tvChannel.id.toString()}>
                        {tvChannel.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Grid>

          {/* Timestamps */}
          <Grid item xs={12}>
            <Divider />
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="textSecondary">
                Added: {formatDate(channel.added_at)}
              </Typography>
              {channel.last_processed && (
                <Typography variant="body2" color="textSecondary">
                  Last Processed: {formatDate(channel.last_processed)}
                </Typography>
              )}
            </Box>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
};

export default ChannelDetail;
