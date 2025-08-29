import {
    Datagrid,
    List,
    ReferenceField,
    TextField,
    Identifier, useRecordContext,
} from 'react-admin';

import React from "react";
import IsOkField from "../bits/IsOkField";
import ArxivCheckSubmissionLink from "../bits/ArxivCheckSubmissionLink";
import PrimaryCategoryField from "../bits/PirmaryCategoryField";

export const UserIdSubmissionList: React.FC<{userId: Identifier}> = ({userId}) => {

    return (
        <List resource="submissions"
              filterDefaultValues={{
                  submitter_id: userId,
                  submission_status: [],
              }}
              sort={{ field: 'id', order: 'DESC' }}
              exporter={false}
              empty={(<p>User has no submissions</p>)}
              actions={false}
        >
            <Datagrid rowClick={false}

                      bulkActionsToolbar={undefined}
                      bulkActionButtons={false}>

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
        </List>
    );
};

export const UserSubmissionList: React.FC<{}> = ({}) => {
    const record = useRecordContext();
    if (!record) return null;
    const userId = record.id;

    return (<UserIdSubmissionList userId={userId} />);
};

