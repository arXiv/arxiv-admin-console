import React, { useState, useEffect } from 'react';
import Dialog from '@mui/material/Dialog';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import DialogTitle from '@mui/material/DialogTitle';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select, { SelectChangeEvent } from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import Typography from '@mui/material/Typography';
import CircularProgress from '@mui/material/CircularProgress';
import { useNotify, useRefresh, Identifier } from 'react-admin';

type FileType = 'tarball' | 'abs';
type StorageType = 'gcp' | 'local';

interface DocumentFileUploadDialogProps {
    documentId?: Identifier;
    open: boolean;
    setOpen: (open: boolean) => void;
}

const DocumentFileUploadDialog: React.FC<DocumentFileUploadDialogProps> = ({
    documentId,
    open,
    setOpen
}) => {
    const notify = useNotify();
    const refresh = useRefresh();
    const [fileType, setFileType] = useState<FileType>('tarball');
    const [storage, setStorage] = useState<StorageType>('gcp');
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [isUploading, setIsUploading] = useState(false);

    // Clear selected file when file type changes
    useEffect(() => {
        setSelectedFile(null);
    }, [fileType]);

    const handleFileTypeChange = (event: SelectChangeEvent<FileType>) => {
        setFileType(event.target.value as FileType);
    };

    const handleStorageChange = (event: SelectChangeEvent<StorageType>) => {
        setStorage(event.target.value as StorageType);
    };

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const files = event.target.files;
        if (files && files.length > 0) {
            const file = files[0];

            // Validate file extension based on file type
            const fileName = file.name.toLowerCase();
            let isValid = false;
            let expectedExtension = '';

            if (fileType === 'abs') {
                expectedExtension = '.abs';
                isValid = fileName.endsWith('.abs');
            } else if (fileType === 'tarball') {
                expectedExtension = '.tar.gz';
                isValid = fileName.endsWith('.tar.gz');
            }

            if (!isValid) {
                notify(`Invalid file extension. Expected: ${expectedExtension}`, { type: 'error' });
                // Clear the file input
                event.target.value = '';
                return;
            }

            setSelectedFile(file);
        }
    };

    const handleUpload = async () => {
        if (!selectedFile || !documentId) {
            notify('Please select a file to upload', { type: 'warning' });
            return;
        }

        setIsUploading(true);

        try {
            const formData = new FormData();
            formData.append('uploading', selectedFile);
            formData.append('file_type', fileType);
            formData.append('storage_id', storage);

            const access_token = localStorage.getItem('access_token');
            const token_type = localStorage.getItem('token_type') || 'Bearer';

            // TODO: Replace with actual API endpoint
            const response = await fetch(`/admin-api/v1/documents/${documentId}/files`, {
                method: 'POST',
                headers: {
                    'Authorization': `${token_type} ${access_token}`,
                },
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Upload failed: ${response.statusText}`);
            }

            notify('File uploaded successfully', { type: 'success' });
            handleClose();
            refresh();
        } catch (error: any) {
            console.error('Error uploading file:', error);
            notify(error.message || 'Failed to upload file', { type: 'error' });
        } finally {
            setIsUploading(false);
        }
    };

    const handleClose = () => {
        if (!isUploading) {
            setOpen(false);
            setFileType('tarball');
            setStorage('gcp');
            setSelectedFile(null);
        }
    };

    if (!documentId) return null;

    return (
        <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
            <DialogTitle>Upload Document File</DialogTitle>
            <DialogContent>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 2 }}>
                    <FormControl fullWidth>
                        <InputLabel id="file-type-label">File Type</InputLabel>
                        <Select
                            labelId="file-type-label"
                            id="file-type"
                            value={fileType}
                            label="File Type"
                            onChange={handleFileTypeChange}
                            disabled={isUploading}
                        >
                            <MenuItem value="tarball">Sources</MenuItem>
                            <MenuItem value="abs">Abstract</MenuItem>
                        </Select>
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, ml: 1.5 }}>
                            Expected extension: {fileType === 'abs' ? '.abs' : '.tar.gz'}
                        </Typography>
                    </FormControl>

                    <FormControl fullWidth>
                        <InputLabel id="storage-label">Storage</InputLabel>
                        <Select
                            labelId="storage-label"
                            id="storage"
                            value={storage}
                            label="Storage"
                            onChange={handleStorageChange}
                            disabled={isUploading}
                        >
                            <MenuItem value="gcp">GCP Bucket</MenuItem>
                            <MenuItem value="local">Local files</MenuItem>
                        </Select>
                    </FormControl>

                    <Box>
                        <input
                            accept={fileType === 'abs' ? '.abs' : '.tar.gz'}
                            style={{ display: 'none' }}
                            id="raised-button-file"
                            type="file"
                            onChange={handleFileChange}
                            disabled={isUploading}
                        />
                        <label htmlFor="raised-button-file">
                            <Button
                                variant="outlined"
                                component="span"
                                fullWidth
                                disabled={isUploading}
                            >
                                Choose File
                            </Button>
                        </label>
                        {selectedFile && (
                            <Typography variant="body1" fontSize={"large"} sx={{ mt: 1, color: 'text.secondary' }}>
                                Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(2)} KB)
                            </Typography>
                        )}
                    </Box>
                </Box>
            </DialogContent>
            <DialogActions>
                <Button onClick={handleClose} disabled={isUploading}>
                    Cancel
                </Button>
                <Box sx={{ flexGrow: 1 }} />
                {isUploading && <CircularProgress size={24} />}
                <Button
                    onClick={handleUpload}
                    variant="contained"
                    disabled={!selectedFile || isUploading}
                >
                    {isUploading ? 'Uploading...' : 'Upload'}
                </Button>
            </DialogActions>
        </Dialog>
    );
};

export default DocumentFileUploadDialog;
