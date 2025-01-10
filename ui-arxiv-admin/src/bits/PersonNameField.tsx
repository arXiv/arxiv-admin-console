
import React from 'react';
import { useRecordContext, FieldProps } from 'react-admin';

interface UserNameFieldProps extends FieldProps {
}

const PersonNameField: React.FC<UserNameFieldProps> = () => {
    const record = useRecordContext<{ [key: string]: string }>();
    if (!record) return null;
    return (
        <span>
            {record.first_name} {record.last_name}{record.suffix_name ? ", " + record.suffix_name : ""}
        </span>
    );
};

export default PersonNameField;