
import React from 'react';
import {useRecordContext, FieldProps, TextField} from 'react-admin';

interface SubmissionStatusFieldProps extends FieldProps {
    record?: any;
}

export const submissionStatusOptions = [
    {"id": 0, "name": "Working" },
    {"id": 1, "name": "Submitted"},
    {"id": 2, "name": "On hold"},
    {"id": 3, "name": "Unused"},
    {"id": 4, "name": "Next"},
    {"id": 5, "name": "Processing"},
    {"id": 6, "name": "Needs_email"},
    {"id": 7, "name": "Published"},
    {"id": 8, "name": "Processing(submitting)"},
    {"id": 9, "name": "Removed"},
    {"id": 10, "name": "User deleted"},
    {"id": 19, "name": "Error state"},
    {"id": 20, "name": 'Deleted(working)'},
    {"id": 22, "name": 'Deleted(on hold)'},
    {"id": 25, "name": 'Deleted(processing)'},
    {"id": 27, "name": 'Deleted(published)'},
    {"id": 29, "name": "Deleted(removed)"},
    {"id": 30, "name": 'Deleted(user deleted)'},
];


const SubmissionStatusField: React.FC<SubmissionStatusFieldProps> = (props) => {
    const record = useRecordContext();
    const { source } = props;
    let submissionStatus = -1;
    if (record && source && record[source] !== undefined)
        submissionStatus = Number(record[source]);
    const customRecord = { ...record, [source]: submissionStatusOptions.find(entry => entry.id === submissionStatus)?.name || "unknown"};
    return (<TextField {...props} record={customRecord} />);
};

export default SubmissionStatusField;
