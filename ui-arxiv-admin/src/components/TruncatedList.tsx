import React from 'react';
import { Typography } from '@mui/material';

interface TruncatedListProps {
    text?: string;
    maxItems?: number;
    separator?: string;
    className?: string;
    variant?: 'body1' | 'body2' | 'caption' | 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 'subtitle1' | 'subtitle2' | 'overline' | 'inherit';
    component?: React.ElementType;
}

export const TruncatedList: React.FC<TruncatedListProps> = ({
    text = '',
    maxItems = 3,
    separator = ',',
    className,
    variant = 'body1',
    component = 'span'
}) => {
    if (!text || text.trim() === '') {
        return null;
    }

    // Split by separator and trim whitespace from each element
    const items = text.split(separator).map(item => item.trim()).filter(item => item !== '');

    if (items.length === 0) {
        return null;
    }

    // If we have fewer items than maxItems, show all
    if (items.length <= maxItems) {
        return (
            <Typography variant={variant} component={component} className={className}>
                {items.join(', ')}
            </Typography>
        );
    }

    // Show first maxItems and indicate how many more
    const visibleItems = items.slice(0, maxItems);
    const remainingCount = items.length - maxItems;

    return (
        <Typography variant={variant} component={component} className={className}>
            {visibleItems.join(', ')}, and {remainingCount} more
        </Typography>
    );
};