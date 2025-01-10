import { useMediaQuery } from '@mui/material';
import {
    List,
    SimpleList,
    Datagrid,
    TextField,
    EmailField,
    BooleanField,
    SortPayload,
    NumberInput,
    useRecordContext,
    Edit,
    SimpleForm,
    TextInput,
    ReferenceInput,
    Create,
    Filter,
    BooleanInput,
    DateField,
    ReferenceField,
    NumberField,
    DateInput, useListContext, SelectInput
} from 'react-admin';

import { addDays } from 'date-fns';

import React from "react";
/*
    endorser_id: Optional[int] # Mapped[Optional[int]] = mapped_column(ForeignKey('tapir_users.user_id'), index=True)
    endorsee_id: int # Mapped[int] = mapped_column(ForeignKey('tapir_users.user_id'), nullable=False, index=True, server_default=FetchedValue())
    archive: str #  mapped_column(String(16), nullable=False, server_default=FetchedValue())
    subject_class: str # Mapped[str] = mapped_column(String(16), nullable=False, server_default=FetchedValue())
    flag_valid: int # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    type: str | None # Mapped[Optional[Literal['user', 'admin', 'auto']]] = mapped_column(Enum('user', 'admin', 'auto'))
    point_value: int # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    issued_when: int # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    request_id: int | None # Mapped[Optional[int]] = mapped_column(ForeignKey('arXiv_ownership_requests.request_id'), index=True)
 */

const presetOptions = [
    { id: 'last_1_day', name: 'Last 1 Day' },
    { id: 'last_7_days', name: 'Last 7 Days' },
    { id: 'last_28_days', name: 'Last 28 Days' },
];

const calculatePresetDates = (preset: string) => {
    const today = new Date();
    switch (preset) {
        case 'last_1_day':
            return { startDate: addDays(today, -1), endDate: today };
        case 'last_7_days':
            return { startDate: addDays(today, -7), endDate: today };
        case 'last_28_days':
            return { startDate: addDays(today, -28), endDate: today };
        default:
            return { startDate: null, endDate: null };
    }
};

const OwnershipFilter = (props: any) => {
    const { setFilters, filterValues } = useListContext();
    const handlePresetChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const { startDate, endDate } = calculatePresetDates(event.target.value);
        setFilters({
            ...filterValues,
            startDate: startDate ? startDate.toISOString().split('T')[0] : '',
            endDate: endDate ? endDate.toISOString().split('T')[0] : '',
        });
    };

    return (
        <Filter {...props}>
            <SelectInput
                label="Preset Date Range"
                source="preset"
                choices={presetOptions}
                onChange={(event) => handlePresetChange(event as React.ChangeEvent<HTMLSelectElement>)}
                alwaysOn
            />
            <DateInput label="Start Date" source="start_date" />
            <DateInput label="End Date" source="end_date" />
            <BooleanInput label="Valid" source="flag_valid" />
        </Filter>
    );
};


export const OwnershipList = () => {
    const sorter: SortPayload = {field: 'ownership_id', order: 'ASC'};
    const isSmall = useMediaQuery<any>(theme => theme.breakpoints.down('sm'));
    return (
        <List filters={<OwnershipFilter />}>
            {isSmall ? (
                <SimpleList
                    primaryText={record => record.name}
                    secondaryText={record => record.ownershipname}
                    tertiaryText={record => record.email}
                />
            ) : (
                <Datagrid rowClick="show" sort={sorter}>
                    <ReferenceField source="endorsee_id" reference="users" label={"Endorsee"}
                                    link={(record, reference) => `/${reference}/${record.id}`} >
                        <TextField source={"last_name"} />
                        {", "}
                        <TextField source={"first_name"} />
                    </ReferenceField>

                    <ReferenceField source="endorser_id" reference="users" label={"Endorser"}
                                    link={(record, reference) => `/${reference}/${record.id}`} >
                        <TextField source={"last_name"} />
                        {", "}
                        <TextField source={"first_name"} />
                    </ReferenceField>

                    <TextField source="archive" />

                    <TextField source="subject_class" />
                    <BooleanField source="flag_valid" label={"Valid"} FalseIcon={null} />

                    <TextField source="type" />
                    <NumberField source="point_value" label={"Point"} />
                    <DateField source="issued_when" label={"Issued"} />

                    <ReferenceField source="request_id" reference="ownership_requests" label={"Request"}
                                    link={(record, reference) => `/${reference}/${record.id}`} >
                        Show
                    </ReferenceField>
                </Datagrid>
            )}
        </List>
    );
};


const OwnershipTitle = () => {
    const record = useRecordContext();
    return <span>Ownership {record ? `"${record.last_name}, ${record.first_name}" - ${record.email}` : ''}</span>;
};

export const OwnershipEdit = () => (
    <Edit title={<OwnershipTitle />}>
        <SimpleForm>
            <ReferenceField source="endorsee_id" reference="users" label={"Endorsee"}
                            link={(record, reference) => `/${reference}/${record.id}`} >
                <TextField source={"last_name"} />
                {", "}
                <TextField source={"first_name"} />
            </ReferenceField>

            <ReferenceField source="endorser_id" reference="users" label={"Endorser"}
                            link={(record, reference) => `/${reference}/${record.id}`} >
                <TextField source={"last_name"} />
                {", "}
                <TextField source={"first_name"} />
            </ReferenceField>

            <TextInput source="archive" />

            <TextInput source="subject_class" />
            <BooleanInput source="flag_valid" label={"Valid"} />

            <TextInput source="type" />
            <NumberInput source="point_value" label={"Point"} />
            <DateInput source="issued_when" label={"Issued"} />

            <ReferenceField source="request_id" reference="ownership_request" label={"Request"}
                            link={(record, reference) => `/${reference}/${record.id}`} >
            </ReferenceField>
        </SimpleForm>
    </Edit>
);

export const OwnershipCreate = () => (
    <Create>
        <SimpleForm>
            <ReferenceField source="endorsee_id" reference="users" label={"Endorsee"}
                            link={(record, reference) => `/${reference}/${record.id}`} >
                <TextField source={"last_name"} />
                {", "}
                <TextField source={"first_name"} />
            </ReferenceField>

            <ReferenceField source="endorser_id" reference="users" label={"Endorser"}
                            link={(record, reference) => `/${reference}/${record.id}`} >
                <TextField source={"last_name"} />
                {", "}
                <TextField source={"first_name"} />
            </ReferenceField>

            <TextInput source="archive" />

            <TextInput source="subject_class" />
            <BooleanInput source="flag_valid" label={"Valid"}/>

            <TextInput source="type" />
            <NumberInput source="point_value" label={"Point"} />
            <DateInput source="issued_when" label={"Issued"} />

        </SimpleForm>
    </Create>
);


