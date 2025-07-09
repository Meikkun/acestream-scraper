import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Grid,
  Button,
  CircularProgress,
  Alert,
  Chip,
  List,
  ListItem,
  ListItemText
} from '@mui/material';
import { useHealth, useStats } from '../hooks/useConfig';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';

const Health: React.FC = () => {
  // Queries
  const { data: healthData, isLoading: healthLoading, error: healthError, refetch: refetchHealth } = useHealth({
    refetchInterval: 60000 // Refetch every minute
  });
  
  const { data: statsData, isLoading: statsLoading, error: statsError, refetch: refetchStats } = useStats({
    refetchInterval: 60000 // Refetch every minute
  });

  // Helper function to render health status
  const renderHealthStatus = () => {
    if (!healthData) return null;
    
    const { status } = healthData;
    let icon;
    let color;
    
    switch (status) {
      case 'healthy':
        icon = <CheckCircleOutlineIcon />;
        color = 'success';
        break;
      case 'degraded':
        icon = <WarningAmberIcon />;
        color = 'warning';
        break;
      default:
        icon = <ErrorOutlineIcon />;
        color = 'error';
    }
    
    return (
      <Chip 
        icon={icon}
        label={status.toUpperCase()}
        color={color as any}
        sx={{ fontSize: '1rem', py: 2, px: 1 }}
      />
    );
  };

  // Render component state
  if (healthLoading || statsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (healthError || statsError) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {healthError ? `Health check error: ${healthError.toString()}` : ''}
          {statsError ? `Stats error: ${statsError.toString()}` : ''}
        </Alert>
        <Button variant="contained" onClick={() => {
          refetchHealth();
          refetchStats();
        }}>
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" gutterBottom>
          System Health
        </Typography>
        {renderHealthStatus()}
      </Box>

      <Grid container spacing={4}>
        {/* System Status Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="System Status" />
            <Divider />
            <CardContent>
              <List>
                <ListItem>
                  <ListItemText 
                    primary="Acestream Engine" 
                    secondary={healthData?.acestream.message || 'Status unknown'} 
                  />
                  <Chip 
                    label={healthData?.acestream.status.toUpperCase()}
                    color={
                      healthData?.acestream.status === 'online' ? 'success' :
                      healthData?.acestream.status === 'offline' ? 'error' : 'warning'
                    }
                    size="small"
                  />
                </ListItem>
                <Divider component="li" />
                <ListItem>
                  <ListItemText 
                    primary="Software Version" 
                    secondary={healthData?.version || 'Unknown'} 
                  />
                </ListItem>
              </List>
              <Button 
                variant="outlined" 
                onClick={() => refetchHealth()}
                sx={{ mt: 2 }}
              >
                Refresh Health Status
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* System Settings Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="System Configuration" />
            <Divider />
            <CardContent>
              <List dense>
                {healthData?.settings && Object.entries(healthData.settings).map(([key, value]) => (
                  <React.Fragment key={key}>
                    <ListItem>
                      <ListItemText 
                        primary={key} 
                        secondary={value} 
                      />
                    </ListItem>
                    <Divider component="li" />
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Channel Stats Card */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="Channel Statistics" />
            <Divider />
            <CardContent>
              {statsData ? (
                <List dense>
                  <ListItem>
                    <ListItemText primary="Total Channels" secondary={statsData.channels.total.toString()} />
                  </ListItem>
                  <Divider component="li" />
                  <ListItem>
                    <ListItemText primary="Online Channels" secondary={statsData.channels.online.toString()} />
                  </ListItem>
                  <Divider component="li" />
                  <ListItem>
                    <ListItemText primary="Offline Channels" secondary={statsData.channels.offline.toString()} />
                  </ListItem>
                  <Divider component="li" />
                  <ListItem>
                    <ListItemText primary="Unknown Status" secondary={statsData.channels.unknown.toString()} />
                  </ListItem>
                </List>
              ) : (
                <Typography color="textSecondary">No channel statistics available</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* URL Stats Card */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="URL Statistics" />
            <Divider />
            <CardContent>
              {statsData ? (
                <List dense>
                  <ListItem>
                    <ListItemText primary="Total URLs" secondary={statsData.urls.total.toString()} />
                  </ListItem>
                  <Divider component="li" />
                  <ListItem>
                    <ListItemText primary="Active URLs" secondary={statsData.urls.active.toString()} />
                  </ListItem>
                  <Divider component="li" />
                  <ListItem>
                    <ListItemText primary="Error URLs" secondary={statsData.urls.error.toString()} />
                  </ListItem>
                </List>
              ) : (
                <Typography color="textSecondary">No URL statistics available</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* EPG Stats Card */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="EPG Statistics" />
            <Divider />
            <CardContent>
              {statsData ? (
                <List dense>
                  <ListItem>
                    <ListItemText primary="EPG Sources" secondary={statsData.epg.sources.toString()} />
                  </ListItem>
                  <Divider component="li" />
                  <ListItem>
                    <ListItemText primary="EPG Channels" secondary={statsData.epg.channels.toString()} />
                  </ListItem>
                  <Divider component="li" />
                  <ListItem>
                    <ListItemText primary="EPG Programs" secondary={statsData.epg.programs.toString()} />
                  </ListItem>
                </List>
              ) : (
                <Typography color="textSecondary">No EPG statistics available</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Health;
