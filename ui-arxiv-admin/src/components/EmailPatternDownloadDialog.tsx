import React, { useState, useContext } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Box,
    Typography,
    LinearProgress,
    Alert
} from '@mui/material';
import { useNotify } from 'react-admin';
import CloudDownloadIcon from '@mui/icons-material/CloudDownload';
import { RuntimeContext } from '../RuntimeContext';
import { emailPatternPurposeOptions } from "../types/definitions";

interface EmailPatternDownloadDialogProps {
    open: boolean;
    onClose: () => void;
}

export const EmailPatternDownloadDialog: React.FC<EmailPatternDownloadDialogProps> = ({ open, onClose }) => {
    const [purpose, setPurpose] = useState<string>('black');
    const [downloading, setDownloading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    
    const notify = useNotify();
    const runtimeProps = useContext(RuntimeContext);

    const handleDownload = async () => {
        setDownloading(true);
        setError(null);

        try {
            const response = await fetch(`${runtimeProps.ADMIN_API_BACKEND_URL}/v1/email_patterns/export/${purpose}`, {
                method: 'GET',
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Download failed');
            }

            // Get the blob and create download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `email_patterns_${purpose}_${new Date().toISOString().split('T')[0]}.txt`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);

            notify(`Downloaded ${purpose} email patterns`, { type: 'success' });
            handleClose();
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Download failed';
            setError(errorMessage);
            notify('Download failed', { type: 'error' });
        } finally {
            setDownloading(false);
        }
    };

    const handleClose = () => {
        setPurpose('black');
        setError(null);
        setDownloading(false);
        onClose();
    };

    return (
        <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
            <DialogTitle>Download Email Patterns</DialogTitle>
            <DialogContent>
                <Box display="flex" flexDirection="column" gap={3} sx={{ mt: 1 }}>
                    {/* Purpose Selection */}
                    <FormControl fullWidth>
                        <InputLabel>Purpose</InputLabel>
                        <Select
                            value={purpose}
                            label="Purpose"
                            onChange={(e) => setPurpose(e.target.value)}
                        >
                            {emailPatternPurposeOptions.map(option => (
                                <MenuItem key={option.id} value={option.id}>
                                    {option.name}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>

                    <Typography variant="caption" color="text.secondary">
                        Downloads all email patterns for the selected purpose as a text file with one pattern per line.
                    </Typography>

                    {/* Progress Indicator */}
                    {downloading && (
                        <Box>
                            <Typography variant="body2" gutterBottom>
                                Downloading...
                            </Typography>
                            <LinearProgress />
                        </Box>
                    )}

                    {/* Error Display */}
                    {error && (
                        <Alert severity="error">
                            {error}
                        </Alert>
                    )}
                </Box>
            </DialogContent>
            <DialogActions>
                <Button onClick={handleClose} disabled={downloading}>
                    Cancel
                </Button>
                <Button 
                    onClick={handleDownload} 
                    variant="contained" 
                    startIcon={<CloudDownloadIcon />}
                    disabled={downloading}
                >
                    Download
                </Button>
            </DialogActions>
        </Dialog>
    );
};