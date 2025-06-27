import React from 'react';
import { useRecordContext, FieldProps } from 'react-admin';
import Typography from '@mui/material/Typography';

const policyClassChoices = [
    { id: 0, name: 'Owner' },
    { id: 1, name: 'Admin' },
    { id: 2, name: 'Public user' },
    { id: 3, name: 'Legacy user' },
];

interface PolicyClassFieldProps extends FieldProps {
    // Add any additional props if needed
}

const PolicyClassField: React.FC<PolicyClassFieldProps> = (props) => {
    const { source } = props;
    const record = useRecordContext();

    if (!record || !source || record[source] === undefined) return null;

    const policyClass = record[source];
    const policyClassName = policyClassChoices.find(choice => choice.id === policyClass)?.name || `Unknown (${policyClass})`;

    return (
        <Typography component="span" variant="body2">
            {policyClassName}
        </Typography>
    );
};

export default PolicyClassField;
