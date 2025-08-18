import {Grid, ToggleButton, useMediaQuery} from '@mui/material';
import {
    BooleanInput,
    Create,
    Datagrid,
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

import {addDays} from 'date-fns';

import React, {useState} from "react";
import SubmissionStateField, {submissionStatusOptions} from "../bits/SubmissionStateField";
import {AdminLogs} from "./AdminLogs";
import CategoryInputField from "../bits/CategoryInputField";
// import SubmissionCategoriesField, {CategoriesField, CategoryList} from "../bits/SubmissionCategoriesField";
import IsOkField from "../bits/IsOkField";
// import {RuntimeContext} from "../RuntimeContext";
import ArxivCheckSubmissionLink from "../bits/ArxivCheckSubmissionLink";
import ISODateField from '../bits/ISODateFiled';

import {paths as adminApi, components as adminComponents} from "../types/admin-api";
import UserNameField from "../bits/UserNameField";
import CategoryField from "../bits/CategoryField";
import PrimaryCategoryField from "../bits/PirmaryCategoryField";
import AdminLogField from "../bits/AdminLogField";

type SubmissionModel = adminComponents['schemas']['SubmissionModel'];
type SubmissionType = adminComponents['schemas']['SubmissionType'];


const presetOptions = [
    {id: 'last_1_day', name: 'Last 1 Day'},
    {id: 'last_7_days', name: 'Last 7 Days'},
    {id: 'last_28_days', name: 'Last 28 Days'},
];

const calculatePresetDates = (preset: string) => {
    const today = new Date();
    switch (preset) {
        case 'last_1_day':
            return {startDate: addDays(today, -1), endDate: today};
        case 'last_7_days':
            return {startDate: addDays(today, -7), endDate: today};
        case 'last_28_days':
            return {startDate: addDays(today, -28), endDate: today};
        default:
            return {startDate: null, endDate: null};
    }
};

export const submissionTypeOptions = [
    {"id": "new", "name": "New"},
    {"id": "cross", "name": "Cross"},
    {"id": "jref", "name": "JRef"},
    {"id": "rep", "name": "Rep"},
    {"id": "wdr", "name": "Withdrawal"}
];


const SubmissionFilter = (props: any) => {
    const {setFilters, filterValues} = useListContext();
    const handlePresetChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        setFilters({
            ...filterValues,
        });
    };

    return (
        <Filter {...props}>
            <NumberInput label="Submission ID" source="id" alwaysOn sx={{width: '8rem'}}/>
            <SelectInput
                label="Status"
                source="submission_status"
                choices={submissionStatusOptions}
                alwaysOn
            />
            <SelectArrayInput
                label="S-Type"
                source="type"
                choices={submissionTypeOptions}
                alwaysOn
            />
            <DateInput label="Start Date" source="start_date"/>
            <DateInput label="End Date" source="end_date"/>
            <SelectInput
                label="Preset Date Range"
                source="preset"
                choices={presetOptions}
                onChange={(event) => handlePresetChange(event as React.ChangeEvent<HTMLSelectElement>)}
            />
            <BooleanInput label="Valid" source="flag_valid"/>

        </Filter>
    );
};


export const SubmissionList = () => {
    const defaultDates = calculatePresetDates('last_28_days');

    return (
        <List filters={<SubmissionFilter/>}
              filterDefaultValues={{
                  submission_status: [],
              }}
        >
            <Datagrid rowClick={false} bulkActionButtons={false}>
                <ReferenceField reference={"submissions"} source={"id"} link={"edit"}>
                    <TextField source="id" label="ID" textAlign="right"/>
                </ReferenceField>
                <ISODateField source={"submit_time"} showTime/>
                <TextField source="type" label="Type" textAlign="right"/>
                <PrimaryCategoryField source="submission_categories" label="Cat"/>
                <ReferenceField source="submitter_id" reference="users" label={"Submitter"}
                                link={(record, reference) => `/${reference}/${record.id}/show`}>
                    <UserNameField withUsername/>
                </ReferenceField>
                <ArxivCheckSubmissionLink source="title"/>
                <ReferenceField source="document_id" reference="documents" label={"Doc"}
                                link={(record, reference) => `/${reference}/${record.id}/show`}>
                    <TextField source={"paper_id"}/>
                </ReferenceField>
                <AdminLogField source="id" label={"Log"}/>
                <IsOkField source="is_ok" label={"OK?"}/>
            </Datagrid>
        </List>
    );
};


const SubmissionTitle = () => {
    const record = useRecordContext();
    return <span>Submission {record ? `"${record.last_name}, ${record.first_name}" - ${record.email}` : ''}</span>;
};


export const SubmissionEdit = () => {
    const [showLogs, setShowLogs] = useState<boolean>(false);

    return (
        <Grid container>
            <Grid size={12}>
                <Grid size={2} alignItems={"center"}>
                    <ToggleButton value="showAdminLogs" selected={showLogs} onClick={() => setShowLogs(!showLogs)}>
                        {showLogs ? "Hide Admin Logs" : "Show Admin Logs"}
                    </ToggleButton>
                </Grid>
                <Edit aside={<AdminLogs showLogs={showLogs}/>}>
                    <SimpleForm>
                        <Grid container>
                            <Grid size={3}>
                                {"submit/"}
                                <TextField source="id"/>
                            </Grid>
                            <Grid size={3}>
                                {"source format: "}
                                <TextField source="source_format"/>
                                {" - "}
                                <NumberField source="source_size"/>
                                {" bytes"}

                            </Grid>
                            <Grid size={2}>
                                <SelectInput source="status" choices={submissionStatusOptions}/>
                            </Grid>
                            <Grid container size={12}>
                                <Grid size={2}>
                                    User Identity
                                </Grid>
                                <Grid size={4}>
                                    <ReferenceField source="submitter_id" reference="users" label={"Submitter"}
                                                    link={(record, reference) => `/${reference}/${record.id}`}>
                                        <TextField source={"last_name"}/>
                                        {", "}
                                        <TextField source={"first_name"}/>
                                    </ReferenceField>
                                </Grid>
                                <Grid size={4}>
                                    <ReferenceField source="submitter_id" reference="users" label={"Submitter"}>
                                        <EmailField source={"email"}/>
                                    </ReferenceField>
                                </Grid>
                            </Grid>
                            <Grid container size={12}>
                                <Grid size={2}>
                                    From
                                </Grid>
                                <Grid size={4}>
                                    <TextInput source="submitter_name"/>
                                </Grid>
                                <Grid size={4}>
                                    <TextInput source="submitter_email"/>
                                </Grid>
                            </Grid>

                            <Grid container size={12}>
                                <Grid size={2}>
                                    Date created:
                                </Grid>
                                <Grid size={2}>
                                    <ISODateField source="created" label="Created"/>
                                </Grid>
                                <Grid size={2}>
                                    Date updated:
                                </Grid>
                                <Grid size={2}>
                                    <ISODateField source="updated"/>
                                </Grid>
                            </Grid>

                            <Grid container size={12}>
                                <Grid size={2}>
                                    Categories:
                                </Grid>
                                <Grid size={10}>
                                    <CategoryInputField source="id" sourceCategory="archive"
                                                        sourceClass="subject_class"/>
                                </Grid>
                            </Grid>

                            <Grid container size={12}>
                                <Grid size={2}>
                                    Title
                                </Grid>
                                <Grid size={10}>
                                    <TextInput source="title"/>
                                </Grid>

                            </Grid>
                            <Grid container size={12}>
                                <Grid size={2}>
                                    Authors
                                </Grid>
                                <Grid size={10}>
                                    <TextInput source="authors"/>
                                </Grid>

                            </Grid>

                            <Grid container size={12}>
                                <Grid size={2}>
                                    Comments
                                </Grid>
                                <Grid size={10}>
                                    <TextInput source="comments"/>
                                </Grid>

                            </Grid>
                            <Grid container size={12}>
                                <Grid size={2}>
                                    License
                                </Grid>
                                <Grid size={10}>
                                    <TextField source="license"/>
                                </Grid>

                            </Grid>
                            <Grid container size={12}>
                                <Grid size={2}>
                                    Abstract
                                </Grid>
                                <Grid size={10}>
                                    <TextInput source="abstract" multiline rows={20}/>
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
                            link={(record, reference) => `/${reference}/${record.id}`}>
                <TextField source={"last_name"}/>
                {", "}
                <TextField source={"first_name"}/>
            </ReferenceField>

            <ReferenceField source="endorser_id" reference="users" label={"Endorser"}
                            link={(record, reference) => `/${reference}/${record.id}`}>
                <TextField source={"last_name"}/>
                {", "}
                <TextField source={"first_name"}/>
            </ReferenceField>

            <TextInput source="archive"/>

            <TextInput source="subject_class"/>
            <BooleanInput source="flag_valid" label={"Valid"}/>

            <TextInput source="type"/>
            <NumberInput source="point_value" label={"Point"}/>
            <DateInput source="issued_when" label={"Issued"}/>

        </SimpleForm>
    </Create>
);

/*
 */

export const SubmissionShow = () => {
    return (
        <Show>
            <Grid container>
                <Grid container size={12}>
                    <Grid size={3}>
                        <TextField source="id"/>
                        {" / "}
                        <TextField source="document_id"/>
                    </Grid>
                    <Grid size={9}>
                        <TextField source="title"/>
                    </Grid>
                </Grid>
                <Grid container size={12}>
                    <Grid size={2}>
                        Authors:
                    </Grid>
                    <Grid size={10}>
                        <TextField source="authors"/>
                    </Grid>
                </Grid>
                <Grid container size={12}>
                    <Grid size={2}>
                        Submitter:
                    </Grid>
                    <Grid size={10}>
                        <ReferenceField source="submitter_id" reference="users" label={"Submitter"}
                                        link={(record, reference) => `/${reference}/${record.id}`}>
                            <TextField source={"last_name"}/>
                            {", "}
                            <TextField source={"first_name"}/>
                        </ReferenceField>
                    </Grid>
                </Grid>
                <Grid container size={12}>
                    <Grid size={2}>
                        Submission date:
                    </Grid>
                    <Grid size={3}>
                        <ISODateField source="submit_time"/>
                    </Grid>
                    <Grid size={2}>
                        Release time:
                    </Grid>
                    <Grid size={3}>
                        <ISODateField source="release_time"/>
                    </Grid>
                </Grid>

                <Grid container size={12}>
                    <Grid size={2}>
                        Comments
                    </Grid>
                    <Grid size={10}>
                        <TextField source="comments"/>
                    </Grid>
                </Grid>

                <Grid container size={12}>
                    <Grid size={2}>
                        Abstract
                    </Grid>
                    <Grid size={10}>
                        <TextField source="abstract"/>
                    </Grid>
                </Grid>
            </Grid>
        </Show>
    )
};
