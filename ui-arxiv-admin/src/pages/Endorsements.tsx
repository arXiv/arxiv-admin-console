import { ReactNode } from 'react';
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
    DateInput, useListContext, SelectInput, SelectField,
    NullableBooleanInput
} from 'react-admin';

import React from "react";
import CategoryField from "../bits/CategoryField";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Tooltip from '@mui/material/Tooltip';

/*
    endorser_id: Optional[int] # Mapped[Optional[int]] = mapped_column(ForeignKey('tapir_users.user_id'), index=True)
    endorsee_id: int # Mapped[int] = mapped_column(ForeignKey('tapir_users.user_id'), nullable=False, index=True, server_default=FetchedValue())
    archive: str #  mapped_column(String(16), nullable=False, server_default=FetchedValue())
    subject_class: str # Mapped[str] = mapped_column(String(16), nullable=False, server_default=FetchedValue())
    flag_valid: int # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    type: str | None # Mapped[Optional[Literal['user', 'admin', 'auto']]] = mapped_column(Enum('user', 'admin', 'auto'))
    point_value: int # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    issued_when: int # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    request_id: int | None # Mapped[Optional[int]] = mapped_column(ForeignKey('arXiv_endorsement_requests.request_id'), index=True)

 */

const presetOptions = [
    { id: 'last_1_day', name: 'Last 1 Day' },
    { id: 'last_7_days', name: 'Last 7 Days' },
    { id: 'last_28_days', name: 'Last 28 Days' },
];

const endorsementTypeOptions = [
    { id: 'user', name: 'By User' },
    { id: 'admin', name: 'By Admin' },
    { id: 'auto', name: 'Auto' },
];


const EndorsementFilter = (props: any) => {
    const { setFilters, filterValues } = useListContext();
    const handlePresetChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const preset_value = event?.target.value;
        setFilters({
            ...filterValues,
            preset: preset_value,
        });
    };

    const handleEndorsementTypeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const et_value = event?.target.value;
        setFilters({
            ...filterValues,
            "type": et_value,
        });
    };


    return (
        <Filter {...props}>
            <SelectInput
                label="Preset Date Range"
                source="preset"
                choices={presetOptions}
                onChange={(event) => handlePresetChange(event as React.ChangeEvent<HTMLSelectElement>)}
            />
            <SelectInput
                label="Endorsement Type"
                source="type"
                choices={endorsementTypeOptions}
                onChange={(event) => handleEndorsementTypeChange(event as React.ChangeEvent<HTMLSelectElement>)}
                alwaysOn
            />

            <NullableBooleanInput label="Positive" source="positive_endorsement" alwaysOn />
            <TextInput label={"Name"} source={"endorsee_name"} alwaysOn size={"small"} />
            <TextInput label={"Email"} source={"endorsee_email"} alwaysOn />
            <TextInput label={"Category"} source={"category"} alwaysOn />

            <DateInput label="Start Date" source="start_date" />
            <DateInput label="End Date" source="end_date" />
            <BooleanInput label="Valid" source="flag_valid" />
            <BooleanInput label="Flagged" source="by_suspct" />
        </Filter>
    );
};

const WithTooltip = ({ children }: { children: ReactNode }) => {
    const record = useRecordContext();
    if (!record) return null;

    return (
        <Tooltip title={record.comment || ''} arrow placement="top">
            <span>{children}</span>
        </Tooltip>
    );
};


export const EndorsementList = () => {
    const sorter: SortPayload = {field: 'endorsement_id', order: 'ASC'};
    const isSmall = useMediaQuery<any>(theme => theme.breakpoints.down('sm'));
    return (
        <List
            filters={<EndorsementFilter />}
            filterDefaultValues={{
                type: "user",
                positive_endorsement: false
            }}
            sort={{ field: 'id', order: 'DESC' }}
        >
            {isSmall ? (
                <SimpleList
                    primaryText={record => record.name}
                    secondaryText={record => record.endorsementname}
                    tertiaryText={record => record.email}
                />
            ) : (
                <Datagrid rowClick="edit" >
                    <WithTooltip>
                        <NumberField source={"id"} />
                    </WithTooltip>
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

                    <CategoryField sourceCategory="archive" sourceClass="subject_class" source="id" label="Category" />
                    <BooleanField source="flag_valid" label={"Valid"} FalseIcon={null} />

                    <TextField source="type" />
                    <NumberField source="point_value" label={"Point"} />
                    <DateField source="issued_when" label={"Issued"} />

                    <ReferenceField source="request_id" reference="endorsement_requests" label={"Request"}
                                    link={(record, reference) => `/${reference}/${record.id}`} >
                        Show
                    </ReferenceField>
                </Datagrid>
            )}
        </List>
    );
};


const EndorsementTitle = () => {
    const record = useRecordContext();
    if (!record) return null;
    const action = record.positive_endorsement ? " trusts " : " dosen't trust ";

    const endorser = record["type"] === "user" ? (
        <ReferenceField source="endorser_id" reference="users" label={"Endorser"}
                        link={(record, reference) => `/${reference}/${record.id}`} >
            <TextField source={"first_name"} />
            {" "}
            <TextField source={"last_name"} />
        </ReferenceField>
    ) : (
        record["type"] === "admin" ? "EUST" : "arXiv system"
    );

    return (
        <Box sx={{ flex: 8, display: 'flex', flexDirection: 'row', gap: 1, alignItems: 'baseline'}} >
            {endorser}
            {action}
            <ReferenceField source="endorsee_id" reference="users" label={"Endorsee"}
                            link={(record, reference) => `/${reference}/${record.id}`} >
                <TextField source={"first_name"} />
                {" "}
                <TextField source={"last_name"} />
            </ReferenceField>
            {" for "}
            <CategoryField sourceCategory="archive" sourceClass="subject_class" source="id" label="Category" />
        </Box>
    )

};

export const EndorsementEdit = () => (
    <Edit title={ <EndorsementTitle />}  >
        <SimpleForm>
            <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gridTemplateRows: 'repeat(2, 1fr)',
                height: '100%',
                minWidth: '60%',
                gap: '0px 8px',
            }}>
                <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                    <Typography>{"ID: "}</Typography>
                    <NumberField source="id" />
                </Box>

                <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                    <Typography>{"Request ID: "}</Typography>
                    <ReferenceField source="request_id" reference="endorsement_requests" label={"Endorsement Request"}
                                    link={(record, reference) => `/${reference}/${record.id}`} >
                        <NumberField source={"id"} />
                    </ReferenceField>
                </Box>

                <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                    <Typography>{"Category: "}</Typography>
                    <CategoryField sourceCategory="archive" sourceClass="subject_class" source="id" label="Category" />
                </Box>

                <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                    <Typography>{"Issued on: "}</Typography>
                    <DateField source="issued_when"/>
                </Box>


                <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                    <Typography>{"Endorser: "}</Typography>

                    <ReferenceField source="endorser_id" reference="users" label={"Endorser"}
                                link={(record, reference) => `/${reference}/${record.id}`} >
                        <TextField source={"last_name"} />
                        {", "}
                        <TextField source={"first_name"} />
                    </ReferenceField>
                </Box>

                <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                    <Typography>{"Session ID: "}</Typography>
                    <NumberField source="session_id"/>
                </Box>

                <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                    <Typography>{"Endorsee: "}</Typography>
                    <ReferenceField source="endorsee_id" reference="users" label={"Endorsee"}
                                    link={(record, reference) => `/${reference}/${record.id}`} >
                        <TextField source={"last_name"} />
                        {", "}
                        <TextField source={"first_name"} />
                    </ReferenceField>
                </Box>

                <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                    <Typography>{"Remote Hostname: "}</Typography>
                    <TextField source={"remote_host"} />
                </Box>

                <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                    <BooleanInput source="flag_valid" label={"Valid"} size={"small"} />
                    <BooleanInput source="positive_endorsement" label={"Positive"} size={"small"} />
                    <SelectField source="type" choices={endorsementTypeOptions}  />
                </Box>

                <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                    <Typography>{"Remote Address: "}</Typography>
                    <TextField source={"remote_addr"} />
                </Box>

                <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                    <Typography>{"Knows Presonally: "}</Typography>
                    <BooleanField source="flag_knows_personally"/>
                    <Typography>{"Seen Paper: "}</Typography>
                    <BooleanField source="flag_seen_paper"/>
                </Box>

                <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                    <Typography>{"Tracking Cookie: "}</Typography>
                    <TextField source="tracking_cookie"/>
                </Box>
            </div>
            <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                <Typography>{"Comment: "}</Typography>
                <TextField source={"comment"} />
            </Box>
        </SimpleForm>
    </Edit>
);

export const EndorsementCreate = () => (
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


