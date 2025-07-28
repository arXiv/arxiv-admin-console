import React from 'react';
import { TextField, TextFieldProps, useRecordContext } from 'react-admin';
import Box from '@mui/material/Box';

interface ISODateFieldProps extends Omit<TextFieldProps, 'source'> {
    source: string;
    showTime?: boolean;
    minWidth?: string | number;
}

/**
 * Display a date in ISO format (YYYY-MM-DD) with optional time
 * 
 * @example
 * // Without time
 * <ISODateField source="created_at" />
 * // With time
 * <ISODateField source="published_at" showTime />
 */
const ISODateField: React.FC<ISODateFieldProps> = ({ 
    source, 
    showTime = false, 
    minWidth = showTime ? '11rem' : '5rem',
    ...props 
}) => {
    const record = useRecordContext();

    const formatValue = (value: any): string | null => {
        if (!value) return null;
        try {
            const date = new Date(value);
            if (isNaN(date.getTime())) {
                console.warn(`Invalid date value for ${source}: ${value}`);
                return value?.toString() || null;
            }
            
            if (showTime) {
                // Format with time: YYYY-MM-DD HH:MM:SS
                return date.toISOString().replace('T', ' ').slice(0, 19);
            } else {
                // Format date only: YYYY-MM-DD
                return date.toISOString().split('T')[0];
            }
        } catch (error) {
            console.error(`Error formatting date for ${source}:`, error);
            return value?.toString() || null;
        }
    };

    const formattedValue = record ? formatValue(record[source]) : null;

    return (
        <Box sx={{ minWidth, display: 'inline-block' }}>
            <TextField
                source={source}
                record={{ ...record, [source]: formattedValue }}
                {...props}
            />
        </Box>
    );
};

export default ISODateField;