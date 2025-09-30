import React from 'react';
import { useRecordContext } from 'react-admin';
import { Chip, Box, Tooltip } from '@mui/material';

interface EndorsementCandidate {
    id: number;
    category: string;
    document_count: number;
    latest: string;
}

interface EndorsementCategoriesFieldProps {
    source?: string;
    emptyText?: string;
}

const EndorsementCategoriesField: React.FC<EndorsementCategoriesFieldProps> = ({
    source = '',
    emptyText = 'None'
}) => {
    const record = useRecordContext();

    console.log("EndorsementCategoriesField record: " + JSON.stringify(record));

    if (!record ||(source && !record[source])) {
        return <span>{emptyText}</span>;
    }

    const endorsementData: EndorsementCandidate[] = source ? record[source] : record;

    if (!Array.isArray(endorsementData) || endorsementData.length === 0) {
        return <span>{emptyText}</span>;
    }

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    };

    return (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {endorsementData.map((item, index) => (
                <Tooltip
                    key={`${item.id}-${item.category}-${index}`}
                    title={
                        <div>
                            <div><strong>Category:</strong> {item.category}</div>
                            <div><strong>Document Count:</strong> {item.document_count}</div>
                            <div><strong>Latest Submission:</strong> {formatDate(item.latest)}</div>
                        </div>
                    }
                    placement="top"
                >
                    <Chip
                        label={`${item.category} (${item.document_count})`}
                        size="small"
                        variant="outlined"
                        sx={{ cursor: 'help' }}
                    />
                </Tooltip>
            ))}
        </Box>
    );
};

export default EndorsementCategoriesField;