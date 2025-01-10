import {Grid, ToggleButton, useMediaQuery} from '@mui/material';
import {
    BooleanField,
    BooleanInput,
    Create,
    Datagrid,
    DateField,
    DateInput,
    Edit,
    EmailField,
    Filter,
    List,
    NumberField,
    NumberInput,
    ReferenceField,
    ReferenceInput,
    SelectInput,
    SelectArrayInput,
    Show,
    SimpleForm,
    SimpleList,
    SortPayload,
    TextField,
    TextInput,
    useListContext,
    useRecordContext,
} from 'react-admin';


import LinkIcon from '@mui/icons-material/Link';


import { addDays } from 'date-fns';

import React, {useState} from "react";
import SubmissionStateField, {submissionStatusOptions} from "./bits/SubmissionStateField";
import {AdminLogs} from "./AdminLogs";
import CategoryInputField from "./bits/CategoryInputField";
import SubmissionCategoriesField, {CategoriesField, CategoryList} from "./bits/SubmissionCategoriesField";
import IsOkField from "./bits/IsOkField";

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

const SubmissionFilter = (props: any) => {
    const { setFilters, filterValues } = useListContext();
    const handlePresetChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const { startDate, endDate } = calculatePresetDates(event.target.value);
        setFilters({
            ...filterValues,
        });
    };

    return (
        <Filter {...props}>
            <NumberInput label="Submission ID" source="id" alwaysOn />
            <SelectArrayInput
                label="Status"
                source="submission_status"
                choices={submissionStatusOptions}
                alwaysOn
            />
            <DateInput label="Start Date" source="start_date" />
            <DateInput label="End Date" source="end_date" />
            <SelectInput
                label="Preset Date Range"
                source="preset"
                choices={presetOptions}
                onChange={(event) => handlePresetChange(event as React.ChangeEvent<HTMLSelectElement>)}
            />
            <BooleanInput label="Valid" source="flag_valid" />

        </Filter>
    );
};


export const SubmissionList = () => {
    const sorter: SortPayload = {field: 'submission_id', order: 'ASC'};
    const isSmall = useMediaQuery<any>(theme => theme.breakpoints.down('sm'));
    const defaultDates = calculatePresetDates('last_28_days');

    return (
        <List filters={<SubmissionFilter />}
              filterDefaultValues={{
                  start_date: defaultDates.startDate ? defaultDates.startDate.toISOString().split('T')[0] : '',
                  end_date: defaultDates.endDate ? defaultDates.endDate.toISOString().split('T')[0] : '',
                  submission_status: 1,
              }}
        >
            {isSmall ? (
                <SimpleList
                    primaryText={record => record.name}
                    secondaryText={record => record.submissionname}
                    tertiaryText={record => record.email}
                />
            ) : (
                <Datagrid rowClick="edit" sort={sorter}>
                    <TextField source="id" label="Submission ID"  textAlign="right" />
                    <CategoriesField source="submission_categories" />
                    <ReferenceField source="submitter_id" reference="users" label={"Submitter"}
                                    link={(record, reference) => `/${reference}/${record.id}/show`} >
                        <TextField source={"last_name"} />
                        {", "}
                        <TextField source={"first_name"} />
                    </ReferenceField>
                    <TextField source="title" />
                    <ReferenceField source="document_id" reference="documents" label={"Document"}
                                    link={(record, reference) => `/${reference}/${record.id}/show`} >
                        <LinkIcon />
                    </ReferenceField>
                    <SubmissionStateField source="status"/>
                    <IsOkField source="is_ok" label={"OK?"}/>
                </Datagrid>
            )}
        </List>
    );
};


const SubmissionTitle = () => {
    const record = useRecordContext();
    return <span>Submission {record ? `"${record.last_name}, ${record.first_name}" - ${record.email}` : ''}</span>;
};


export const SubmissionEdit = () => {
    const [showLogs, setShowLogs] = useState<boolean>(false);

    return(
<Grid container>
        <Grid item xs={12}>
            <Grid item xs={2} alignItems={"center"}>
                <ToggleButton value="showAdminLogs" selected={showLogs} onClick={() => setShowLogs(!showLogs)} >
                    {showLogs ? "Hide Admin Logs" : "Show Admin Logs"}
                </ToggleButton>
            </Grid>
        <Edit aside={<AdminLogs showLogs={showLogs} />}>
            <SimpleForm>
                <Grid container>
                    <Grid item xs={3}>
                        {"submit/"}
                        <TextField source="id" />
                    </Grid>
                    <Grid item xs={3}>
                        {"source format: "}
                        <TextField source="source_format" />
                        {" - "}
                        <NumberField source="source_size" />
                        {" bytes"}

                    </Grid>
                    <Grid item xs={2}>
                        <SelectInput source="status" choices={submissionStatusOptions} />
                    </Grid>
                    <Grid container item xs={12}>
                        <Grid item xs={2}>
                            User Identity
                        </Grid>
                        <Grid item xs={4}>
                            <ReferenceField source="submitter_id" reference="users" label={"Submitter"}
                                            link={(record, reference) => `/${reference}/${record.id}`} >
                                <TextField source={"last_name"} />
                                {", "}
                                <TextField source={"first_name"} />
                            </ReferenceField>
                        </Grid>
                        <Grid item xs={4}>
                            <ReferenceField source="submitter_id" reference="users" label={"Submitter"}>
                                <EmailField source={"email"} />
                            </ReferenceField>
                        </Grid>
                    </Grid>
                    <Grid container item xs={12}>
                        <Grid item xs={2}>
                            From
                        </Grid>
                        <Grid item xs={4}>
                            <TextInput source="submitter_name" />
                        </Grid>
                        <Grid item xs={4}>
                            <TextInput source="submitter_email" />
                        </Grid>
                    </Grid>

                    <Grid container item xs={12}>
                        <Grid item xs={2}>
                            Date created:
                        </Grid>
                        <Grid item xs={2}>
                            <DateField source="created" label="Created"/>
                        </Grid>
                        <Grid item xs={2}>
                            Date updated:
                        </Grid>
                        <Grid item xs={2}>
                            <DateField source="updated" />
                        </Grid>
                    </Grid>

                    <Grid container item xs={12}>
                        <Grid item xs={2}>
                            Categories:
                        </Grid>
                        <Grid item xs={10}>
                            <CategoryInputField source="id" sourceCategory="archive" sourceClass="subject_class" />
                        </Grid>
                    </Grid>

                    <Grid container item xs={12}>
                        <Grid item xs={2}>
                            Title
                        </Grid>
                        <Grid item xs={10}>
                            <TextInput source="title" />
                        </Grid>

                    </Grid>
                    <Grid container item xs={12}>
                        <Grid item xs={2}>
                            Authors
                        </Grid>
                        <Grid item xs={10}>
                            <TextInput source="authors" />
                        </Grid>

                    </Grid>

                    <Grid container item xs={12}>
                        <Grid item xs={2}>
                            Comments
                        </Grid>
                        <Grid item xs={10}>
                            <TextInput source="comments" />
                        </Grid>

                    </Grid>
                    <Grid container item xs={12}>
                        <Grid item xs={2}>
                            License
                        </Grid>
                        <Grid item xs={10}>
                            <TextField source="license" />
                        </Grid>

                    </Grid>
                    <Grid container item xs={12}>
                        <Grid item xs={2}>
                            Abstract
                        </Grid>
                        <Grid item xs={10}>
                            <TextInput source="abstract" multiline rows={20} />
                        </Grid>

                    </Grid>
                </Grid>
            </SimpleForm>
        </Edit>
        </Grid>
</Grid>
    );
}

export const SubmissionCreate = () => (
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

/*
 */

export const SubmissionShow = () => {
    return (
        <Show>
            <Grid container>
                <Grid container item xs={12}>
                    <Grid item xs={3}>
                        <TextField source="id"/>
                        {" / "}
                        <TextField source="document_id"/>
                    </Grid>
                    <Grid item xs={9}>
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
                        Submitter:
                    </Grid>
                    <Grid item xs={10}>
                        <ReferenceField source="submitter_id" reference="users" label={"Submitter"}
                                        link={(record, reference) => `/${reference}/${record.id}`} >
                            <TextField source={"last_name"} />
                            {", "}
                            <TextField source={"first_name"} />
                        </ReferenceField>
                    </Grid>
                </Grid>
                <Grid container item xs={12}>
                    <Grid item xs={2}>
                        Submission date:
                    </Grid>
                    <Grid item xs={3}>
                        <DateField source="submit_time" />
                    </Grid>
                    <Grid item xs={2}>
                        Release time:
                    </Grid>
                    <Grid item xs={3}>
                        <DateField source="release_time" />
                    </Grid>
                </Grid>

                <Grid container item xs={12}>
                    <Grid item xs={2}>
                        Comments
                    </Grid>
                    <Grid item xs={10}>
                        <TextField source="comments" />
                    </Grid>
                </Grid>

                <Grid container item xs={12}>
                    <Grid item xs={2}>
                        Abstract
                    </Grid>
                    <Grid item xs={10}>
                        <TextField source="abstract" />
                    </Grid>
                </Grid>
            </Grid>
        </Show>
    )};
