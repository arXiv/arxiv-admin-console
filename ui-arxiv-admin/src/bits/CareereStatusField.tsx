
import React from 'react';
import {useRecordContext, FieldProps, TextField} from 'react-admin';

interface CareerStatusFieldProps extends FieldProps {
    record?: any;
}

const CareerStatusField: React.FC<CareerStatusFieldProps> = (props) => {
    const literals = ["Unknown", "Staff", "Professor", "Post Doc", "Grad Student", "Other"];
    const record = useRecordContext();
    const { source } = props;
    // console.log("CareerStatusField source: " + source);
    let careerStatus = 0;
    if (record && !source)
        careerStatus = record[source];
    const customRecord = { ...record, [source]: literals[careerStatus]};
    return (<TextField {...props} record={customRecord} />);
};

export default CareerStatusField;