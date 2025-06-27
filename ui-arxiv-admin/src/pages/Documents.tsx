import {Card, CardContent, Grid, ToggleButton, Typography, useMediaQuery, Switch, FormControlLabel} from '@mui/material';
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
    SimpleShowLayout,
    Show,
    DateInput, useListContext, SelectInput, useShowContext
} from 'react-admin';

import { addDays } from 'date-fns';

import React from "react";
import CircularProgress from "@mui/material/CircularProgress";
import CategoryField from "../bits/CategoryField";
import SubmissionCategoriesField from "../bits/SubmissionCategoriesField";
/*
    endorser_id: Optional[int] # Mapped[Optional[int]] = mapped_column(ForeignKey('tapir_users.user_id'), index=True)
    endorsee_id: int # Mapped[int] = mapped_column(ForeignKey('tapir_users.user_id'), nullable=False, index=True, server_default=FetchedValue())
    archive: str #  mapped_column(String(16), nullable=False, server_default=FetchedValue())
    subject_class: str # Mapped[str] = mapped_column(String(16), nullable=False, server_default=FetchedValue())
    flag_valid: int # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    type: str | None # Mapped[Optional[Literal['user', 'admin', 'auto']]] = mapped_column(Enum('user', 'admin', 'auto'))
    point_value: int # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    issued_when: int # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    request_id: int | None # Mapped[Optional[int]] = mapped_column(ForeignKey('arXiv_document_requests.request_id'), index=True)

 */

const presetOptions = [
    { id: 'last_1_day', name: 'Last 1 Day' },
    { id: 'last_7_days', name: 'Last 7 Days' },
    { id: 'last_28_days', name: 'Last 28 Days' },
    { id: 'last_366_days', name: 'Last 366 Days' },
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
        case 'last_366_days':
            return { startDate: addDays(today, -366), endDate: today };
        default:
            return { startDate: null, endDate: null };
    }
};

const DocumentFilter = (props: any) => {
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
            <TextInput label="arXiv ID" source="paper_id" alwaysOn />
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


const ShowArxivPdf = () => {
    const record = useShowContext();

    if (record.isFetching)
        return <CircularProgress />;

    const paper_id = record?.record?.paper_id;

    return (
        paper_id ? (
            <Grid item xs={12}  style={{ display: 'flex', flexDirection: 'column', height: '75vh' }}>
                <iframe
                    src={`https://arxiv.org/pdf/${paper_id}`}
                    title="PDF Document"
                    style={{ border: 'none',
                        width:"100%",
                        flex: 1,}}
                />
            </Grid>
        )
            : null
    );
}

export const DocumentShow = () => {
    const [showPdf, setShowPdf] = React.useState(true);

    return (
    <Show>
        <Grid container>
            <Grid container item xs={12}>
                <Grid item xs={2}>
                    {" "}
                </Grid>
                <Grid item xs={10}>
                    <TextField source="paper_id"/>
                    {" / "}
                    <TextField source="id"/>
                    {" ("}
                    <ReferenceField source="last_submission_id" reference="submissions" label={"Submission"}>
                        <TextField source="id"/>
                    </ReferenceField>
                    {")"}
                </Grid>
            </Grid>
            <Grid container item xs={12}>
                <Grid item xs={2}>
                    From:
                </Grid>
                <Grid item xs={10}>
                    <ReferenceField source="submitter_id" reference="users" label={"Submitter"}
                                    link={(record, reference) => `/${reference}/${record.id}`} >
                        <TextField source={"last_name"} />
                        {", "}
                        <TextField source={"first_name"} />
                        {" <"}
                        <EmailField source={"email"} />
                        {">"}
                    </ReferenceField>
                </Grid>
            </Grid>

            <Grid container item xs={12}>
                <Grid item xs={2}>
                    Submitter Email:
                </Grid>
                <Grid item xs={10}>
                    <EmailField source="submitter_email" />
                </Grid>
            </Grid>

            <Grid container item xs={12}>
                <Grid item xs={2}>
                    Submission date:
                </Grid>
                <Grid item xs={3}>
                    <DateField source="dated" />
                </Grid>
                <Grid item xs={2}>
                    Created:
                </Grid>
                <Grid item xs={3}>
                    <DateField source="created" />
                </Grid>
            </Grid>

            <Grid container item xs={12}>
                <Grid item xs={2}>
                    Title:
                </Grid>
                <Grid item xs={10}>
                    <TextField source="title" />
                </Grid>
            </Grid>

            <Grid container item xs={12}>
                <Grid item xs={2}>
                    Authors:
                </Grid>
                <Grid item xs={10}>
                    <TextField source="authors" />
                </Grid>
            </Grid>

            <Grid container item xs={12}>
                <Grid item xs={2}>
                    Categories:
                </Grid>
                <Grid item xs={10}>
                    <SubmissionCategoriesField />
                </Grid>
            </Grid>

            <Grid container item xs={12}>
                <Grid item xs={2}>
                    License:
                </Grid>
                <Grid item xs={10}>
                    <ReferenceField source="last_submission_id" reference="submissions" label={"Licence"} link={false}>
                        <TextField source="license" />
                    </ReferenceField>
                </Grid>
            </Grid>

            <Grid container item xs={12}>
                <Grid item xs={2}>
                    Abstract:
                </Grid>
                <Grid item xs={10}>
                    <ReferenceField source="last_submission_id" reference="submissions" label={"Abstract"} link={false}>
                        <TextField source="abstract" />
                    </ReferenceField>
                </Grid>
            </Grid>

            <Grid container item xs={12}>
                <FormControlLabel
                    control={
                        <Switch checked={showPdf} onChange={() => setShowPdf(!showPdf)} inputProps={{ 'aria-label': 'controlled'}} />
                    }
                    label="PDF"/>
            </Grid>
            <Grid container item xs={12}>
                {
                    showPdf ? <ShowArxivPdf /> : null
                }
            </Grid>
        </Grid>
    </Show>
)};

export const DocumentList = () => {
    const sorter: SortPayload = {field: 'document_id', order: 'ASC'};
    const isSmall = useMediaQuery<any>(theme => theme.breakpoints.down('sm'));
    return (
        <List filters={<DocumentFilter />}>
            {isSmall ? (
                <SimpleList
                    primaryText={record => record.name}
                    secondaryText={record => record.documentname}
                    tertiaryText={record => record.email}
                />
            ) : (
                <Datagrid rowClick="show" sort={sorter}>
                    <DateField source="dated" label={"Date"}/>

                    <TextField source="paper_id" label={"Paper ID"}/>

                    <TextField source="title" label={"Title"}/>

                    <ReferenceField source="submitter_id" reference="users" label={"Submitter"}
                                    link={(record, reference) => `/${reference}/${record.id}`} >
                        <TextField source={"last_name"} />
                        {", "}
                        <TextField source={"first_name"} />
                    </ReferenceField>

                    <TextField source="authors" />
                    <TextField source="abs_categories" label={"Categories"}/>
                    <DateField source="created" label={"Created"}/>

                </Datagrid>
            )}
        </List>
    );
};


const DocumentTitle = () => {
    const record = useRecordContext();
    return <span>Document {record ? `${record.paper_id}: ${record.title} by ${record.authors}` : ''}</span>;
};

export const DocumentEdit = () => (
    <Edit title={<DocumentTitle />}>
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

            <ReferenceField source="request_id" reference="document_request" label={"Request"}
                            link={(record, reference) => `/${reference}/${record.id}`} >
            </ReferenceField>
        </SimpleForm>
    </Edit>
);

export const DocumentCreate = () => (
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


