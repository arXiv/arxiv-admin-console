import React from 'react';
import { useRecordContext, FieldProps } from 'react-admin';
import Chip from '@mui/material/Chip';

const DocumentFileTypeField: React.FC<FieldProps> = (props) => {
    const record = useRecordContext(props);

    if (!record) {
        return null;
    }

    // Determine file type from file_name or id
    let fileType = 'unknown';
    const fileName = record.file_name || record.id || '';

    if (fileName.endsWith('.abs')) {
        fileType = 'abs';
    } else if (fileName.endsWith('.outcome.tar.gz')) {
        fileType = 'outcome';
    } else if (fileName.endsWith('.gz') || fileName.endsWith('.tar')) {
        fileType = 'source';
    } else if (fileName.endsWith('.pdf')) {
        fileType = 'PDF';
    }

    const getChipColor = (type: string): 'primary' | 'secondary' | 'default' => {
        switch (type) {
            case 'abs':
                return 'primary';
            case 'source':
                return 'primary';
            case 'outcome':
                return 'secondary';
            case 'PDF':
                return 'secondary';
            default:
                return 'default';
        }
    };

    return (
        <Chip
            label={fileType.toUpperCase()}
            size="small"
            color={getChipColor(fileType)}
            sx={{ fontWeight: 600 }}
        />
    );
};

DocumentFileTypeField.displayName = 'DocumentFileTypeField';

export default DocumentFileTypeField;
