import React from 'react';
import { useRecordContext, FieldProps } from 'react-admin';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Tooltip from '@mui/material/Tooltip';

interface StorageURLFieldProps extends FieldProps {
    showSchema?: boolean;
    showBucket?: boolean;
    showPath?: boolean;
    showFullURI?: boolean;
}

interface ParsedURI {
    schema: string;
    schemaLabel: string;
    bucket?: string;
    path: string;
    fullURI: string;
}

const parseStorageURI = (uri: string): ParsedURI | null => {
    if (!uri) return null;

    try {
        // Handle file:// URIs
        if (uri.startsWith('file://')) {
            const path = uri.substring(7); // Remove 'file://'
            return {
                schema: 'file',
                schemaLabel: 'CIT',
                path: path,
                fullURI: uri,
                bucket: "file"
            };
        }

        // Handle gs:// URIs (Google Cloud Storage)
        if (uri.startsWith('gs://')) {
            const withoutSchema = uri.substring(5); // Remove 'gs://'
            const firstSlashIndex = withoutSchema.indexOf('/');

            if (firstSlashIndex === -1) {
                // Just bucket, no path
                return {
                    schema: 'gs',
                    schemaLabel: 'GCS',
                    bucket: withoutSchema,
                    path: '',
                    fullURI: uri,
                };
            }

            const bucket = withoutSchema.substring(0, firstSlashIndex);
            const path = withoutSchema.substring(firstSlashIndex + 1);

            return {
                schema: 'gs',
                schemaLabel: 'GCS',
                bucket: bucket,
                path: path,
                fullURI: uri,
            };
        }

        // Handle s3:// URIs (AWS S3)
        if (uri.startsWith('s3://')) {
            const withoutSchema = uri.substring(5); // Remove 's3://'
            const firstSlashIndex = withoutSchema.indexOf('/');

            if (firstSlashIndex === -1) {
                return {
                    schema: 's3',
                    schemaLabel: 'S3',
                    bucket: withoutSchema,
                    path: '',
                    fullURI: uri,
                };
            }

            const bucket = withoutSchema.substring(0, firstSlashIndex);
            const path = withoutSchema.substring(firstSlashIndex + 1);

            return {
                schema: 's3',
                schemaLabel: 'S3',
                bucket: bucket,
                path: path,
                fullURI: uri,
            };
        }

        // Unknown schema or plain path
        return {
            schema: 'unknown',
            schemaLabel: 'Unknown',
            path: uri,
            fullURI: uri,
        };
    } catch (error) {
        console.error('Error parsing storage URI:', error);
        return null;
    }
};

const StorageURLField: React.FC<StorageURLFieldProps> = (props) => {
    const {
        source,
        showSchema = false,
        showBucket = false,
        showPath = false,
        showFullURI = false,
    } = props;

    const record = useRecordContext(props);

    if (!record || !source || !record[source]) {
        return null;
    }

    const uri = record[source] as string;
    const parsed = parseStorageURI(uri);

    if (!parsed) {
        return <Typography variant="body2" color="text.secondary">Invalid URI</Typography>;
    }

    // If showFullURI is true, just show the full URI
    if (showFullURI || (!showSchema && !showBucket && !showPath)) {
        return (
            <Tooltip title={parsed.fullURI}>
                <Typography
                    variant="body2"
                    sx={{
                        fontFamily: 'monospace',
                        fontSize: '0.85rem',
                        wordBreak: 'break-all',
                    }}
                >
                    {parsed.fullURI}
                </Typography>
            </Tooltip>
        );
    }

    return (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>

            {showSchema && (
                <Typography>{parsed.schemaLabel}</Typography>
            )}

            {showBucket && parsed.bucket && (
                <Typography>{parsed.bucket}</Typography>
            )}

            {showPath && parsed.path && (
                <Tooltip title={parsed.fullURI}>
                    <Typography
                        variant="body2"
                        sx={{
                            fontFamily: 'monospace',
                            fontSize: '0.85rem',
                            maxWidth: '400px',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                        }}
                    >
                        {parsed.path}
                    </Typography>
                </Tooltip>
            )}
        </Box>
    );
};

StorageURLField.displayName = 'StorageURLField';

export default StorageURLField;
