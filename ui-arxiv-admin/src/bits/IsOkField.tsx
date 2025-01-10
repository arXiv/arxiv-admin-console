import React from 'react';
import {useRecordContext, FieldProps, TextField} from 'react-admin';

const IsOkField: React.FC<FieldProps> = (props) => {
    const record = useRecordContext();
    const { source } = props;
    let ok = "?";
    if (record && source && record[source] !== undefined)
        if (record[source] !== null)
            ok = record[source] ? "OK" : "No"
    const customRecord = { ...record, [source]: ok};
    return (<TextField {...props} record={customRecord} />);
};

export default IsOkField;
