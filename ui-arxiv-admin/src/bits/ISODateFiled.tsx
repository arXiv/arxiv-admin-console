/*
import React from 'react';

import { DateField, DateFieldProps } from 'react-admin';

interface ISODateFieldProps extends Omit<DateFieldProps, 'transform'> {
    source: string;
    showTime?: boolean;
}


 * A DateField component that formats dates in ISO format (YYYY-MM-DD)
 * with optional time display based on the showTime prop

const ISODateField: React.FC<ISODateFieldProps> = ({
                                                       source,
                                                       showTime = false,
                                                       ...props
                                                   }) => {
    return (
        <DateField
            source={source}
            showTime={showTime}
            locales="en-CA" // Canadian English uses YYYY-MM-DD format
            options={{
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                ...(showTime ? {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: false // Use 24-hour format
                } : {})
            }}
            {...props}
        />
    );
};

export default ISODateField;
*/

import React from 'react';
import { TextField, TextFieldProps, useRecordContext } from 'react-admin';

interface ISODateFieldProps extends Omit<TextFieldProps, 'source'> {
    source: string;
    showTime?: boolean;
}

const ISODateField: React.FC<ISODateFieldProps> = ({ source, showTime = false, ...props }) => {
    const record = useRecordContext();

    const formatValue = (value: any): string | null => {
        if (!value) return null;
        try {
            const date = new Date(value);
            if (showTime) {
                return date.toISOString().replace('T', ' ').replace('Z', '');
            } else {
                return date.toISOString().split('T')[0]; // Returns YYYY-MM-DD
            }
        } catch (error) {
            console.warn('Invalid date value:', value);
            return value?.toString() || null;
        }
    };

    const formattedValue = record ? formatValue(record[source]) : null;

    return (
        <TextField
            source={source}
            record={{ ...record, [source]: formattedValue }}
            {...props}
        />
    );
};

export default ISODateField;
