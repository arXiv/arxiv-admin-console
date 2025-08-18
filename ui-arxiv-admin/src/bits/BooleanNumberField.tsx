import React from 'react';
import {useRecordContext, BooleanFieldProps, BooleanField} from 'react-admin';

const BooleanNumberField: React.FC<BooleanFieldProps> = (props) => {
    const record = useRecordContext();
    const { source } = props;
    let value = undefined;
    if (record && source && record[source] !== undefined)
        value = record[source];
    if (value === 0) value = false;
    if (value === 1) value = true;
    const customRecord = { ...record, [source]: value};
    return (<BooleanField {...props} record={customRecord} />);
};

export default BooleanNumberField;
