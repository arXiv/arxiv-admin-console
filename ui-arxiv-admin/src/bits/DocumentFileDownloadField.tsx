import React from 'react';
import { useRecordContext, FieldProps, useNotify } from 'react-admin';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import DownloadIcon from '@mui/icons-material/Download';
import Tooltip from '@mui/material/Tooltip';

interface DocumentFileDownloadFieldProps extends FieldProps {
    variant?: 'button' | 'icon';
}

const DocumentFileDownloadField: React.FC<DocumentFileDownloadFieldProps> = (props) => {
    const { variant = 'icon' } = props;
    const record = useRecordContext(props);
    const notify = useNotify();

    if (!record || !record.id) {
        return null;
    }

    const handleDownload = async () => {
        try {
            const access_token = localStorage.getItem('access_token');
            const token_type = localStorage.getItem('token_type') || 'Bearer';

            // Extract file name from the URI or use a default
            let fileName = 'download';
            if (record.file_name) {
                fileName = record.file_name;
            } else if (record.id) {
                const uri = record.id as string;
                const parts = uri.split('/');
                fileName = parts[parts.length - 1] || 'download';
            }

            const response = await fetch(`/admin-api/v1/documents/${record.document_id}/files/${encodeURIComponent(record.blob_id)}`, {
                method: 'GET',
                headers: {
                    'Authorization': `${token_type} ${access_token}`,
                },
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Download failed: ${response.statusText}`);
            }

            // Get the blob from the response
            const blob = await response.blob();

            // Create a temporary URL for the blob
            const url = window.URL.createObjectURL(blob);

            // Create a temporary anchor element and trigger download
            const a = document.createElement('a');
            a.href = url;
            a.download = fileName;
            document.body.appendChild(a);
            a.click();

            // Cleanup
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            notify('File downloaded successfully', { type: 'success' });
        } catch (error: any) {
            console.error('Error downloading file:', error);
            notify(error.message || 'Failed to download file', { type: 'error' });
        }
    };

    const downloadButton = variant === 'button' ? (
        <Button
            size="small"
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleDownload}
            disabled={!record.exists}
        >
            Download
        </Button>
    ) : (
        <Tooltip title={record.exists ? "Download file" : "File does not exist"}>
            <span>
                <IconButton
                    size="small"
                    onClick={handleDownload}
                    disabled={!record.exists}
                    color="primary"
                >
                    <DownloadIcon />
                </IconButton>
            </span>
        </Tooltip>
    );

    return downloadButton;
};

DocumentFileDownloadField.displayName = 'DocumentFileDownloadField';

export default DocumentFileDownloadField;
