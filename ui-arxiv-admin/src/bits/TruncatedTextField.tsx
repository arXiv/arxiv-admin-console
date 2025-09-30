import React from 'react';
import { useRecordContext } from 'react-admin';
import Typography from '@mui/material/Typography';

interface TruncatedTextFieldProps {
    source: string;
    label?: string;
    maxItems?: number;
    separator?: string;
    emptyText?: string;
}

const TruncatedTextField: React.FC<TruncatedTextFieldProps> = ({
    source,
    label,
    maxItems = 3,
    separator = ',',
    emptyText = ''
}) => {
    const record = useRecordContext();

    if (!record || !record[source]) {
        return <span>{emptyText}</span>;
    }

    const text = record[source];
    if (!text || text.trim() === '') {
        return <span>{emptyText}</span>;
    }

    // Split by separator and trim whitespace from each element
    const items = text.split(separator).map(item => item.trim()).filter(item => item !== '');

    if (items.length === 0) {
        return <span>{emptyText}</span>;
    }

    // If we have fewer items than maxItems, show all
    if (items.length <= maxItems) {
        return (
            <Typography variant="body2" component="span">
                {items.join(', ')}
            </Typography>
        );
    }

    // Calculate remaining items
    const remainingCount = items.length - maxItems;

    // If only "1 more", don't truncate - show all items
    if (remainingCount === 1) {
        return (
            <Typography variant="body2" component="span">
                {items.join(', ')}
            </Typography>
        );
    }

    // Show first maxItems and indicate how many more (only if 2 or more)
    const visibleItems = items.slice(0, maxItems);

    return (
        <Typography variant="body2" component="span">
            {visibleItems.join(', ')}, and {remainingCount} more
        </Typography>
    );
};

export default TruncatedTextField;