import React, { useState } from 'react';
import {
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  TextField,
  Checkbox,
  FormControlLabel,
  FormGroup,
  Switch,
  Alert,
  CircularProgress
} from '@mui/material';

interface BulkOperationsProps {
  open: boolean;
  onClose: () => void;
  selectedChannels: any[];
  onBulkEdit: (updates: any) => Promise<void>;
  onBulkDelete: () => Promise<void>;
  onBulkActivate: (active: boolean) => Promise<void>;
}

const BulkOperations: React.FC<BulkOperationsProps> = ({
  open,
  onClose,
  selectedChannels,
  onBulkEdit,
  onBulkDelete,
  onBulkActivate
}) => {
  const [editFields, setEditFields] = useState({
    category: false,
    country: false,
    language: false,
    is_active: false
  });
  const [editValues, setEditValues] = useState({
    category: '',
    country: '',
    language: '',
    is_active: true
  });
  const [mode, setMode] = useState<'edit'|'delete'|'activate'|null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string|null>(null);
  const [success, setSuccess] = useState<string|null>(null);

  const handleFieldToggle = (field: string) => {
    setEditFields(prev => ({ ...prev, [field]: !prev[field as keyof typeof prev] }));
  };

  const handleValueChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setEditValues(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleBulkEdit = async () => {
    setLoading(true);
    setError(null);
    try {
      const updates: any = {};
      Object.keys(editFields).forEach(field => {
        if (editFields[field as keyof typeof editFields]) {
          updates[field] = editValues[field as keyof typeof editValues];
        }
      });
      await onBulkEdit(updates);
      setSuccess('Channels updated successfully.');
      setTimeout(() => { setSuccess(null); onClose(); }, 1500);
    } catch (err: any) {
      setError(err.message || 'Bulk edit failed');
    } finally {
      setLoading(false);
    }
  };

  const handleBulkDelete = async () => {
    setLoading(true);
    setError(null);
    try {
      await onBulkDelete();
      setSuccess('Channels deleted successfully.');
      setTimeout(() => { setSuccess(null); onClose(); }, 1500);
    } catch (err: any) {
      setError(err.message || 'Bulk delete failed');
    } finally {
      setLoading(false);
    }
  };

  const handleBulkActivate = async (active: boolean) => {
    setLoading(true);
    setError(null);
    try {
      await onBulkActivate(active);
      setSuccess(`Channels ${active ? 'activated' : 'deactivated'} successfully.`);
      setTimeout(() => { setSuccess(null); onClose(); }, 1500);
    } catch (err: any) {
      setError(err.message || 'Bulk status update failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Bulk Operations for {selectedChannels.length} Channels</DialogTitle>
      <DialogContent>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
        <Box mb={2}>
          <Button variant="outlined" onClick={() => setMode('edit')} sx={{ mr: 1 }}>Bulk Edit</Button>
          <Button variant="outlined" color="error" onClick={() => setMode('delete')} sx={{ mr: 1 }}>Bulk Delete</Button>
          <Button variant="outlined" color="success" onClick={() => setMode('activate')}>Bulk Activate/Deactivate</Button>
        </Box>
        {mode === 'edit' && (
          <Box>
            <Typography variant="subtitle1" gutterBottom>Select fields to update:</Typography>
            <FormGroup>
              <FormControlLabel control={<Checkbox checked={editFields.category} onChange={() => handleFieldToggle('category')} />} label="Category" />
              {editFields.category && <TextField name="category" label="Category" value={editValues.category} onChange={handleValueChange} fullWidth sx={{ mb: 2 }} />}
              <FormControlLabel control={<Checkbox checked={editFields.country} onChange={() => handleFieldToggle('country')} />} label="Country" />
              {editFields.country && <TextField name="country" label="Country" value={editValues.country} onChange={handleValueChange} fullWidth sx={{ mb: 2 }} />}
              <FormControlLabel control={<Checkbox checked={editFields.language} onChange={() => handleFieldToggle('language')} />} label="Language" />
              {editFields.language && <TextField name="language" label="Language" value={editValues.language} onChange={handleValueChange} fullWidth sx={{ mb: 2 }} />}
              <FormControlLabel control={<Checkbox checked={editFields.is_active} onChange={() => handleFieldToggle('is_active')} />} label="Active Status" />
              {editFields.is_active && <FormControlLabel control={<Switch checked={editValues.is_active} onChange={handleValueChange} name="is_active" color="primary" />} label="Active" />}
            </FormGroup>
          </Box>
        )}
        {mode === 'delete' && (
          <Alert severity="warning">Are you sure you want to delete {selectedChannels.length} channels? This action cannot be undone.</Alert>
        )}
        {mode === 'activate' && (
          <Box>
            <Button variant="contained" color="success" onClick={() => handleBulkActivate(true)} disabled={loading} sx={{ mr: 1 }}>Activate All</Button>
            <Button variant="contained" color="warning" onClick={() => handleBulkActivate(false)} disabled={loading}>Deactivate All</Button>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} color="inherit">Cancel</Button>
        {mode === 'edit' && <Button onClick={handleBulkEdit} color="primary" variant="contained" disabled={loading}>Update</Button>}
        {mode === 'delete' && <Button onClick={handleBulkDelete} color="error" variant="contained" disabled={loading}>Delete</Button>}
      </DialogActions>
      {loading && <Box display="flex" justifyContent="center" alignItems="center" p={2}><CircularProgress /></Box>}
    </Dialog>
  );
};

export default BulkOperations;
