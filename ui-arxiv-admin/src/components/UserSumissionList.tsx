import {
    Datagrid,
    ReferenceField,
    TextField,
    Identifier,
    useRecordContext,
    useListController,
    ListContextProvider,
    Pagination,
} from 'react-admin';

import React from "react";
import IsOkField from "../bits/IsOkField";
import ArxivCheckSubmissionLink from "../bits/ArxivCheckSubmissionLink";
import PrimaryCategoryField from "../bits/PirmaryCategoryField";

export const UserIdSubmissionList: React.FC<{userId: Identifier}> = ({userId}) => {
    const controllerProps = useListController({
        resource: 'submissions',
        filter: {
            submitter_id: userId,
            submission_status: [],
        },
        sort: { field: 'id', order: 'DESC' },
        perPage: 10,
        disableSyncWithLocation: true,
    });

    if (controllerProps.isLoading) return null;
    if (controllerProps.error) return <p>Error loading submissions data.</p>;

    return (
        <ListContextProvider value={controllerProps}>
            <Datagrid
                rowClick={false}
                bulkActionsToolbar={undefined}
                bulkActionButtons={false}
                empty={<p><b>User has no submissions</b></p>}
            >
                <ReferenceField reference={"submissions"} source={"id"} link={"show"}>
                    <TextField source="id" label="ID" textAlign="right"/>
                </ReferenceField>
                <ArxivCheckSubmissionLink source="type" label="Type"/>
                <PrimaryCategoryField source="submission_categories" label="Cat"/>
                <ArxivCheckSubmissionLink source="title"/>
                <ReferenceField source="document_id" reference="documents" label={"Doc"}
                                link={(record, reference) => `/${reference}/${record.id}/show`}>
                    <TextField source={"paper_id"}/>
                </ReferenceField>
                <IsOkField source="is_ok" label={"OK?"}/>
            </Datagrid>
            <Pagination sx={{
                '& .MuiTablePagination-toolbar': {
                    minHeight: '32px',
                    padding: '2px 8px'
                },
                '& .MuiTablePagination-selectLabel, & .MuiTablePagination-displayedRows': {
                    fontSize: '0.8rem'
                }
            }} />
        </ListContextProvider>
    );
};

export const UserSubmissionList: React.FC<{}> = ({}) => {
    const record = useRecordContext();
    if (!record) return null;
    const userId = record.id;

    return (<UserIdSubmissionList userId={userId} />);
};

