import React, { useState } from 'react';
import { useRecordContext, FieldProps } from 'react-admin';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import UploadIcon from '@mui/icons-material/Upload';
import Tooltip from '@mui/material/Tooltip';
import DocumentFileUploadDialog from '../components/DocumentFileUploadDialog';

interface DocumentFileUploadFieldProps extends Omit<FieldProps, 'source'> {
    variant?: 'button' | 'icon';
    source?: string;
}

const DocumentFileUploadField: React.FC<DocumentFileUploadFieldProps> = (props) => {
    const { variant = 'icon' } = props;
    const record = useRecordContext(props);
    const [open, setOpen] = useState(false);

    if (!record || !record.document_id) {
        return null;
    }

    // Determine file type from file name or id
    let fileType: 'tarball' | 'abs' = 'tarball';
    const fileName = (record.file_name || record.id || '').toLowerCase();
    if (fileName.endsWith('.abs')) {
        fileType = 'abs';
    }

    // Determine storage from URI
    let storage: 'gcp' | 'local' = 'local';
    const uri = (record.id || '').toLowerCase();
    if (uri.startsWith('gs://')) {
        storage = 'gcp';
    } else if (uri.startsWith('file://')) {
        storage = 'local';
    }

    const handleClick = () => {
        setOpen(true);
    };

    const uploadButton = variant === 'button' ? (
        <Button
            size="small"
            variant="outlined"
            startIcon={<UploadIcon />}
            onClick={handleClick}
        >
            Upload
        </Button>
    ) : (
        <Tooltip title="Upload file">
            <IconButton
                size="small"
                onClick={handleClick}
                color="primary"
            >
                <UploadIcon />
            </IconButton>
        </Tooltip>
    );

    return (
        <>
            {uploadButton}
            <DocumentFileUploadDialog
                documentId={record.document_id}
                open={open}
                setOpen={setOpen}
                defaultFileType={fileType}
                defaultStorage={storage}
            />
        </>
    );
};

DocumentFileUploadField.displayName = 'DocumentFileUploadField';

export default DocumentFileUploadField;
