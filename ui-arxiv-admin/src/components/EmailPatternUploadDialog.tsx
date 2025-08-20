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
    RadioGroup,
    FormControlLabel,
    Radio,
    FormLabel,
    Box,
    Typography,
    LinearProgress,
    Alert
} from '@mui/material';
import { useNotify, useRefresh } from 'react-admin';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { RuntimeContext } from '../RuntimeContext';
import { emailPatternPurposeOptions } from "../types/definitions";

interface EmailUploadUploadDialogProps {
    open: boolean;
    onClose: () => void;
}


const operationOptions = [
    { id: 'append', name: 'Append' },
    { id: 'replace', name: 'Replace' },
];

export const EmailPatternUploadDialog: React.FC<EmailUploadUploadDialogProps> = ({ open, onClose }) => {
    const [file, setFile] = useState<File | null>(null);
    const [purpose, setPurpose] = useState<string>('black');
    const [operation, setOperation] = useState<string>('append');
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    
    const notify = useNotify();
    const refresh = useRefresh();
    const runtimeProps = useContext(RuntimeContext);

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = event.target.files?.[0];
        if (selectedFile) {
            // Validate file type (text files only)
            if (selectedFile.type === 'text/plain' || selectedFile.name.endsWith('.txt')) {
                setFile(selectedFile);
                setError(null);
            } else {
                setError('Please select a text file (.txt)');
                setFile(null);
            }
        }
    };

    const handleUpload = async () => {
        if (!file) {
            setError('Please select a file');
            return;
        }

        setUploading(true);
        setError(null);

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('purpose', purpose);
            formData.append('operation', operation);

            const response = await fetch(`${runtimeProps.ADMIN_API_BACKEND_URL}/v1/email_patterns/import`, {
                method: 'POST',
                body: formData,
                headers: {
                    'Authorization': `${localStorage.getItem('token_type')} ${localStorage.getItem('access_token')}`
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Upload failed');
            }

            const result = await response.json();
            notify(`Successfully processed ${result.processed_count} patterns`, { type: 'success' });
            refresh();
            handleClose();
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Upload failed';
            setError(errorMessage);
            notify('Upload failed', { type: 'error' });
        } finally {
            setUploading(false);
        }
    };

    const handleClose = () => {
        setFile(null);
        setPurpose('black');
        setOperation('append');
        setError(null);
        setUploading(false);
        onClose();
    };

    return (
        <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
            <DialogTitle>Bulk Email Pattern Upload</DialogTitle>
            <DialogContent>
                <Box display="flex" flexDirection="column" gap={3} sx={{ mt: 1 }}>
                    {/* File Upload */}
                    <Box>
                        <Typography variant="subtitle2" gutterBottom>
                            Select File
                        </Typography>
                        <Button
                            variant="outlined"
                            component="label"
                            startIcon={<CloudUploadIcon />}
                            fullWidth
                            sx={{ mb: 1 }}
                        >
                            Choose Text File
                            <input
                                type="file"
                                accept=".txt,text/plain"
                                onChange={handleFileChange}
                                hidden
                            />
                        </Button>
                        {file && (
                            <Typography variant="body2" color="text.secondary">
                                Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
                            </Typography>
                        )}
                        <Typography variant="caption" color="text.secondary">
                            Upload a text file with one email pattern per line
                        </Typography>
                    </Box>

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

                    {/* Operation Selection */}
                    <FormControl>
                        <FormLabel component="legend">Operation</FormLabel>
                        <RadioGroup
                            value={operation}
                            onChange={(e) => setOperation(e.target.value)}
                            row
                        >
                            {operationOptions.map(option => (
                                <FormControlLabel
                                    key={option.id}
                                    value={option.id}
                                    control={<Radio />}
                                    label={option.name}
                                />
                            ))}
                        </RadioGroup>
                        <Typography variant="caption" color="text.secondary">
                            Append: Add patterns to existing list | Replace: Clear existing patterns and add new ones
                        </Typography>
                    </FormControl>

                    {/* Progress Indicator */}
                    {uploading && (
                        <Box>
                            <Typography variant="body2" gutterBottom>
                                Uploading...
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
                <Button onClick={handleClose} disabled={uploading}>
                    Cancel
                </Button>
                <Button 
                    onClick={handleUpload} 
                    variant="contained" 
                    disabled={!file || uploading}
                >
                    Upload
                </Button>
            </DialogActions>
        </Dialog>
    );
};